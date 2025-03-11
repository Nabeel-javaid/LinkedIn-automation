#!/usr/bin/env python3
"""
LinkedIn AI News Bot - Main Entry Point

This script runs the LinkedIn AI News Bot, which automatically posts AI news
to LinkedIn using LLM-generated content.
"""

import os
import sys
import time
from datetime import datetime
import random
import argparse
from datetime import timedelta

from dotenv import load_dotenv # type: ignore

from linkedin.auth import LinkedInAuth
from linkedin.poster import LinkedInPoster
from news.fetcher import NewsFetcher
from news.filter import NewsFilter
from content.generator import ContentGenerator
from content.evaluator import ContentEvaluator
from utils.history import PostingHistory
from utils.analytics import Analytics
from utils.discord_notifier import DiscordNotifier
from config import Config

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='LinkedIn AI News Bot')
    parser.add_argument('--once', action='store_true', help='Run a single post')
    parser.add_argument('--analytics', action='store_true', help='Show posting analytics')
    parser.add_argument('--days', type=int, default=30, help='Run scheduler for specific number of days')
    return parser.parse_args()

class AINewsBot:
    """Main bot class that orchestrates the posting process"""
    
    def __init__(self):
        """Initialize the LinkedIn AI News Bot"""
        load_dotenv()
        
        # Load config
        self.config = Config()
        
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
        return self.auth.authenticate()
    
    def run_once(self):
        """Run one cycle of the news bot"""
        # Check if we should post based on frequency settings
        current_time = time.time()
        if (self.last_post_time and 
            (current_time - self.last_post_time) < (self.min_hours_between_posts * 3600)):
            print(f"Too soon to post again. Waiting until minimum interval of {self.min_hours_between_posts} hours has passed.")
            return False
        
        # Fetch news from all sources
        print("Fetching news...")
        all_articles = self.news_fetcher.fetch_all_news()
        
        if not all_articles:
            print("No articles found")
            return False
        
        # Filter to find the most relevant
        print("Filtering articles...")
        best_articles = self.news_filter.filter_news(all_articles, self.posted_articles)
        
        if not best_articles:
            print("No suitable articles found after filtering")
            return False
        
        # Select one article - either top article or random from top 3
        selected_article = random.choice(best_articles[:3]) if len(best_articles) >= 3 else best_articles[0]
        print(f"Selected article: {selected_article['title']}")
        
        # Check if it's a weekend and use weekend variation if so
        is_weekend = datetime.now().weekday() >= 5  # 5 and 6 are Saturday and Sunday
        
        # Generate post with LLM
        print("Generating LinkedIn post...")
        if is_weekend:
            print("Detected weekend - using weekend post style")
            post_content = self.content_generator.create_post_variation(selected_article, "weekend")
        else:
            post_content = self.content_generator.generate_post(selected_article)
        
        # Evaluate post quality
        quality_score = self.content_evaluator.evaluate(post_content, selected_article)
        print(f"Post quality score: {quality_score}/9")
        
        # Post to LinkedIn
        print("Posting to LinkedIn...")
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
            
            print("Successfully posted to LinkedIn!")
            
            # Send notification to Discord
            self.discord.send_post_success(selected_article['title'], quality_score, current_time_str)
            
            return True
        else:
            self.analytics.track_failed_post()
            print("Failed to post to LinkedIn")
            
            # Send failure notification to Discord
            self.discord.send_post_failure(selected_article['title'], current_time_str)
            
            return False
    
    def run_scheduler(self, days=30):
        """Run the scheduler for a specified number of days, posting once per day"""
        print(f"Starting LinkedIn AI News Bot scheduler for {days} days")
        self.discord.send_bot_started(days)
        
        # First authenticate with LinkedIn
        if not self.auth.access_token:
            if not self.authenticate():
                print("Authentication failed. Cannot proceed.")
                self.discord.send_notification("❌ LinkedIn authentication failed. Bot stopped.")
                return
        
        day = 0
        while day < days:
            print(f"\n--- Day {day+1} ---")
            
            # Post immediately for the first run
            if day == 0:
                print("First run - posting immediately...")
                success = self.run_once()
                
                if success:
                    print(f"Successfully posted for day {day+1}")
                else:
                    print(f"Failed to post for day {day+1}")
                
                # Calculate time until tomorrow with a small random buffer
                seconds_until_tomorrow = self._calculate_seconds_until_tomorrow() + random.randint(0, 3600)
                next_day_time = datetime.fromtimestamp(time.time() + seconds_until_tomorrow).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"Day {day+1} complete. Waiting {seconds_until_tomorrow/3600:.1f} hours until day {day+2}")
                print(f"Next day begins at: {next_day_time}")
                
                # Send Discord notification about next day
                self.discord.send_day_complete(day+1, seconds_until_tomorrow/3600, next_day_time)
                
                # Wait until next day with hourly updates
                self._wait_with_updates(seconds_until_tomorrow, day+2)
            else:
                # For subsequent days, post at a random time during the day
                post_delay = random.randint(0, 23) * 3600  # Convert hours to seconds
                post_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                scheduled_post_time = datetime.fromtimestamp(time.time() + post_delay).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"Current time: {post_time}")
                print(f"Scheduled post time: {scheduled_post_time}")
                print(f"Will post in {post_delay/3600:.1f} hours")
                
                # Send Discord notification about scheduled post
                self.discord.send_schedule_update(day+1, post_delay/3600, scheduled_post_time)
                
                # Wait until post time with hourly updates
                self._wait_with_updates(post_delay)
                
                # Attempt to post
                print("\nTime to post! Attempting now...")
                success = self.run_once()
                
                if success:
                    print(f"Successfully posted for day {day+1}")
                else:
                    print(f"Failed to post for day {day+1}")
                
                # Calculate time until tomorrow with a small random buffer
                remaining_time = self._calculate_seconds_until_tomorrow() + random.randint(0, 3600)
                next_day_time = datetime.fromtimestamp(time.time() + remaining_time).strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"Day {day+1} complete. Waiting {remaining_time/3600:.1f} hours until day {day+2}")
                print(f"Next day begins at: {next_day_time}")
                
                # Send Discord notification about next day
                self.discord.send_day_complete(day+1, remaining_time/3600, next_day_time)
                
                # Wait until next day with hourly updates
                self._wait_with_updates(remaining_time, day+2)
            
            day += 1
    
    def _calculate_seconds_until_tomorrow(self):
        """Calculate seconds until tomorrow at the same time"""
        now = datetime.now()
        tomorrow = datetime(now.year, now.month, now.day) + timedelta(days=1)
        return (tomorrow - now).total_seconds()
    
    def _wait_with_updates(self, wait_seconds, next_day=None):
        """Wait for specified time with hourly updates and progress bar"""
        remaining = wait_seconds
        while remaining > 0:
            # Sleep for 1 hour or remaining time, whichever is less
            sleep_time = min(3600, remaining)
            time.sleep(sleep_time)
            remaining -= sleep_time
            
            # Update on time remaining if we still have time left
            if remaining > 0:
                hours_left = remaining / 3600
                if next_day:
                    print(f"Update: {hours_left:.1f} hours until day {next_day}")
                else:
                    print(f"Update: {hours_left:.1f} hours until posting")
                
                # Update progress bar
                progress = int(((wait_seconds - remaining) / wait_seconds) * 20)
                progress_bar = "█" * progress + "░" * (20 - progress)
                print(f"Progress: |{progress_bar}| {((wait_seconds - remaining) / wait_seconds) * 100:.1f}%")
    
    def display_analytics(self):
        """Display analytics about the bot's performance"""
        analytics_data = self.analytics.get_data()
        print("\n=== LinkedIn AI News Bot Analytics ===")
        for key, value in analytics_data.items():
            print(f"{key}: {value}")
        
        # Send to Discord
        self.discord.send_analytics(analytics_data)

