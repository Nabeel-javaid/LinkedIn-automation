"""
History tracking module for the LinkedIn AI News Bot
"""

import os
import json

class PostingHistory:
    """Class for managing posting history"""
    
    def __init__(self, history_file="posted_articles_history.json"):
        """Initialize with history file path"""
        self.history_file = history_file
    
    def load_posted_articles(self):
        """Load previously posted articles from file"""
        posted_articles = set()
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                    posted_articles = set(history_data.get("posted_urls", []))
                    print(f"Loaded {len(posted_articles)} previously posted articles")
        except Exception as e:
            print(f"Error loading posting history: {str(e)}")
        
        return posted_articles
    
    def get_last_post_time(self):
        """Get the timestamp of the last post"""
        last_post_time = None
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                    last_post_time = history_data.get("last_post_time")
        except Exception as e:
            print(f"Error loading last post time: {str(e)}")
        
        return last_post_time
    
    def save_posting_history(self, posted_articles, last_post_time, analytics):
        """Save posted articles to file"""
        try:
            history_data = {
                "posted_urls": list(posted_articles),
                "last_post_time": last_post_time,
                "analytics": analytics
            }
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
            print(f"Saved posting history with {len(posted_articles)} articles")
        except Exception as e:
            print(f"Error saving posting history: {str(e)}")