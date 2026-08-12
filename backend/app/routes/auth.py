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