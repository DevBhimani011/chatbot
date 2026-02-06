import jwt
from datetime import datetime, timedelta
from app.core.config import settings

def generate_jwt(user_id: str, role: str, email: str) -> str:
    """Generate JWT token with Hasura claims"""
    payload = {
        "sub": str(user_id),
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "https://hasura.io/jwt/claims": {
            "x-hasura-user-id": str(user_id),
            "x-hasura-default-role": role,
            "x-hasura-role": role,
            "x-hasura-allowed-roles": [role],
            "x-hasura-email": email,
        },
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
