"""
LinkedIn comment monitoring and response module
"""

import time
import json
import requests
from datetime import datetime, timedelta
from utils.console import Console, Colors

class LinkedInCommentResponder:
    """Class for monitoring and responding to LinkedIn comments"""
    
    def __init__(self, auth, content_generator, discord_notifier=None):
        """Initialize with LinkedIn authentication and content generator"""
        self.auth = auth
        self.content_generator = content_generator
        self.discord_notifier = discord_notifier
        self.processed_comments = set()
        self.check_interval = 60  # Check every minute by default
        self.latest_post_id = None
        self.error_count = 0
        self.max_consecutive_errors = 5
    
    def load_processed_comments(self, filename="processed_comments.json"):
        """Load previously processed comments from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                self.processed_comments = set(data.get("comment_ids", []))
                Console.info(f"Loaded {len(self.processed_comments)} previously processed comments")
        except (FileNotFoundError, json.JSONDecodeError):
            Console.warning("No valid processed comments file found. Starting fresh.")
            self.processed_comments = set()
    
    def save_processed_comments(self, filename="processed_comments.json"):
        """Save processed comments to file"""
        with open(filename, 'w') as f:
            json.dump({"comment_ids": list(self.processed_comments)}, f)
            Console.debug(f"Saved {len(self.processed_comments)} processed comments")
    
    def get_recent_posts(self, days_back=7, max_posts=10):
        """Get your recent LinkedIn posts (RESTRICTED API ACCESS)
        
        Note: This will likely fail unless you have Marketing Developer Partner
        status with LinkedIn, which requires a business application.
        
        Args:
            days_back (int): How many days back to look for posts
            max_posts (int): Maximum number of posts to retrieve
            
        Returns:
            list: List of post IDs
        """
        # Display a warning about LinkedIn API limitations
        Console.debug("⚠️ Note: LinkedIn API access for posts is restricted to Marketing Developer Partners")
        Console.debug("Most developer applications don't have sufficient permissions")
        
        # Check authentication status
        Console.debug("Checking auth - Token exists: " + str(bool(self.auth.access_token)))
        Console.debug("Checking auth - Person ID exists: " + str(bool(self.auth.person_id)))
        
        if not self.auth.access_token or not self.auth.person_id:
            Console.warning("Not authenticated. Cannot fetch recent posts.")
            return []
        
        Console.debug(f"Person ID being used: {self.auth.person_id}")
        
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
            Console.debug(f"API Response Status: {response.status_code}")
            
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
                
                Console.info(f"Found {len(recent_posts)} recent posts")
                return recent_posts
            elif response.status_code == 403:
                # This is expected - LinkedIn API restrictions
                Console.warning(f"LinkedIn API access restricted (403)")
                Console.debug(f"This is normal - LinkedIn restricts post API access to Marketing Developer Partners")
                return []
            else:
                Console.error(f"Failed to get posts: {response.status_code}")
                Console.debug(f"Response: {response.text[:200]}...")
                return []
        except Exception as e:
            Console.error(f"Error getting posts: {str(e)}")
            return []
    
    def set_latest_post_id(self, post_id):
        """Set the ID of the latest post for comment monitoring
        
        This is a workaround for when we can't fetch posts from the API
        """
        self.latest_post_id = post_id
        Console.info(f"Set latest post ID for comment monitoring: {post_id}")
    
    def get_comments_for_post(self, post_id):
        """Get comments for a specific LinkedIn post
        
        Args:
            post_id (str): The LinkedIn post ID
            
        Returns:
            list: List of comment objects with id, actor, comment text
        """
        if not self.auth.access_token:
            Console.warning("Not authenticated. Please run authenticate() first.")
            return []
        
        # Construct the URL for comments on this post
        # Try modern format first
        url = f"{self.auth.api_url}/socialActions/{post_id}/comments"
        headers = {
            'Authorization': f'Bearer {self.auth.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        try:
            Console.debug(f"Fetching comments for post: {post_id}")
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
                
                if processed_comments:
                    Console.success(f"Found {len(processed_comments)} comments on post")
                
                # Reset error count on success
                self.error_count = 0
                
                return processed_comments
            elif response.status_code == 400 or response.status_code == 404:
                # LinkedIn API can sometimes reject the post ID format
                # or the post might not exist, or we don't have access
                self.error_count += 1
                Console.debug(f"API Error ({response.status_code}): Unable to fetch comments for this post.")
                Console.debug("This may be due to LinkedIn API limitations or incorrect post ID format")
                
                if self.error_count >= self.max_consecutive_errors:
                    Console.warning(f"Reached maximum consecutive errors ({self.max_consecutive_errors})")
                    Console.info("Will continue monitoring but with reduced frequency")
                    # Double the check interval to reduce API calls
                    self.check_interval = min(300, self.check_interval * 2)
                
                return []
            else:
                self.error_count += 1
                Console.warning(f"Failed to get comments: {response.status_code}")
                Console.debug(f"Response: {response.text[:200]}...")
                return []
        except Exception as e:
            self.error_count += 1
            Console.error(f"Error getting comments: {str(e)}")
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
            Console.warning("Not authenticated. Please run authenticate() first.")
            return False
        
        # Generate the reply content
        Console.info(f"Generating reply to comment: \"{comment_obj['text'][:50]}...\"")
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
            Console.info("Posting reply to LinkedIn...")
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in (200, 201):
                Console.success(f"Successfully replied to comment")
                Console.debug(f"Reply: \"{reply_text[:50]}...\"")
                
                # Send notification to Discord if enabled
                if self.discord_notifier:
                    notification = f"💬 Replied to LinkedIn comment\n\n**Comment:** {comment_obj['text'][:100]}...\n**Reply:** {reply_text[:100]}..."
                    self.discord_notifier.send_notification(notification)
                
                # Mark this comment as processed
                self.processed_comments.add(comment_obj['id'])
                self.save_processed_comments()
                
                return True
            else:
                Console.error(f"Failed to reply to comment: {response.status_code}")
                Console.debug(f"Response: {response.text[:200]}...")
                return False
        except Exception as e:
            Console.error(f"Error replying to comment: {str(e)}")
            return False
    
    def check_and_reply_to_new_comments(self, article_title):
        """Check for new comments on recent posts and reply to them
        
        Args:
            article_title (str): The title of the article (for context in replies)
            
        Returns:
            int: Number of comments replied to
        """
        # If we have a latest_post_id specified, use it directly
        # This is useful when the API doesn't allow fetching posts
        if self.latest_post_id:
            recent_posts = [self.latest_post_id]
        else:
            # Try to get recent posts from API (likely to fail due to LinkedIn API limitations)
            recent_posts = self.get_recent_posts()
        
        if not recent_posts:
            Console.info("No recent posts found to check for comments")
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
                
                Console.info(f"New comment found: \"{comment['text'][:50]}...\"")
                
                # Reply to the comment
                success = self.reply_to_comment(comment, article_title)
                
                if success:
                    reply_count += 1
                
                # Add a small delay between replies to avoid rate limiting
                time.sleep(2)
        
        if reply_count == 0:
            Console.info("No new comments found")
        
        return reply_count
    
    def start_monitoring(self, article_title, post_id=None, duration_hours=24):
        """Start monitoring for comments and automatically reply
        
        Args:
            article_title (str): The title of the article for context in replies
            post_id (str, optional): The specific post ID to monitor (if API can't fetch posts)
            duration_hours (int): How long to monitor for comments (in hours)
            
        Returns:
            None
        """
        # If post_id is provided, set it as the latest post
        if post_id:
            self.set_latest_post_id(post_id)
        
        # Load previously processed comments
        self.load_processed_comments()
        
        Console.section("Comment Monitoring")
        Console.info(f"Starting LinkedIn comment monitoring for {duration_hours} hours")
        Console.info(f"Will check for new comments every {self.check_interval/60:.1f} minutes")
        
        if self.discord_notifier:
            self.discord_notifier.send_notification(f"🔍 Started monitoring LinkedIn comments for {duration_hours} hours")
        
        # Calculate end time
        end_time = datetime.now() + timedelta(hours=duration_hours)
        
        try:
            while datetime.now() < end_time:
                # Check for new comments and reply
                replies_sent = self.check_and_reply_to_new_comments(article_title)
                
                if replies_sent > 0:
                    Console.success(f"Replied to {replies_sent} new comments")
                
                # Calculate time until next check
                next_check_time = datetime.now() + timedelta(seconds=self.check_interval)
                time_left = end_time - datetime.now()
                
                # Format remaining time nicely
                if time_left.total_seconds() < 0:
                    break
                
                hours_left = time_left.total_seconds() / 3600
                
                # Display next check time and remaining monitoring time
                Console.info(f"Next check at: {next_check_time.strftime('%Y-%m-%d %H:%M:%S')}")
                Console.info(f"Monitoring will continue for: {hours_left:.1f} more hours")
                
                # Wait until next check
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            Console.warning("Comment monitoring interrupted by user")
        except Exception as e:
            Console.error(f"Error during comment monitoring: {str(e)}")
        finally:
            Console.success("Comment monitoring completed")
            if self.discord_notifier:
                self.discord_notifier.send_notification("✅ LinkedIn comment monitoring completed")