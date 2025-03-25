#!/usr/bin/env python3
"""
LinkedIn AI News Bot - Main Entry Point

This script runs the LinkedIn AI News Bot, which automatically posts AI news
to LinkedIn using LLM-generated content.
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
import random
import argparse


from dotenv import load_dotenv # type: ignore

from linkedin.auth import LinkedInAuth
from linkedin.poster import LinkedInPoster
from linkedin.comment_responder import LinkedInCommentResponder
from news.fetcher import NewsFetcher
from news.filter import NewsFilter
from content.generator import ContentGenerator
from content.evaluator import ContentEvaluator
from utils.history import PostingHistory
from utils.analytics import Analytics
from utils.discord_notifier import DiscordNotifier
from utils.console import Console  # Import the new console utility
from config import Config

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='LinkedIn AI News Bot')
    parser.add_argument('--once', action='store_true', help='Run a single post')
    parser.add_argument('--analytics', action='store_true', help='Show posting analytics')
    parser.add_argument('--days', type=int, default=30, help='Run scheduler for specific number of days')
    parser.add_argument('--update-interval', type=int, default=30, 
                        help='Update interval in minutes (default: 30)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed debug information')
    return parser.parse_args()

class AINewsBot:
    """Main bot class that orchestrates the posting process"""
    
    def __init__(self, update_interval_minutes=30, verbose=False):
        """Initialize the LinkedIn AI News Bot"""
        load_dotenv()
        
        # Set verbose mode
        if verbose:
            os.environ['DEBUG'] = '1'
        
        # Load config
        self.config = Config()
        
        # Set update interval (in minutes)
        self.update_interval_minutes = update_interval_minutes
        self.update_interval_seconds = update_interval_minutes * 60
        
        # Initialize Discord notifier
        self.discord = DiscordNotifier()
        
        # Initialize components
        self.auth = LinkedInAuth(
            client_id=os.environ.get('LINKEDIN_CLIENT_ID'),
            client_secret=os.environ.get('LINKEDIN_CLIENT_SECRET'),
            redirect_uri='http://localhost:8000/callback'
        )
        
        self.poster = LinkedInPoster(self.auth)
        self.news_fetcher = NewsFetcher(self.config.news_sources)
        self.news_filter = NewsFilter()
        
        # Setup history tracking
        self.history = PostingHistory("posted_articles_history.json")
        self.posted_articles = self.history.load_posted_articles()
        self.last_post_time = self.history.get_last_post_time()
        
        # Initialize content generation
        self.llm_api_key = os.environ.get('LLM_API_KEY')
        self.llm_provider = os.environ.get('LLM_PROVIDER', 'groq')
        self.content_generator = ContentGenerator(self.llm_api_key, self.llm_provider)
        self.content_evaluator = ContentEvaluator()
        
        # Setup analytics
        self.analytics = Analytics()
        
        # Post frequency settings
        self.posts_per_day = self.config.posts_per_day
        self.min_hours_between_posts = self.config.min_hours_between_posts
    
    def authenticate(self):
        """Authenticate with LinkedIn"""
        Console.section("LinkedIn Authentication")
        Console.info("Opening browser for authentication...")
        return self.auth.authenticate()
    
    def run_once(self, force=False):
        """Run one cycle of the news bot
        
        Args:
            force (bool): If True, ignore minimum time interval check
        """
        # Check if we should post based on frequency settings
        current_time = time.time()
        if not force and self.last_post_time and (current_time - self.last_post_time) < (self.min_hours_between_posts * 3600):
            hours_to_wait = (self.min_hours_between_posts * 3600 - (current_time - self.last_post_time)) / 3600
            next_post_time = datetime.fromtimestamp(current_time + hours_to_wait * 3600).strftime('%Y-%m-%d %H:%M:%S')
            Console.warning(f"Too soon to post again. Waiting {hours_to_wait:.1f} hours until {next_post_time}")
            return False
        
        # Fetch news from all sources
        Console.section("Fetching News")
        Console.info("Retrieving articles from configured sources...")
        all_articles = self.news_fetcher.fetch_all_news()
        
        if not all_articles:
            Console.error("No articles found")
            return False
        
        # Filter to find the most relevant
        Console.section("Filtering Articles")
        Console.info("Analyzing and ranking articles by relevance...")
        best_articles = self.news_filter.filter_news(all_articles, self.posted_articles)
        
        if not best_articles:
            Console.error("No suitable articles found after filtering")
            return False
        
        # Select one article - either top article or random from top 3
        selected_article = random.choice(best_articles[:3]) if len(best_articles) >= 3 else best_articles[0]
        Console.article_info(selected_article)
        
        # Check if it's a weekend and use weekend variation if so
        is_weekend = datetime.now().weekday() >= 5  # 5 and 6 are Saturday and Sunday
        
        # Generate post with LLM
        Console.section("Generating Content")
        if is_weekend:
            Console.info("Detected weekend - using weekend post style")
            post_content = self.content_generator.create_post_variation(selected_article, "weekend")
        else:
            Console.info("Generating engaging LinkedIn post...")
            post_content = self.content_generator.generate_post(selected_article)
        
        # Evaluate post quality
        quality_score = self.content_evaluator.evaluate(post_content, selected_article)
        if quality_score >= 7:
            Console.success(f"Post quality score: {quality_score}/9")
        elif quality_score >= 5:
            Console.info(f"Post quality score: {quality_score}/9")
        else:
            Console.warning(f"Post quality score: {quality_score}/9")
        
        # Post to LinkedIn
        Console.section("Posting to LinkedIn")
        Console.info("Submitting post to LinkedIn API...")
        self.analytics.track_post_generated()
        result = self.poster.create_text_post(post_content)
        
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if result:
            # Track that we've posted this article
            self.analytics.track_successful_post()
            self.posted_articles.add(selected_article['link'])
            self.last_post_time = current_time
            
            # Save history
            self.history.save_posting_history(self.posted_articles, self.last_post_time, self.analytics.get_data())
            
            Console.success("Post successfully published to LinkedIn!")
            
            # Send notification to Discord
            self.discord.send_post_success(selected_article['title'], quality_score, current_time_str)
            
            # Start monitoring for comments
            self.monitor_comments_after_posting(selected_article['title'])
            
            return True
        else:
            self.analytics.track_failed_post()
            Console.error("Failed to post to LinkedIn")
            
            # Send failure notification to Discord
            self.discord.send_post_failure(selected_article['title'], current_time_str)
            
            return False
    
    def monitor_comments_after_posting(self, article_title, duration_hours=24):
        """Start monitoring for comments on LinkedIn posts after posting
        
        Args:
            article_title (str): Title of the article that was shared
            duration_hours (int): How long to monitor for comments (in hours)
        """
        Console.section("Comment Monitoring")
        Console.info(f"Setting up comment monitoring for {duration_hours} hours")
        
        # Get the post ID of the most recent post
        post_id = self.poster.get_last_post_id()
        
        # Initialize the comment responder
        responder = LinkedInCommentResponder(
            auth=self.auth,
            content_generator=self.content_generator,
            discord_notifier=self.discord
        )
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(
            target=responder.start_monitoring,
            args=(article_title, post_id, duration_hours)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        Console.info("Comment monitoring started in background")
        return monitor_thread
    
    def run_scheduler(self, days=30):
        """Run the scheduler for a specified number of days, posting once per day"""
        Console.header(f"Starting LinkedIn AI News Bot for {days} days")
        self.discord.send_bot_started(days)
        
        # First authenticate with LinkedIn
        if not self.auth.access_token:
            if not self.authenticate():
                Console.error("Authentication failed. Cannot proceed.")
                self.discord.send_notification("❌ LinkedIn authentication failed. Bot stopped.")
                return
        
        day = 0
        while day < days:
            Console.day_header(day+1, days)
            
            # Post immediately for the first run
            if day == 0:
                Console.info("First run - posting immediately...")
                success = self.run_once(force=True)
                
                if success:
                    Console.success(f"Successfully posted for day {day+1}")
                else:
                    Console.error(f"Failed to post for day {day+1}")
                
                # Calculate time until tomorrow with a small random buffer
                seconds_until_tomorrow = self._calculate_seconds_until_tomorrow() + random.randint(0, 3600)
                next_day_time = datetime.fromtimestamp(time.time() + seconds_until_tomorrow).strftime('%Y-%m-%d %H:%M:%S')
                
                Console.section("Day Complete")
                Console.info(f"Day {day+1} complete. Waiting {seconds_until_tomorrow/3600:.1f} hours until day {day+2}")
                Console.info(f"Next day begins at: {next_day_time}")
                
                # Send Discord notification about next day
                self.discord.send_day_complete(day+1, seconds_until_tomorrow/3600, next_day_time)
                
                # Wait until next day with updates
                self._wait_with_updates(seconds_until_tomorrow, day+2)
            else:
                # For subsequent days, post at a random time during the day
                post_delay = random.randint(0, 23) * 3600  # Convert hours to seconds
                post_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                scheduled_post_time = datetime.fromtimestamp(time.time() + post_delay).strftime('%Y-%m-%d %H:%M:%S')
                
                Console.section("Post Scheduling")
                Console.info(f"Current time: {post_time}")
                Console.info(f"Scheduled post time: {scheduled_post_time}")
                Console.info(f"Will post in {post_delay/3600:.1f} hours")
                
                # Send Discord notification about scheduled post
                self.discord.send_schedule_update(day+1, post_delay/3600, scheduled_post_time)
                
                # Wait until post time with updates
                self._wait_with_updates(post_delay)
                
                # Attempt to post
                Console.section("Post Attempt")
                Console.info("Time to post! Attempting now...")
                success = self.run_once()
                
                if success:
                    Console.success(f"Successfully posted for day {day+1}")
                else:
                    Console.error(f"Failed to post for day {day+1}")
                
                # Calculate time until tomorrow with a small random buffer
                remaining_time = self._calculate_seconds_until_tomorrow() + random.randint(0, 3600)
                next_day_time = datetime.fromtimestamp(time.time() + remaining_time).strftime('%Y-%m-%d %H:%M:%S')
                
                Console.section("Day Complete")
                Console.info(f"Day {day+1} complete. Waiting {remaining_time/3600:.1f} hours until day {day+2}")
                Console.info(f"Next day begins at: {next_day_time}")
                
                # Send Discord notification about next day
                self.discord.send_day_complete(day+1, remaining_time/3600, next_day_time)
                
                # Wait until next day with updates
                self._wait_with_updates(remaining_time, day+2)
            
            day += 1
    
    def _calculate_seconds_until_tomorrow(self):
        """Calculate seconds until tomorrow at the same time"""
        now = datetime.now()
        tomorrow = datetime(now.year, now.month, now.day) + timedelta(days=1)
        return (tomorrow - now).total_seconds()
    
    def _wait_with_updates(self, wait_seconds, next_day=None):
        """Wait for specified time with regular updates at configured interval
        
        Args:
            wait_seconds (float): Total seconds to wait
            next_day (int, optional): Next day number for context
        """
        start_time = time.time()
        end_time = start_time + wait_seconds
        remaining = wait_seconds
        update_count = 0
        
        while remaining > 0:
            # Sleep for update interval or remaining time, whichever is less
            sleep_time = min(self.update_interval_seconds, remaining)
            time.sleep(sleep_time)
            remaining -= sleep_time
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Calculate time values for the update
            hours_left = remaining / 3600
            minutes_left = (remaining % 3600) / 60
            percent_complete = (elapsed / wait_seconds) * 100
            
            # Format current time and estimated completion time
            current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            est_completion_time = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
            
            # Create status message based on context
            if next_day:
                context = f"Day {next_day}"
            else:
                context = "Next post"
            
            # Print formatted status update
            Console.status_update(
                update_count+1,
                hours_left,
                minutes_left,
                percent_complete,
                current_time_str,
                est_completion_time,
                context
            )
            
            # Send update to Discord
            self.discord.send_status_update(
                update_count+1,
                hours_left,
                minutes_left,
                percent_complete,
                current_time_str,
                est_completion_time,
                context
            )
            
            update_count += 1
    
    def display_analytics(self):
        """Display analytics about the bot's performance"""
        Console.header("LinkedIn AI News Bot Analytics")
        analytics_data = self.analytics.get_data()
        
        for key, value in analytics_data.items():
            if isinstance(value, list):
                Console.info(f"{key}:")
                for item in value:
                    Console.info(f"  - {item[0]}: {item[1]}")
            else:
                Console.info(f"{key}: {value}")
        
        # Send to Discord
        self.discord.send_analytics(analytics_data)

def main():
    """Main entry point for the application"""
    args = parse_arguments()
    verbose = args.verbose
    
    # Clear the terminal
    Console.clear()
    Console.app_banner()
    
    # Create the news bot with custom update interval if specified
    news_bot = AINewsBot(update_interval_minutes=args.update_interval, verbose=verbose)
    
    Console.info(f"Update interval set to {args.update_interval} minutes")
    
    # Run based on command line arguments
    if args.once:
        # Run just once for testing
        Console.header("Single Post Mode")
        news_bot.discord.send_notification("🔍 LinkedIn AI News Bot started in single post mode")
        news_bot.run_once(force=True)  # Use force=True to ensure it posts regardless of timing
    elif args.analytics:
        # Show analytics
        if news_bot.auth.access_token or news_bot.authenticate():
            news_bot.display_analytics()
    else:
        # Run scheduler for specified days
        news_bot.run_scheduler(days=args.days)

if __name__ == "__main__":
    main()