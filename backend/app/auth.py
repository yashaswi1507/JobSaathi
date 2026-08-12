from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

# --- Password hashing setup ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # use bcrypt hashing

# --- JWT settings ---
SECRET_KEY = "careershield_secret_key_2024"            # secret key for signing tokens
ALGORITHM = "HS256"                                    # hashing algorithm
TOKEN_EXPIRE_HOURS = 24                                # token valid for 24 hours

# --- Hash a plain password ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)                  # return hashed password

# --- Verify plain password against hashed password ---
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)           # return True if match

# --- Create JWT token for a user ---
def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)  # set expiry
    payload = {"sub": str(user_id), "exp": expire}    # token payload
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)  # encode and return

# --- Decode and verify JWT token ---
def decode_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # decode token
        return int(payload["sub"])                     # return user id
    except JWTError:
        return None                                    # return None if invalid

print("Auth functions loaded successfully.")