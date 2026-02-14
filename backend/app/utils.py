from passlib.context import CryptContext

<<<<<<< HEAD
# This tells the system to use "Bcrypt", a standard security algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
=======
# Use bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Max bytes for bcrypt
MAX_BCRYPT_BYTES = 72

def hash_password(password: str) -> str:
    """
    Hash password safely, truncating to 72 bytes.
    """
    truncated = password.encode("utf-8")[:MAX_BCRYPT_BYTES]
    return pwd_context.hash(truncated)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password safely, truncating to 72 bytes.
    """
    truncated = plain_password.encode("utf-8")[:MAX_BCRYPT_BYTES]
    return pwd_context.verify(truncated, hashed_password)
>>>>>>> 526d1f3e7242931859b44adfb2172bd7426d4457
