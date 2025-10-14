import httpx
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.models import User
from app.services.user_service import UserService


class GoogleAuthService:

    @staticmethod
    async def verify_google_token(token: str) -> dict:
        """
        Универсальная верификация Google токена (ID token или access token)
        """
        try:
            print(f"🔍 Verifying Google token (length: {len(token)})...")

            # Сначала пробуем верифицировать как ID token
            try:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    requests.Request(),
                    settings.GOOGLE_CLIENT_ID
                )
                print("✅ Successfully verified as ID token")
                return idinfo
            except ValueError as id_token_error:
                print(f"⚠️ Not an ID token: {str(id_token_error)}")

                # Если не ID token, пробуем использовать как access token
                print("🔄 Trying to verify as access token...")
                return await GoogleAuthService.verify_access_token(token)

        except Exception as e:
            print(f"❌ Token verification failed: {str(e)}")
            raise ValueError(f"Invalid Google token: {str(e)}")

    @staticmethod
    async def verify_access_token(access_token: str) -> dict:
        """
        Верификация Google access token через Google API
        """
        try:
            print("🔍 Verifying access token via Google API...")

            async with httpx.AsyncClient() as client:
                # Вариант 1: Получаем информацию о токене
                token_info_response = await client.get(
                    f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
                )

                if token_info_response.status_code == 200:
                    token_info = token_info_response.json()
                    print(f"✅ Access token info: {token_info}")

                    # Проверяем, что токен действителен и для нашего client_id
                    if token_info.get('audience') != settings.GOOGLE_CLIENT_ID:
                        raise ValueError("Token audience does not match our client ID")

                    # Получаем информацию о пользователе
                    user_info_response = await client.get(
                        "https://www.googleapis.com/oauth2/v3/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )

                    if user_info_response.status_code == 200:
                        user_info = user_info_response.json()
                        print(f"✅ User info: {user_info}")

                        # Форматируем в тот же формат, что и ID token
                        return {
                            'sub': user_info.get('sub'),
                            'email': user_info.get('email'),
                            'email_verified': user_info.get('email_verified', False),
                            'name': user_info.get('name'),
                            'picture': user_info.get('picture'),
                            'given_name': user_info.get('given_name'),
                            'family_name': user_info.get('family_name'),
                            'iss': 'https://accounts.google.com',
                            'aud': settings.GOOGLE_CLIENT_ID,
                        }
                    else:
                        raise ValueError("Failed to get user info")
                else:
                    error_detail = token_info_response.json()
                    raise ValueError(f"Invalid access token: {error_detail.get('error_description', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Access token verification failed: {str(e)}")
            raise ValueError(f"Invalid access token: {str(e)}")