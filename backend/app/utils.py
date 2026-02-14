from passlib.context import CryptContext

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
