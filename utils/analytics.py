"""
Analytics tracking module for the LinkedIn AI News Bot
"""

class Analytics:
    """Class for tracking analytics about the bot's performance"""
    
    def __init__(self):
        """Initialize analytics tracking"""
        self.analytics = {
            "posts_generated": 0,
            "successful_posts": 0,
            "failed_posts": 0,
            "sources": {},
            "topics": {}
        }
    
    def track_post_generated(self):
        """Track that a post was generated"""
        self.analytics["posts_generated"] += 1
    
    def track_successful_post(self):
        """Track that a post was successfully published"""
        self.analytics["successful_posts"] += 1
    
    def track_failed_post(self):
        """Track that a post failed to publish"""
        self.analytics["failed_posts"] += 1
    
    def track_source(self, source_name):
        """Track news sources used"""
        if source_name in self.analytics["sources"]:
            self.analytics["sources"][source_name] += 1
        else:
            self.analytics["sources"][source_name] = 1
    
    def track_topic(self, topic):
        """Track topics of articles"""
        if topic in self.analytics["topics"]:
            self.analytics["topics"][topic] += 1
        else:
            self.analytics["topics"][topic] = 1
    
    def get_data(self):
        """Return analytics about the bot's performance"""
        return {
            "total_posts_generated": self.analytics["posts_generated"],
            "successful_posts": self.analytics["successful_posts"],
            "failed_posts": self.analytics["failed_posts"],
            "success_rate": (self.analytics["successful_posts"] / self.analytics["posts_generated"]) * 100 if self.analytics["posts_generated"] > 0 else 0,
            "top_sources": sorted(self.analytics["sources"].items(), key=lambda x: x[1], reverse=True)[:5],
            "top_topics": sorted(self.analytics["topics"].items(), key=lambda x: x[1], reverse=True)[:10],
        }