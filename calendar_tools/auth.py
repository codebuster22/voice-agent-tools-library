import os
import json
import asyncio
import webbrowser
from datetime import datetime, timezone
from urllib.parse import urlencode, parse_qs, urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = 'http://localhost:8080/callback'

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/callback'):
            query = urlparse(self.path).query
            params = parse_qs(query)
            
            if 'code' in params:
                self.server.auth_code = params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body><h1>Authorization successful!</h1><p>You can close this window.</p></body></html>')
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body><h1>Authorization failed!</h1></body></html>')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logging

async def create_service(email=None):
    """Create authenticated Google Calendar service using OAuth 2.0."""
    if not email:
        email = os.getenv('GOOGLE_USER_EMAIL')
        if not email:
            raise ValueError("Email must be provided either as parameter or in GOOGLE_USER_EMAIL env variable")
    
    # Check for existing tokens
    token_file = Path(f"tokens/{email}_tokens.json")
    credentials = None
    
    if token_file.exists():
        credentials = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    
    # Refresh tokens if expired
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            _save_credentials(credentials, email)
        except Exception as e:
            print(f"Token refresh failed: {e}")
            credentials = None
    
    # If no valid credentials, start OAuth flow
    if not credentials or not credentials.valid:
        credentials = await _oauth_flow(email)
    
    service = build('calendar', 'v3', credentials=credentials)
    return service

async def _oauth_flow(email):
    """Perform OAuth 2.0 authorization flow with local server."""
    # Load client secrets from environment variables or file
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if client_id and client_secret:
        # Use environment variables
        client_config = {
            'client_id': client_id,
            'client_secret': client_secret
        }
        print("Using Google credentials from environment variables")
    else:
        # Fallback to client_secret.json file
        client_secrets_file = "client_secret.json"
        if not Path(client_secrets_file).exists():
            raise FileNotFoundError(f"Client secrets file not found: {client_secrets_file} and GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET not set")
        
        with open(client_secrets_file, 'r') as f:
            client_data = json.load(f)
            client_config = client_data.get('installed') or client_data.get('web')
            if not client_config:
                raise ValueError("Invalid client secrets file format. Expected 'installed' or 'web' key.")
    
    # Build authorization URL
    auth_params = {
        'client_id': client_config['client_id'],
        'redirect_uri': REDIRECT_URI,
        'scope': ' '.join(SCOPES),
        'response_type': 'code',
        'access_type': 'offline',
        'prompt': 'consent',
        'state': email
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(auth_params)}"
    
    print(f"\nStarting OAuth flow for {email}")
    print(f"Please visit this URL to authorize access:")
    print(f"{auth_url}")
    
    # Start local server to catch callback
    server = HTTPServer(('localhost', 8080), CallbackHandler)
    server.auth_code = None
    
    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Open browser automatically
    try:
        webbrowser.open(auth_url)
        print("Browser opened automatically. If not, please copy and paste the URL above.")
    except:
        print("Could not open browser automatically. Please copy and paste the URL above.")
    
    # Wait for authorization code
    print("Waiting for authorization...")
    while server.auth_code is None:
        await asyncio.sleep(0.5)
    
    auth_code = server.auth_code
    server.shutdown()
    
    # Exchange code for tokens
    credentials = await _exchange_code_for_tokens(auth_code, client_config)
    _save_credentials(credentials, email)
    
    print(f"Authorization successful! Tokens saved for {email}")
    return credentials

async def _exchange_code_for_tokens(auth_code, client_config):
    """Exchange authorization code for access and refresh tokens."""
    import urllib.request
    import urllib.parse
    
    token_data = {
        'code': auth_code,
        'client_id': client_config['client_id'],
        'client_secret': client_config['client_secret'],
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    
    token_url = 'https://oauth2.googleapis.com/token'
    data = urllib.parse.urlencode(token_data).encode()
    
    req = urllib.request.Request(token_url, data=data)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    with urllib.request.urlopen(req) as response:
        token_response = json.loads(response.read().decode())
    
    # Create credentials object
    credentials = Credentials(
        token=token_response['access_token'],
        refresh_token=token_response.get('refresh_token'),
        token_uri=token_url,
        client_id=client_config['client_id'],
        client_secret=client_config['client_secret'],
        scopes=SCOPES
    )
    
    return credentials

def _save_credentials(credentials, email):
    """Save credentials to file."""
    token_file = Path(f"tokens/{email}_tokens.json")
    token_file.parent.mkdir(exist_ok=True)
    
    cred_data = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes,
        'email': email,
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    
    with open(token_file, 'w') as f:
        json.dump(cred_data, f, indent=2)
    
    # Set secure permissions
    token_file.chmod(0o600)