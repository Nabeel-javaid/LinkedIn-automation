import requests # type: ignore
import json
import webbrowser
import urllib.parse
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

class LinkedInPoster:
    def __init__(self):
        # LinkedIn API credentials
        self.client_id = os.environ.get('LINKEDIN_CLIENT_ID')
        self.client_secret = os.environ.get('LINKEDIN_CLIENT_SECRET')
        self.redirect_uri = 'http://localhost:8000/callback'
        
        # LinkedIn API endpoints
        self.auth_url = "https://www.linkedin.com/oauth/v2/authorization"
        self.token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        self.api_url = "https://api.linkedin.com/v2"
        
        # Store access token
        self.access_token = None
        
        # Flag for callback completion
        self.auth_completed = False
        
        # Your LinkedIn ID
        self.person_id = None  # This will be retrieved during authentication
    
    def authenticate(self):
        """Start OAuth flow with updated scopes"""
        auth_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': 'openid profile email w_member_social',  # Updated scopes
            'state': 'linkedin_state'
        }
        
        auth_url = f"{self.auth_url}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"
        
        print("Opening browser for LinkedIn authentication...")
        print(f"Authorization URL: {auth_url}")
        webbrowser.open(auth_url)
        
        # Start local server to receive callback
        server_thread = threading.Thread(target=self._start_callback_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for authentication to complete
        print("Waiting for authentication to complete...")
        while not self.auth_completed:
            time.sleep(1)
        
        # Give the server thread time to shut down properly
        time.sleep(2)
        
        return self.access_token is not None
    
    def _start_callback_server(self):
        """Start a local server to receive the OAuth callback"""
        poster = self
        server = None
        
        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                # Parse the query parameters
                query = urllib.parse.urlparse(self.path).query
                params = dict(urllib.parse.parse_qsl(query))
                
                # Send headers first
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                if 'code' in params:
                    # Exchange authorization code for access token
                    success = poster._exchange_code_for_token(params['code'])
                    
                    if success:
                        self.wfile.write(b"Authentication successful! You can close this window.")
                    else:
                        self.wfile.write(b"Authentication failed during token exchange. Check console for details.")
                    
                elif 'error' in params:
                    # Show error details
                    error = params.get('error', 'unknown')
                    error_desc = params.get('error_description', 'No description provided')
                    
                    error_html = f"""
                    <html>
                    <body>
                        <h2>Authentication Error</h2>
                        <p>Error: {error}</p>
                        <p>Description: {error_desc}</p>
                        <p>Please check the console for troubleshooting steps.</p>
                    </body>
                    </html>
                    """.encode('utf-8')
                    
                    self.wfile.write(error_html)
                    print(f"\nLinkedIn OAuth Error: {error}")
                    print(f"Error Description: {error_desc}")
                else:
                    # Handle unexpected response
                    self.wfile.write(b"Unexpected response from LinkedIn. Check console for details.")
                
                # Signal that we're done with authentication
                poster.auth_completed = True
        
        try:
            server = HTTPServer(('localhost', 8000), CallbackHandler)
            print("Callback server started. Waiting for authentication...")
            server.handle_request()
        except Exception as e:
            print(f"Error with callback server: {str(e)}")
        finally:
            if server:
                server.server_close()
                print("Callback server closed.")
    
    def _exchange_code_for_token(self, code):
        """Exchange authorization code for access token"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(self.token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            print(f"Successfully obtained access token. Expires in {token_data.get('expires_in')} seconds")
            print(f"Token: {self.access_token[:10]}... (truncated for security)")
            return True
        else:
            print(f"Failed to get access token: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    def get_user_profile(self):
        """Get the user profile information using OpenID Connect"""
        if not self.access_token:
            print("Not authenticated. Please run authenticate() first.")
            return None

        url = f"{self.api_url}/userinfo"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"Successfully retrieved profile: {json.dumps(data, indent=2)}")
                self.person_id = data.get('sub').split(':')[-1] if 'sub' in data else None
                return data
            else:
                print(f"Failed to get profile: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"Error getting profile: {str(e)}")
            return None
    
    def create_text_post(self, content):
        """Create a text post to LinkedIn"""
        if not self.access_token:
            print("Not authenticated. Please run authenticate() first.")
            return False

        # Get user profile information to get the correct author format
        user_profile = self.get_user_profile()
        if not user_profile or not self.person_id:
            print("Could not determine author format")
            return False

        url = f"{self.api_url}/ugcPosts"

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        author_format = f"urn:li:person:{self.person_id}"

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

# Example usage
if __name__ == "__main__":
    # Check if credentials are set
    if not os.environ.get('LINKEDIN_CLIENT_ID') or not os.environ.get('LINKEDIN_CLIENT_SECRET'):
        print("Please set the LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET environment variables.")
        # exit(1)
    
    # Create LinkedIn poster and authenticate
    poster = LinkedInPoster()
    
    # You can set a token manually if you already have one
    # poster.access_token = "YOUR_ACCESS_TOKEN"
    
    if not poster.access_token:
        if not poster.authenticate():
            print("Authentication failed. Cannot proceed with posting.")
            exit(1)
    
    print("\n--- Ready to post to LinkedIn ---\n")
    
    # Create a text post
    content = input("Enter your post content: ")
    result = poster.create_text_post(content)
    
    if result:
        print("\n=== SUCCESS ===")
        print(f"Successfully created LinkedIn post")
    else:
        print("\n=== LINKEDIN API LIMITATIONS ===")
        print("We couldn't post to LinkedIn.")
        print("This could be due to one of the following reasons:")
        print("1. Your LinkedIn Developer App doesn't have required permissions")
        print("2. LinkedIn's API has changed since this script was created")
        print("3. The API access pattern requires Marketing Developer Partner status")

        print("\nRecommended alternatives:")
        print("- Use approved third-party tools like Buffer, Hootsuite, or Later")
        print("- Apply for Marketing Developer Partner status with LinkedIn")
        print("- Use LinkedIn's website directly")