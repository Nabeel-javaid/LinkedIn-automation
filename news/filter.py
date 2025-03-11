"""
News filtering module for the LinkedIn AI News Bot
"""

class NewsFilter:
    """Class for filtering and ranking news articles"""
    
    def __init__(self):
        """Initialize with filtering configuration"""
        # Key terms for relevance scoring
        self.key_terms = [
            'breakthrough', 'new model', 'release', 'advancement', 'state-of-the-art', 
            'sota', 'performance', 'improvement', 'beats', 'outperforms'
        ]
        
        # Popular models and companies
        self.companies_models = [
            'openai', 'anthropic', 'claude', 'gpt', 'llama', 'mistral', 
            'google', 'gemini', 'ai21', 'groq', 'stability'
        ]
    
    def filter_news(self, articles, posted_articles, max_articles=5):
        """Filter news to find the most relevant and recent articles"""
        # Remove duplicates based on URL
        unique_articles = {}
        for article in articles:
            if article['link'] not in unique_articles and article['link'] not in posted_articles:
                unique_articles[article['link']] = article
        
        filtered_articles = list(unique_articles.values())
        
        # Calculate relevance scores
        for article in filtered_articles:
            relevance_score = self._calculate_relevance_score(article)
            article['relevance_score'] = relevance_score
        
        # Sort by relevance score and recency
        sorted_articles = sorted(
            filtered_articles, 
            key=lambda x: (x.get('relevance_score', 0), x.get('published', '')), 
            reverse=True
        )
        
        return sorted_articles[:max_articles]
    
    def _calculate_relevance_score(self, article):
        """Calculate relevance score for an article"""
        relevance_score = 0
        
        # Check for key terms in title and summary
        for term in self.key_terms:
            if term.lower() in article['title'].lower():
                relevance_score += 2
            if 'summary' in article and term.lower() in article['summary'].lower():
                relevance_score += 1
        
        # Check if it mentions popular models or companies
        for entity in self.companies_models:
            if entity.lower() in article['title'].lower():
                relevance_score += 1
            if 'summary' in article and entity.lower() in article['summary'].lower():
                relevance_score += 0.5
        
        return relevance_score