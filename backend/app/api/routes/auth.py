from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from app.db.session import get_connection
from app.core.security import generate_jwt, verify_password, get_password_hash

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
