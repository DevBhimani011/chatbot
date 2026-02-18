from fastapi import APIRouter, HTTPException, Response, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from app.db.session import get_connection
from app.core.security import generate_jwt, verify_password, get_password_hash
from app.core.oauth import get_google_user_info
from app.core.config import settings
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])

# -------------------- MODELS --------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    access_token: str
    token_type: str = "bearer"

# -------------------- ROUTES --------------------

@router.post("/login", response_model=UserResponse)
def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    Supports seamless migration from plain-text to hashed passwords.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Check if user exists
        cur.execute(
            "SELECT id, username, email, password, role FROM users WHERE email = %s",
            (request.email,)
        )
        user = cur.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user_id, username, email, db_password, role = user
        
        if not verify_password(request.password, db_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate JWT token
        token = generate_jwt(str(user_id), role, email)
        
        return {
            "user_id": str(user_id),
            "username": username,
            "email": email,
            "role": role,
            "access_token": token,
            "token_type": "bearer"
        }
    
    finally:
        cur.close()
        conn.close()


@router.post("/signup", response_model=UserResponse)
def signup(request: SignupRequest):
    """
    Register new user and return JWT token
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Check if email already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (request.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash the password
        hashed_password = get_password_hash(request.password)
        
        # Insert new user (default role is 'user')
        cur.execute(
            """
            INSERT INTO users (username, email, password, role)
            VALUES (%s, %s, %s, 'user')
            RETURNING id
            """,
            (request.username, request.email, hashed_password)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        
        # Generate JWT token
        token = generate_jwt(str(user_id), 'user', request.email)
        
        return {
            "user_id": str(user_id),
            "username": request.username,
            "email": request.email,
            "role": "user",
            "access_token": token,
            "token_type": "bearer"
        }
    
    finally:
        cur.close()
        conn.close()


@router.post("/logout")
def logout():
    """
    Client-side logout is sufficient for JWT.
    """
    return {"message": "Logged out successfully"}


@router.post("/login-json", include_in_schema=False)
def login_for_swagger(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Dedicated endpoint for Swagger UI OAuth2 login.
    Swagger sends data as form-data (username, password).
    """
    # Create the LoginRequest object expected by our logic
    try:
        # In OAuth2 form, username field contains the email
        request = LoginRequest(email=form_data.username, password=form_data.password)
        
        # Reuse existing login logic
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(
                "SELECT id, username, email, password, role FROM users WHERE email = %s",
                (request.email,)
            )
            user = cur.fetchone()
            
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            user_id, username, email, db_password, role = user
            
            # Verify password
            if not verify_password(request.password, db_password):
                 raise HTTPException(status_code=401, detail="Invalid credentials")
            
            token = generate_jwt(str(user_id), role, email)
            
            return {
                "access_token": token,
                "token_type": "bearer"
            }
        
        finally:
            cur.close()
            conn.close()

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -------------------- GOOGLE OAUTH ROUTES --------------------

@router.get("/google/login")
async def google_login(request: Request, prompt: str = None):
    """
    Initiate Google OAuth login flow.
    Returns the Google authorization URL to redirect the user to.
    
    Query params:
    - prompt: 'select_account' to force account selection even if already logged in
    """
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    # Import here to avoid circular dependency
    from app.core.oauth import oauth
    
    # Generate authorization URL with optional prompt parameter
    extra_params = {}
    if prompt:
        extra_params['prompt'] = prompt
    
    return await oauth.google.authorize_redirect(request, redirect_uri, **extra_params)


@router.get("/google/callback", response_model=UserResponse)
async def google_callback(request: Request):
    """
    Handle Google OAuth callback.
    Exchanges authorization code for user info and creates/logs in user.
    """
    try:
        # Get user info from Google
        user_info = await get_google_user_info(request)
        
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info from Google")
        
        google_id = user_info.get('sub')
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0])
        
        if not google_id or not email:
            raise HTTPException(status_code=400, detail="Invalid user info from Google")
        
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            # Check if user exists with this Google ID
            cur.execute(
                """SELECT id, username, email, role 
                   FROM users 
                   WHERE oauth_provider = 'google' AND oauth_provider_id = %s""",
                (google_id,)
            )
            user = cur.fetchone()
            
            if user:
                # Existing Google user - log them in
                user_id, username, email, role = user
            else:
                # Check if email already exists with different provider
                cur.execute(
                    "SELECT id, oauth_provider FROM users WHERE email = %s",
                    (email,)
                )
                existing = cur.fetchone()
                
                if existing:
                    provider = existing[1]
                    raise HTTPException(
                        status_code=400,
                        detail=f"Email already registered with {provider} login. Please use {provider} to sign in."
                    )
                
                # Create new user with Google OAuth
                user_id = str(uuid.uuid4())
                cur.execute(
                    """INSERT INTO users (id, username, email, password, role, oauth_provider, oauth_provider_id)
                       VALUES (%s, %s, %s, NULL, 'user', 'google', %s)
                       RETURNING id, username, email, role""",
                    (user_id, name, email, google_id)
                )
                user = cur.fetchone()
                conn.commit()
                
                user_id, username, email, role = user
            
            # Generate JWT token
            token = generate_jwt(str(user_id), role, email)
            
            # Redirect to frontend with user data
            from fastapi.responses import RedirectResponse
            from urllib.parse import urlencode
            
            user_data = {
                "user_id": str(user_id),
                "username": username,
                "email": email,
                "role": role,
                "access_token": token,
                "token_type": "bearer"
            }
            
            # Redirect to frontend callback with data as query params
            params = urlencode(user_data)
            redirect_url = f"{settings.FRONTEND_URL}/auth/google/callback?{params}"
            
            return RedirectResponse(url=redirect_url)
            
        finally:
            cur.close()
            conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {str(e)}")
