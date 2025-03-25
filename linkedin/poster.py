"""
LinkedIn posting module
"""

import json
import requests
from utils.console import Console, Colors

class LinkedInPoster:
    """Class for posting content to LinkedIn"""
    
    def __init__(self, auth):
        """Initialize with LinkedIn authentication"""
        self.auth = auth
        self.last_post_id = None
    
    def create_text_post(self, content):
        """Create a text post to LinkedIn"""
        if not self.auth.access_token:
            Console.warning("Not authenticated. Please run authenticate() first.")
            return False
        
        # Get user profile information to get the correct author format
        user_profile = self.auth.get_user_profile()
        if not user_profile or not self.auth.person_id:
            Console.error("Could not determine author format")
            return False
        
        url = f"{self.auth.api_url}/ugcPosts"
        headers = {
            'Authorization': f'Bearer {self.auth.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }
        
        author_format = f"urn:li:person:{self.auth.person_id}"
        post_data = {
            "author": author_format,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        response = requests.post(url, headers=headers, json=post_data)
        
        if response.status_code in (200, 201):
            post_id = response.json().get('id')
            self.last_post_id = post_id  # Store the post ID for later use
            Console.success(f"Successfully posted to LinkedIn! Post ID: {post_id}")
            return True
        else:
            Console.error(f"Failed to post: {response.status_code}")
            Console.error(f"Response: {response.text}")
            return False
            
    def get_last_post_id(self):
        """Get the ID of the last created post"""
        return self.last_post_id