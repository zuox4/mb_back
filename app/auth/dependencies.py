from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.auth.utils import verify_token, get_user_by_email
from app.database.models.users import User

security = HTTPBearer()


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = verify_token(credentials.credentials)

    if token_data is None:
        raise credentials_exception

    # Получаем email из sub
    email = token_data.get("sub")
    if not email:
        print("❌ No 'sub' field in token")
        raise credentials_exception

    user = get_user_by_email(db, email=email)

    if user is None:
        print(f"❌ User with email {email} not found in database")
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    print(current_user)
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Пользователь неактивен")
    return current_user


async def get_current_active_teacher(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Пользователь неактивен")

    if not any(role.name == 'teacher' for role in current_user.roles):
        raise HTTPException(status_code=403, detail="Доступно только для учителей")
    print('Был запретный запрос')
    return current_user
