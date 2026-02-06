from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, EmailStr
from app.db.session import get_connection
from app.core.security import generate_jwt

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

# -------------------- ROUTES --------------------

@router.post("/login", response_model=UserResponse)
def login(request: LoginRequest, response: Response):
    """
    Authenticate user and return JWT token in HTTP-only cookie
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
        
        # Verify password (plain text comparison - should use bcrypt in production!)
        if request.password != db_password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate JWT token
        token = generate_jwt(str(user_id), role, email)
        
        # Set HTTP-only cookie
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=60 * 60 * 24,  # 24 hours
        )
        
        return {
            "user_id": str(user_id),
            "username": username,
            "email": email,
            "role": role,
            "access_token": token
        }
    
    finally:
        cur.close()
        conn.close()


@router.post("/signup", response_model=UserResponse)
def signup(request: SignupRequest, response: Response):
    """
    Register new user and return JWT token in HTTP-only cookie
    """
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Check if email already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (request.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Insert new user (default role is 'user')
        cur.execute(
            """
            INSERT INTO users (username, email, password, role)
            VALUES (%s, %s, %s, 'user')
            RETURNING id
            """,
            (request.username, request.email, request.password)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        
        # Generate JWT token
        token = generate_jwt(str(user_id), 'user', request.email)
        
        # Set HTTP-only cookie
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=60 * 60 * 24,  # 24 hours
        )
        
        return {
            "user_id": str(user_id),
            "username": request.username,
            "email": request.email,
            "role": "user",
            "access_token": token
        }
    
    finally:
        cur.close()
        conn.close()


@router.post("/logout")
def logout(response: Response):
    """
    Clear authentication cookie
    """
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}
