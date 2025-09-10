#!/usr/bin/env python3
"""
Gmail OAuth Integration for ClAP
Handles complete OAuth flow for Gmail MCP authentication

Usage:
  python3 gmail_oauth_integration.py generate-url  # Generate OAuth URL
  python3 gmail_oauth_integration.py exchange CODE # Exchange auth code for tokens
  python3 gmail_oauth_integration.py setup         # Complete initial setup
"""

import os
import sys
import json
import urllib.parse
import urllib.request
from pathlib import Path

# Add utils directory to path using cleaner approach
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
UTILS_DIR = PROJECT_ROOT / 'utils'
sys.path.insert(0, str(UTILS_DIR))
from infrastructure_config_reader import get_config_value

class GmailOAuthIntegrator:
    def __init__(self):
        self.home_dir = Path.home()
        self.gmail_mcp_dir = self.home_dir / '.gmail-mcp'
        self.oauth_keys_file = self.gmail_mcp_dir / 'gcp-oauth.keys.json'
        self.credentials_file = self.gmail_mcp_dir / 'credentials.json'
        
        # OAuth configuration
        self.client_id = get_config_value('GOOGLE_CLIENT_ID')
        self.project_id = get_config_value('GOOGLE_PROJECT_ID')
        # OAuth client credential
        self.google_oauth_credential = get_config_value('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = get_config_value('GOOGLE_REDIRECT_URI', 'http://localhost:3000/oauth2callback')
        
        # OAuth URLs and scopes
        self.auth_uri = "https://accounts.google.com/o/oauth2/auth"
        self.token_uri = "https://oauth2.googleapis.com/token"
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.modify"
        ]
    
    def validate_config(self):
        """Validate that required OAuth configuration is present"""
        missing = []
        if not self.client_id or self.client_id == 'your-google-client-id':
            missing.append('GOOGLE_CLIENT_ID')
        if not self.google_oauth_credential or self.google_oauth_credential.startswith('your-google-client'):
            missing.append('GOOGLE_CLIENT_SECRET')
            
        if missing:
            print("❌ Missing required OAuth configuration:")
            for item in missing:
                print(f"   - {item}")
            print("\n📝 Please add these values to claude_infrastructure_config.txt")
            return False
        return True
    
    def ensure_directory_structure(self):
        """Create necessary directories and files"""
        print(f"📁 Creating Gmail MCP directory: {self.gmail_mcp_dir}")
        self.gmail_mcp_dir.mkdir(exist_ok=True)
        
        # Create OAuth keys file
        oauth_keys_content = {
            "web": {
                "client_id": self.client_id,
                "project_id": self.project_id,
                "auth_uri": self.auth_uri,
                "token_uri": self.token_uri,
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": self.google_oauth_credential,
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        print(f"📝 Creating OAuth keys file: {self.oauth_keys_file}")
        with open(self.oauth_keys_file, 'w') as f:
            json.dump(oauth_keys_content, f, indent=2)
        
        return True
    
    def generate_oauth_url(self):
        """Generate OAuth authorization URL"""
        if not self.validate_config():
            return None
            
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'  # Force consent screen to get refresh token
        }
        
        url = f"{self.auth_uri}?{urllib.parse.urlencode(params)}"
        return url
    
    def exchange_code_for_tokens(self, authorization_code):
        """Exchange authorization code for access and refresh tokens"""
        if not self.validate_config():
            return False
            
        # Prepare token exchange request
        data = {
            'code': authorization_code,
            'client_id': self.client_id,
            'client_secret': self.google_oauth_credential,
            'redirect_uri': self.redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        # Make request to Google OAuth token endpoint
        try:
            req_data = urllib.parse.urlencode(data).encode('utf-8')
            request = urllib.request.Request(
                self.token_uri,
                data=req_data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            print("🔄 Exchanging authorization code for tokens...")
            
            with urllib.request.urlopen(request) as response:
                tokens = json.loads(response.read().decode('utf-8'))
            
            # Calculate expiry date (current time + expires_in seconds)
            import time
            expiry_date = int((time.time() + tokens.get('expires_in', 3600)) * 1000)
            tokens['expiry_date'] = expiry_date
            
            # Save credentials
            print(f"💾 Saving credentials to: {self.credentials_file}")
            with open(self.credentials_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            
            # Display success information
            print("✅ Gmail OAuth authentication successful!")
            print(f"🔑 Access token expires in: {tokens.get('expires_in', 'unknown')} seconds")
            
            if 'refresh_token' in tokens:
                print("🔄 Refresh token obtained - can automatically renew access")
            else:
                print("⚠️  No refresh token - may need to re-authenticate periodically")
                
            return True
            
        except Exception as e:
            print(f"❌ Error exchanging authorization code: {e}")
            return False
    
    def check_existing_credentials(self):
        """Check if valid credentials already exist"""
        if not self.credentials_file.exists():
            return False
            
        try:
            with open(self.credentials_file, 'r') as f:
                credentials = json.load(f)
            
            # Check if credentials have required fields
            required_fields = ['access_token', 'token_type']
            if all(field in credentials for field in required_fields):
                print("✅ Existing credentials found")
                
                # Check expiry if available
                if 'expiry_date' in credentials:
                    import time
                    expiry_time = credentials['expiry_date'] / 1000
                    if time.time() < expiry_time:
                        print("✅ Credentials are still valid")
                        return True
                    else:
                        print("⚠️  Credentials have expired")
                
                return True
            else:
                print("⚠️  Existing credentials are incomplete")
                return False
                
        except Exception as e:
            print(f"⚠️  Error reading existing credentials: {e}")
            return False

def main():
    if len(sys.argv) < 2:
        print("Gmail OAuth Integration for ClAP")
        print("\nUsage:")
        print("  python3 gmail_oauth_integration.py generate-url")
        print("  python3 gmail_oauth_integration.py exchange CODE")
        print("  python3 gmail_oauth_integration.py setup")
        sys.exit(1)
    
    integrator = GmailOAuthIntegrator()
    command = sys.argv[1]
    
    if command == "generate-url":
        print("🔗 Generating Gmail OAuth authorization URL...")
        url = integrator.generate_oauth_url()
        if url:
            print("\n📋 OAuth Authorization Steps:")
            print("1. Click this URL to authorize Gmail access:")
            print(f"   {url}")
            print("\n2. Grant permissions in your browser")
            print("3. Copy the authorization code from the callback URL")
            print("4. Run: python3 gmail_oauth_integration.py exchange YOUR_CODE")
        
    elif command == "exchange":
        if len(sys.argv) < 3:
            print("❌ Please provide the authorization code")
            print("Usage: python3 gmail_oauth_integration.py exchange YOUR_CODE")
            sys.exit(1)
        
        authorization_code = sys.argv[2]
        success = integrator.exchange_code_for_tokens(authorization_code)
        
        if success:
            print("\n🎉 Gmail OAuth setup complete!")
            print("Gmail MCP is now ready to use.")
        else:
            print("\n❌ OAuth setup failed. Please try again.")
            sys.exit(1)
    
    elif command == "setup":
        print("🚀 Starting Gmail OAuth setup...")
        
        # Check existing credentials first
        if integrator.check_existing_credentials():
            print("✅ Gmail OAuth already configured!")
            print("Use generate-url command to re-authenticate if needed.")
            return
        
        # Ensure directory structure
        if not integrator.ensure_directory_structure():
            print("❌ Failed to create directory structure")
            sys.exit(1)
        
        # Generate URL for user
        url = integrator.generate_oauth_url()
        if url:
            print("\n📋 Gmail OAuth Setup Instructions:")
            print("1. Open this URL in your browser:")
            print(f"   {url}")
            print("\n2. Grant Gmail permissions")
            print("3. Copy the authorization code from the callback URL")
            print("4. Run: python3 gmail_oauth_integration.py exchange YOUR_CODE")
            print("\n💡 The callback URL will look like:")
            print("   http://localhost:3000/oauth2callback?code=YOUR_CODE_HERE")
        
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()