"""
Content generation module for the LinkedIn AI News Bot
"""

import random
import requests # type: ignore
from config import Config

class ContentGenerator:
    """Class for generating content using LLMs"""
    
    def __init__(self, api_key, provider='groq'):
        """Initialize with API key and provider selection"""
        self.api_key = api_key
        self.provider = provider
        self.config = Config()
        
        # Load post styles from config
        self.post_styles = self.config.post_styles
    
    def generate_post(self, article):
        """Generate a high-quality LinkedIn post for the given article"""
        # Try multiple times to get a high-quality post
        for attempt in range(self.config.max_generation_attempts):
            if self.provider == 'groq':
                content = self._generate_with_groq(article)
            else:
                content = self._generate_with_local_llm(article)
            
            if not content:
                content = self._generate_better_fallback_post(article)
                return content
            
            # Accept if content exists
            if content:
                # Make sure it contains the link
                if article['link'] not in content:
                    content += f"\n\nRead more: {article['link']}"
                return content
        
        # After multiple attempts, use a fallback template
        return self._generate_better_fallback_post(article)
    
    def _generate_with_groq(self, article):
        """Generate LinkedIn posts using Groq API with enhanced prompting"""
        if not self.api_key:
            print("Groq API key not found. Using fallback post template.")
            return None
        
        # Choose style - can be fixed or randomized
        chosen_style = random.choice(list(self.post_styles.keys()))
        style = self.post_styles[chosen_style]
        
        # Create enhanced prompt with detailed instructions for more human-like content
        prompt = f"""
        You're a professional AI specialist creating an ENGAGING, AUTHENTIC LinkedIn post about this AI news. 
        Your post should sound completely human-written, conversational, and insightful.
        
        ARTICLE INFORMATION:
        Title: {article['title']}
        Summary: {article.get('summary', 'No summary available')}
        Source: {article.get('source', 'Unknown source')}
        Link: {article['link']}
        
        POST STYLE:
        - Write in a {style['tone']} tone that sounds like a real person
        - {style['approach']}
        - {style['unique']}
        
        CONTENT STRUCTURE:
        1. OPENER: Begin with a thought-provoking question, surprising fact, or personal observation related to the news (NOT just "Here's an update")
        2. YOUR TAKE: Share what YOU find interesting about this development (as if you're a real AI professional)
        3. BROADER IMPACT: Connect this to industry trends or how it might change things
        4. PERSONAL ANGLE: Add a brief reflection on how this relates to your experience or perspective
        5. ENGAGEMENT: End with a SPECIFIC, THOUGHT-PROVOKING question (not generic "what do you think?")
        6. LINK: Include the article link organically within the text
        7. HASHTAGS: Add 3-4 relevant, specific hashtags
        
        WRITING GUIDELINES:
        - Use a natural, conversational voice like you're talking to a colleague
        - Include occasional "I" statements to make it personal
        - Use short paragraphs with line breaks between them
        - Include 1-2 relevant emojis placed naturally, not at the beginning of sentences
        - Use varied sentence structures (mix of short and medium sentences)
        - Sound like a thoughtful professional with genuine curiosity
        - Avoid jargon unless you briefly explain it
        - Use 1-2 rhetorical devices like metaphors or analogies where appropriate
        
        WHAT MAKES IT SOUND HUMAN:
        - Express genuine excitement, concern, or curiosity
        - Mention a personal connection to the topic if relevant
        - Add light personality through word choice and phrasing
        - Include a small detail or example that shows thought
        - Avoid perfectly structured paragraphs - add some natural variation
        - Occasionally use casual transitions like "And yet..." or "But here's the thing..."
        
        WHAT TO AVOID:
        - Generic openings like "I found this interesting article"
        - Any hint of marketing language or corporate speak
        - Perfect parallelism in structure that sounds robotic
        - Excessive formality or academic tone
        - Overly complex or dense sentences
        - Any mention of algorithms, AI generation, or non-human aspects
        
        Return ONLY the finished post text without any additional explanations or formatting.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use primarily llama3 which tends to be better at natural, human-like writing
        models = ["llama3-70b-8192", "mixtral-8x7b-32768"]
        selected_model = models[0] if random.random() < 0.8 else models[1]  # 80% llama3, 20% mixtral
        
        data = {
            "model": selected_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.75,  # Slightly increased for more creative variation
            "max_tokens": 1200
        }
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                post_content = result['choices'][0]['message']['content'].strip()
                
                # Quality check
                if len(post_content) < 300:
                    print("Warning: Generated content is too short, regenerating...")
                    return self._generate_with_groq(article)
                    
                # Check that it contains the link
                if article['link'] not in post_content:
                    post_content += f"\n\nRead more: {article['link']}"
                
                return post_content
            else:
                print(f"Error with Groq API: {response.status_code}")
                print(f"Response: {response.text}")
                return self._generate_better_fallback_post(article)
        except Exception as e:
            print(f"Exception with Groq API: {str(e)}")
            return self._generate_better_fallback_post(article)
    
    def _generate_with_local_llm(self, article):
        """Alternative method to generate with a local LLM or other providers"""
        # This is a placeholder for integration with other LLMs
        # Could be implemented with Ollama, local Llama, etc.
        print("Local LLM generation not implemented yet")
        
        # Use fallback template instead
        return self._generate_better_fallback_post(article)
    
    def _generate_fallback_post(self, article):
        """Generate a simple fallback post if LLM generation fails"""
        title = article['title']
        link = article['link']
        source = article.get('source', 'a source')
        
        return f"""
