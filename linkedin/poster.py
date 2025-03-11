"""
LinkedIn posting module
"""

import json
import requests

class LinkedInPoster:
    """Class for posting content to LinkedIn"""
    
    def __init__(self, auth):
        """Initialize with LinkedIn authentication"""
        self.auth = auth
    
    def create_text_post(self, content):
        """Create a text post to LinkedIn"""
        if not self.auth.access_token:
            print("Not authenticated. Please run authenticate() first.")
            return False
        
        # Get user profile information to get the correct author format
        user_profile = self.auth.get_user_profile()
        if not user_profile or not self.auth.person_id:
            print("Could not determine author format")
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
            print(f"Successfully posted to LinkedIn! Post ID: {post_id}")
            return True
        else:
            print(f"Failed to post: {response.status_code}")
            print(f"Response: {response.text}")
            return False