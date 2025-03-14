"""
LinkedIn comment monitoring and response module
"""

import time
import json
import requests
from datetime import datetime, timedelta

class LinkedInCommentResponder:
    """Class for monitoring and responding to LinkedIn comments"""
    
    def __init__(self, auth, content_generator, discord_notifier=None):
        """Initialize with LinkedIn authentication and content generator"""
        self.auth = auth
        self.content_generator = content_generator
        self.discord_notifier = discord_notifier
        self.processed_comments = set()
        self.check_interval = 60 * 30  # Check every 30 minutes by default
    
    def load_processed_comments(self, filename="processed_comments.json"):
        """Load previously processed comments from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.processed_comments = set(data.get("comment_ids", []))
                print(f"Loaded {len(self.processed_comments)} previously processed comments")
        except (FileNotFoundError, json.JSONDecodeError):
            print("No valid processed comments file found. Starting fresh.")
            self.processed_comments = set()
    
    def save_processed_comments(self, filename="processed_comments.json"):
        """Save processed comments to file"""
        with open(filename, 'w') as f:
            json.dump({"comment_ids": list(self.processed_comments)}, f)
            print(f"Saved {len(self.processed_comments)} processed comments")
    
    def get_recent_posts(self, days_back=7, max_posts=10):
        """Get your recent LinkedIn posts
        
        Args:
            days_back (int): How many days back to look for posts
            max_posts (int): Maximum number of posts to retrieve
            
        Returns:
            list: List of post IDs
        """
        if not self.auth.access_token or not self.auth.person_id:
            print("Not authenticated. Please run authenticate() first.")
            return []
        
        url = f"{self.auth.api_url}/ugcPosts"
        headers = {
            'Authorization': f'Bearer {self.auth.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        params = {
            'q': 'authors',
            'authors': f"List(urn:li:person:{self.auth.person_id})",
            'count': max_posts
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                posts = data.get('elements', [])
                
                # Filter to recent posts only
                cutoff_date = datetime.now() - timedelta(days=days_back)
                recent_posts = []
                
                for post in posts:
                    # Extract the post ID and creation time
                    post_id = post.get('id')
                    created_time = post.get('created', {}).get('time', 0) / 1000  # Convert from milliseconds
                    created_date = datetime.fromtimestamp(created_time)
                    
                    if created_date >= cutoff_date:
                        recent_posts.append(post_id)
                
                print(f"Found {len(recent_posts)} recent posts")
                return recent_posts
            else:
                print(f"Failed to get posts: {response.status_code}")
                print(f"Response: {response.text}")
                return []
        except Exception as e:
            print(f"Error getting posts: {str(e)}")
            return []
    
    def get_comments_for_post(self, post_id):
        """Get comments for a specific LinkedIn post
        
        Args:
            post_id (str): The LinkedIn post ID
            
        Returns:
            list: List of comment objects with id, actor, comment text
        """
        if not self.auth.access_token:
            print("Not authenticated. Please run authenticate() first.")
            return []
        
        # Construct the URL for comments on this post
        url = f"{self.auth.api_url}/socialActions/{post_id}/comments"
        headers = {
            'Authorization': f'Bearer {self.auth.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                comments = data.get('elements', [])
                
                processed_comments = []
                for comment in comments:
                    # Extract the commenter and comment text
                    comment_id = comment.get('id')
                    actor = comment.get('actor', 'urn:li:person:unknown').split(':')[-1]
                    comment_text = comment.get('message', {}).get('text', '')
                    
                    # Skip comments by the post author (yourself)
                    if actor == self.auth.person_id:
                        continue
                    
                    processed_comments.append({
                        'id': comment_id,
                        'actor': actor,
                        'text': comment_text,
                        'post_id': post_id
                    })
                
                return processed_comments
            else:
                print(f"Failed to get comments: {response.status_code}")
                print(f"Response: {response.text}")
                return []
        except Exception as e:
            print(f"Error getting comments: {str(e)}")
            return []
    
    def reply_to_comment(self, comment_obj, article_title):
        """Reply to a specific comment
        
        Args:
            comment_obj (dict): The comment object with id, actor, text, post_id
            article_title (str): The title of the article from the original post
            
        Returns:
            bool: True if reply was successful, False otherwise
        """
        if not self.auth.access_token:
            print("Not authenticated. Please run authenticate() first.")
            return False
        
        # Generate the reply content
        reply_text = self.content_generator.generate_comment_reply(comment_obj['text'], article_title)
        
        # Post the reply
        url = f"{self.auth.api_url}/socialActions/{comment_obj['post_id']}/comments"
        headers = {
            'Authorization': f'Bearer {self.auth.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        data = {
            "actor": f"urn:li:person:{self.auth.person_id}",
            "message": {
                "text": reply_text
            },
            "parentComment": comment_obj['id']
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in (200, 201):
                print(f"Successfully replied to comment: {comment_obj['id']}")
                
                # Send notification to Discord if enabled
                if self.discord_notifier:
                    notification = f"💬 Replied to LinkedIn comment\n\n**Comment:** {comment_obj['text'][:100]}...\n**Reply:** {reply_text[:100]}..."
                    self.discord_notifier.send_notification(notification)
                
                # Mark this comment as processed
                self.processed_comments.add(comment_obj['id'])
                self.save_processed_comments()
                
                return True
            else:
                print(f"Failed to reply to comment: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"Error replying to comment: {str(e)}")
            return False
    
    def check_and_reply_to_new_comments(self, article_title):
        """Check for new comments on recent posts and reply to them
        
        Args:
            article_title (str): The title of the article (for context in replies)
            
        Returns:
            int: Number of comments replied to
        """
        # Get recent posts
        recent_posts = self.get_recent_posts()
        
        if not recent_posts:
            print("No recent posts found to check for comments")
            return 0
        
        # Track how many comments we reply to
        reply_count = 0
        
        # Check each post for comments
        for post_id in recent_posts:
            comments = self.get_comments_for_post(post_id)
            
            for comment in comments:
                # Skip comments we've already processed
                if comment['id'] in self.processed_comments:
                    continue
                
                print(f"New comment found: {comment['text']}")
                
                # Reply to the comment
                success = self.reply_to_comment(comment, article_title)
                
                if success:
                    reply_count += 1
                
                # Add a small delay between replies to avoid rate limiting
                time.sleep(2)
        
        return reply_count
    
    def start_monitoring(self, article_title, check_interval=None, duration_hours=24):
        """Start monitoring for comments and automatically reply
        
        Args:
            article_title (str): The title of the article for context in replies
            check_interval (int): How often to check for new comments (in seconds)
            duration_hours (int): How long to monitor for comments (in hours)
            
        Returns:
            None
        """
        if check_interval:
            self.check_interval = check_interval
        
        # Load previously processed comments
        self.load_processed_comments()
        
        print(f"Starting LinkedIn comment monitoring for {duration_hours} hours")
        print(f"Will check for new comments every {self.check_interval/60} minutes")
        
        if self.discord_notifier:
            self.discord_notifier.send_notification(f"🔍 Started monitoring LinkedIn comments for {duration_hours} hours")
        
        # Calculate end time
        end_time = datetime.now() + timedelta(hours=duration_hours)
        
        while datetime.now() < end_time:
            # Check for new comments and reply
            replies_sent = self.check_and_reply_to_new_comments(article_title)
            
            if replies_sent > 0:
                print(f"Replied to {replies_sent} new comments")
            else:
                print("No new comments found")
            
            # Calculate time until next check
            next_check_time = datetime.now() + timedelta(seconds=self.check_interval)
            time_left = end_time - datetime.now()
            
            print(f"Next check at: {next_check_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Monitoring will continue for: {time_left.total_seconds()/3600:.1f} more hours")
            
            # Wait until next check
            time.sleep(self.check_interval)
        
        print("Comment monitoring completed")
        if self.discord_notifier:
            self.discord_notifier.send_notification("✅ LinkedIn comment monitoring completed")