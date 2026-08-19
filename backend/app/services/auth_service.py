from sqlalchemy.orm import Session
from app.models import User
from app.auth import verify_password, get_password_hash

def authenticate(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def init_default_users(db: Session):
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin_user = User(username="admin", role="admin", password_hash=get_password_hash("admin"))
        db.add(admin_user)
    
    user = db.query(User).filter(User.username == "user").first()
    if not user:
        normal_user = User(username="user", role="user", password_hash=get_password_hash("user"))
        db.add(normal_user)
        
    db.commit()