🔍 AI Technology Update: {title}
I found this interesting development from {source} that could significantly impact how we approach AI systems and applications in the near future.
The advancement focuses on {title.split(':')[-1] if ':' in title else title}, which may lead to new opportunities in the AI landscape.
What are your thoughts on this advancement? How might it affect your work?
Read more: {link}
#AITechnology #MachineLearning #TechInnovation
"""
    
    def _generate_better_fallback_post(self, article):
        """Generate a more natural-sounding fallback post if LLM generation fails"""
        title = article['title']
        link = article['link']
        source = article.get('source', 'a source')
        
        # Create several templates and randomly select one for more variation
        templates = [
            f"""
Is Microsoft about to shake up the AI landscape? 🤔

Just read that {title}. This could significantly shift the competitive dynamics in the foundation model space, especially given Microsoft's deep partnership with OpenAI.

What's fascinating is that Microsoft might be developing its own capabilities while continuing to invest in OpenAI. This dual strategy gives them both internal expertise and external leverage - smart positioning as AI becomes increasingly critical infrastructure.

I've been tracking Big Tech's AI development strategies, and this feels like a natural evolution for Microsoft. They've been quietly building up their AI research teams for years.

What do you think - would Microsoft actually compete directly with OpenAI, or is this about ensuring they have fallback options if their partnership terms change?

{link}

#AIStrategy #TechCompetition #MicrosoftAI
""",

            f"""
The AI chess game continues... Microsoft reportedly building LLMs to rival OpenAI & Anthropic 👀

The most interesting part of {title} isn't just the technological achievement, but what it signals about Microsoft's strategic thinking.

After pouring billions into OpenAI, why develop competing models? Perhaps this is insurance against dependency on a single AI partner. Or maybe it's about specialized models for different applications that OpenAI's general-purpose approach can't deliver efficiently.

In my experience working with these technologies, having multiple approaches is always valuable - different models have different strengths.

What would be your strategy if you were Microsoft? Go all-in with partners, or build parallel internal capabilities?

Check out the details: {link}