def main():
    """Main entry point for the application"""
    args = parse_arguments()
    
    # Check if API keys are set
    if not os.environ.get('LINKEDIN_CLIENT_ID') or not os.environ.get('LINKEDIN_CLIENT_SECRET'):
        print("Please set the LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET environment variables.")
        sys.exit(1)
        
    if not os.environ.get('LLM_API_KEY'):
        print("Please set the LLM_API_KEY environment variable for your chosen LLM provider.")
        print("Example: export LLM_API_KEY=your-groq-api-key")
        sys.exit(1)
    
    if 'newsapi' in os.environ.get('NEWS_SOURCES', '').lower() and not os.environ.get('NEWSAPI_KEY'):
        print("NewsAPI selected but NEWSAPI_KEY not set. This news source will be skipped.")
    
    # Create the news bot
    news_bot = AINewsBot()
    
    # Run based on command line arguments
    if args.once:
        # Run just once for testing
        print("Running in single post mode...")
        news_bot.discord.send_notification("🔍 LinkedIn AI News Bot started in single post mode")
        news_bot.run_once()
    elif args.analytics:
        # Show analytics
        if news_bot.auth.access_token or news_bot.authenticate():
            news_bot.display_analytics()
    else:
        # Run scheduler for specified days
        print(f"Running scheduler for {args.days} days...")
        news_bot.run_scheduler(days=args.days)

if __name__ == "__main__":
    main()