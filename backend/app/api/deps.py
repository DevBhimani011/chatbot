from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.db.session import get_connection

# Defines the tokenUrl. Clients (like Swagger UI) will use this to get the token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-json")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """
    Validates the JWT token from the Authorization header.
    Returns the user dictionary if valid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Check if user exists in DB
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, username, email, role FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        
        if user is None:
            raise credentials_exception
            
        return {
            "id": str(user[0]),
            "username": user[1],
            "email": user[2],
            "role": user[3]
        }
    except Exception:
        raise credentials_exception
    finally:
        cur.close()
        conn.close()

def get_current_admin_user(current_user: Annotated[dict, Depends(get_current_user)]):
    """
    Dependency to check if the current user has 'admin' role.
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