#AIStrategy #BigTech #FutureOfAI
"""
        ]
        
        return random.choice(templates)
    
    def create_post_variation(self, article, variation_type="weekend"):
        """Create variations of posts for different contexts"""
        if not self.api_key:
            print("LLM API key not found. Using fallback post.")
            return self._generate_better_fallback_post(article)
            
        variations = {
            "weekend": {
                "instruction": "Create a more casual, reflective weekend post that encourages deeper discussion. Mention taking time to ponder this news during your weekend.",
                "temp": 0.8
            },
            "trending": {
                "instruction": "Connect this news to a current trending topic in technology or business. Show how this fits into the bigger picture of what's happening right now.",
                "temp": 0.7
            },
            "technical": {
                "instruction": "Create a more technical, detailed post for an audience of AI researchers and engineers. Include one specific technical insight or question.",
                "temp": 0.6
            },
            "business": {
                "instruction": "Focus on the business implications and potential ROI of this advancement. Include a business-related question or observation.",
                "temp": 0.7
            }
        }
        
        variation = variations.get(variation_type, variations["weekend"])
        print(f"Creating {variation_type} variation with temp={variation['temp']}")
        
        # Updated prompt for more engaging, human content
        prompt = f"""
        You're a professional AI specialist creating an AUTHENTIC, ENGAGING LinkedIn weekend post about this AI news.
        Make it sound completely human-written, as if a real person wrote it during their weekend.
        
        ARTICLE INFORMATION:
        Title: {article['title']}
        Summary: {article.get('summary', 'No summary available')}
        Source: {article.get('source', 'Unknown source')}
        Link: {article['link']}
        
        WEEKEND POST STYLE:
        - Write in a relaxed, thoughtful weekend tone
        - {variation['instruction']}
        - Include a personal reflection element that feels authentic
        
        MAKE IT HUMAN AND ENGAGING:
        - Begin with a weekend context (e.g., "Taking some time this Sunday to think about...")
        - Share a genuine-sounding personal reaction to the news
        - Use casual language with occasional "thinking out loud" elements
        - Add a touch of weekend mindset (more reflective, big-picture thinking)
        - Include one specific detail or example that shows thoughtful engagement
        - End with a question that invites genuine conversation
        
        AVOID ANYTHING THAT SOUNDS:
        - Corporate or overly polished
        - Generic or templated
        - Too formal or structured
        - Like it was written by AI
        
        Return ONLY the finished post text without any additional explanations or formatting.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": variation['temp'],
            "max_tokens": 1200
        }
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                post_content = result['choices'][0]['message']['content'].strip()
                
                # Make sure it contains the link
                if article['link'] not in post_content:
                    post_content += f"\n\nRead more: {article['link']}"
                
                return post_content
            else:
                print(f"Error with Groq API: {response.status_code}")
                print(f"Response: {response.text}")
                return self._generate_better_fallback_post(article)
        except Exception as e:
            print(f"Exception with Groq API: {str(e)}")
            return self._generate_better_fallback_post(article)

    def generate_comment_reply(self, comment, article_title, personal_tone=True):
        """Generate a reply to a comment on a LinkedIn post
        
        Args:
            comment (str): The comment to reply to
            article_title (str): Title of the article that was shared
            personal_tone (bool): Whether to use a more personal tone in the reply
        
        Returns:
            str: The generated reply
        """
        if not self.api_key:
            print("Groq API key not found. Using fallback reply.")
            return self._generate_fallback_reply(comment, article_title)
        
        # Create prompt for generating comment reply
        prompt = f"""
        You are a professional AI specialist responding to a comment on your LinkedIn post about this AI news article: "{article_title}".
        
        The comment you're responding to is:
        "{comment}"
        
        Generate a thoughtful, authentic reply that:
        
        1. Sounds like a real person wrote it, not AI
        2. Is appreciative and engaging
        3. Adds value through personal insight or additional information
        4. Is concise (50-100 words maximum)
        5. Potentially asks a follow-up question if appropriate
        
        WRITING STYLE:
        - Conversational and authentic
        - Use "I" statements occasionally
        - Sound genuinely interested in the commenter's perspective
        - Be slightly informal but still professional
        - Include personality through word choice and phrasing
        - Use 1-2 simple emojis if appropriate (not at beginning of sentences)
        
        AVOID:
        - Generic, template-style responses
        - Overly formal language
        - Anything that sounds AI-generated
        - Excessive use of emojis or exclamation marks
        - Being argumentative or condescending
        - Promoting anything
        - Using too manu emojies
        - Writing lenghty posts
        
        Return ONLY the reply text with no additional explanations or formatting.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use primarily llama3 for more natural replies
        model = "llama3-70b-8192"
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                reply_content = result['choices'][0]['message']['content'].strip()
                
                # Quality check
                if len(reply_content) < 10:
                    print("Warning: Generated reply is too short, regenerating...")
                    return self.generate_comment_reply(comment, article_title, personal_tone)
                
                return reply_content
            else:
                print(f"Error with Groq API: {response.status_code}")
                print(f"Response: {response.text}")
                return self._generate_fallback_reply(comment, article_title)
        except Exception as e:
            print(f"Exception with Groq API: {str(e)}")
            return self._generate_fallback_reply(comment, article_title)

    def _generate_fallback_reply(self, comment, article_title):
        """Generate a fallback reply if LLM generation fails"""
        # Create an array of template responses to randomly choose from
        templates = [
            "Thanks for sharing your thoughts! I appreciate your perspective on this topic.",
            
            "That's an interesting take - thanks for adding to the conversation!",
            
            "Thanks for engaging with the post! Your input adds a valuable dimension to this topic.",
            
            "Really appreciate you taking the time to comment. It's great to hear different viewpoints on these developments.",
            
            "Thanks for the comment! It's always helpful to get different perspectives on these AI developments."
        ]
        
        return random.choice(templates)