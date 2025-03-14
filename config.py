"""
Configuration module for the LinkedIn AI News Bot
"""

from datetime import datetime, timedelta

class Config:
    """Configuration class for the LinkedIn AI News Bot"""
    
    def __init__(self):
        """Initialize configuration settings"""
        # RSS feeds and news APIs for AI/LLM updates
        self.news_sources = {
            'rss': [
                'https://news.google.com/rss/search?q=artificial+intelligence+llm+when:7d',
                'https://venturebeat.com/category/ai/feed/',
                'https://www.reddit.com/r/machinelearning/.rss',
                'https://www.artificialintelligence-news.com/feed/',
                'https://blog.research.google/feeds/posts/default?alt=rss',
                'http://export.arxiv.org/rss/cs.AI'
            ],
            'apis': {
                'newsapi': {
                    'url': 'https://newsapi.org/v2/everything',
                    'params': {
                        'q': '(artificial intelligence OR llm OR large language model) AND (breakthrough OR advancement OR new)',
                        'language': 'en',
                        'sortBy': 'publishedAt',
                        'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                    }
                }
            }
        }
        
        # Post frequency settings
        self.posts_per_day = 1
        self.min_hours_between_posts = 20  # Avoid posting too frequently
        
        # Content generation settings
        self.post_styles = {
            "thought_leader": {
                "tone": "insightful and forward-thinking",
                "approach": "analyze implications and future impacts",
                "unique": "include one contrarian or nuanced perspective"
            },
            "industry_expert": {
                "tone": "authoritative but accessible",
                "approach": "connect to broader industry trends",
                "unique": "mention a specific use case or application"
            },
            "curious_professional": {
                "tone": "inquisitive and conversational",
                "approach": "highlight questions this raises for the field",
                "unique": "include a personal reflection on why this matters"
            },
            "data_driven": {
                "tone": "analytical and precise",
                "approach": "focus on the measurable impacts or improvements",
                "unique": "include a comparison to previous approaches/models"
            }
        }
        
        # Post quality thresholds
        self.quality_threshold = 6  # Minimum quality score to accept a post
        self.max_generation_attempts = 3  # Maximum attempts to generate a quality post