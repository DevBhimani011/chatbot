"""
Google OAuth 2.0 Integration

This module handles OAuth authentication with Google using Authlib.
"""

from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from app.core.config import settings

# Initialize OAuth registry
oauth = OAuth()

# Register Google OAuth provider
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


async def get_google_auth_url(request, redirect_uri: str) -> str:
    """
    Generate Google OAuth authorization URL.
    
    Args:
        request: Starlette request object
        redirect_uri: URL to redirect to after authorization
        
    Returns:
        Authorization URL with state parameter for CSRF protection
    """
    return await oauth.google.authorize_redirect(request, redirect_uri)


async def get_google_user_info(request):
    """
    Exchange authorization code for access token and fetch user info.
    
    Args:
        request: Starlette request object containing the code parameter
        
    Returns:
        dict: User information from Google containing:
            - sub: Google user ID
            - email: User's email
            - email_verified: Boolean
            - name: Full name
            - given_name: First name
            - family_name: Last name
            - picture: Profile picture URL
    """
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    return user_info
