"""
News fetching module for the LinkedIn AI News Bot
"""

import os
import feedparser # type: ignore
import requests # type: ignore

class NewsFetcher:
    """Class for fetching news from various sources"""
    
    def __init__(self, news_sources):
        """Initialize with news sources configuration"""
        self.news_sources = news_sources
    
    def fetch_all_news(self):
        """Fetch news from all configured sources"""
        rss_articles = self.fetch_rss_news()
        api_articles = self.fetch_api_news()
        
        all_articles = rss_articles + api_articles
        print(f"Found {len(all_articles)} articles in total")
        
        return all_articles
    
    def fetch_rss_news(self):
        """Fetch news from RSS feeds"""
        articles = []
        
        # for feed_url in self.news_sources['rss']:
        #     try:
        #         feed = feedparser.parse(feed_url)
                
        #         for entry in feed.entries[:20]:  # Get most recent 10 entries
        #             article = {
        #                 'title': entry.title,
        #                 'link': entry.link,
        #                 'published': entry.get('published', entry.get('pubDate', '')),
        #                 'summary': entry.get('summary', ''),
        #                 'source': feed.feed.title if hasattr(feed, 'feed') and hasattr(feed.feed, 'title') else feed_url
        #             }
        #             articles.append(article)
        #     except Exception as e:
        #         print(f"Error fetching RSS feed {feed_url}: {str(e)}")
        
        return articles
    
    def fetch_api_news(self):
        """Fetch news from APIs"""
        articles = []
        
        # NewsAPI
        if 'newsapi' in self.news_sources['apis'] and os.environ.get('NEWSAPI_KEY'):
            try:
                api_config = self.news_sources['apis']['newsapi']
                
                # Add API key to params
                params = api_config['params'].copy()
                params['apiKey'] = os.environ.get('NEWSAPI_KEY')
                
                response = requests.get(api_config['url'], params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for article in data.get('articles', [])[:15]:  # Get top 15 articles
                        articles.append({
                            'title': article.get('title', ''),
                            'link': article.get('url', ''),
                            'published': article.get('publishedAt', ''),
                            'summary': article.get('description', ''),
                            'source': article.get('source', {}).get('name', 'NewsAPI')
                        })
                else:
                    print(f"Error fetching from NewsAPI: {response.status_code}")
                    print(f"Response: {response.text}")
            except Exception as e:
                print(f"Error with NewsAPI: {str(e)}")
        
        return articles