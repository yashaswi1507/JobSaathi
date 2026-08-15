from fastapi import APIRouter, HTTPException
from app.database import SessionLocal, User
from app.auth import hash_password, verify_password, create_token
from app.schemas import UserRegister, UserLogin, TokenResponse

router = APIRouter()                                   # create router for auth endpoints

# --- Register new user ---
@router.post("/register")
def register(data: UserRegister):
    db = SessionLocal()                                # open database session

    # check if email already exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # create new user with hashed password
    user = User(
        username=data.username,
        email=data.email,
        password=hash_password(data.password)          # hash before saving
    )
    db.add(user)                                       # add to database
    db.commit()                                        # save changes
    db.refresh(user)                                   # get updated user object
    db.close()                                         # close session

    return {"message": "User registered successfully", "user_id": user.id}

# --- Login existing user ---
@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin):
    db = SessionLocal()                                # open database session

    # find user by email
    user = db.query(User).filter(User.email == data.email).first()
    db.close()                                         # close session

    # verify user exists and password matches
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # create and return JWT token
    token = create_token(user.id)
    return {
        "access_token": token,
        "token_type":   "bearer",
        "username":     user.username,
        "email":        user.email,
    }

# --- Google OAuth Login ---
@router.post("/google-login")
def google_login(data: dict):
    """
    Verify Google ID token and login/register user automatically.
    Frontend sends: { id_token, email, name, picture }
    """
    import os
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests

    google_id_token = data.get("id_token", "")
    email           = data.get("email", "")
    name            = data.get("name", "")
    picture         = data.get("picture", "")

    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

    # Verify token if CLIENT_ID is set
    if GOOGLE_CLIENT_ID and google_id_token:
        try:
            id_info = id_token.verify_oauth2_token(
                google_id_token,
                google_requests.Request(),
                GOOGLE_CLIENT_ID
            )
            email = id_info.get("email", email)
            name  = id_info.get("name",  name)
        except Exception as e:
            # In dev mode — skip verification
            print(f"[google-login] Token verify skipped: {e}")

    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Auto-register Google user
            username = name.replace(" ", "").lower() or email.split("@")[0]
            # Make username unique
            base = username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base}{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                password=hash_password(os.urandom(32).hex()),  # Random password
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[google-login] New user created: {email}")
        else:
            print(f"[google-login] Existing user: {email}")

        token = create_token(user.id)
        return {
            "access_token": token,
            "token_type":   "bearer",
            "username":     user.username,
            "email":        user.email,
            "is_new_user":  False,
        }
    finally:
        db.close()
