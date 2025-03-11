"""
Content evaluation module for the LinkedIn AI News Bot
"""

import re

class ContentEvaluator:
    """Class for evaluating the quality of generated content"""
    
    def evaluate(self, content, article):
        """Rate the quality of the generated post to ensure high standards"""
        score = 0
        
        # Check length - posts between 700-1300 chars tend to perform best
        length = len(content)
        if 700 <= length <= 1300:
            score += 2
        elif 500 <= length <= 1500:
            score += 1
        
        # Check for paragraph breaks
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            score += 1
        
        # Check for hashtags
        hashtag_count = content.count('#')
        if 3 <= hashtag_count <= 5:
            score += 1
        
        # Check for questions (engagement)
        if '?' in content:
            score += 1
        
        # Check for link inclusion
        if article['link'] in content:
            score += 2
        
        # Check for emoji usage (but not excessive)
        emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F700-\U0001F77F"  # alchemical symbols
                               u"\U0001F780-\U0001F7FF"  # Geometric Shapes
                               u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                               u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                               u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                               u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                               u"\U00002702-\U000027B0"  # Dingbats
                               "]+")
        
        emoji_count = len(emoji_pattern.findall(content))
        if 1 <= emoji_count <= 3:
            score += 1
        
        # Check that title keywords are included
        title_words = set(re.findall(r'\w+', article['title'].lower()))
        content_words = set(re.findall(r'\w+', content.lower()))
        title_keywords = [word for word in title_words if len(word) > 4]  # Only meaningful words
        keyword_matches = sum(1 for word in title_keywords if word in content_words)
        
        if keyword_matches >= len(title_keywords) // 2:
            score += 1
        
        return score