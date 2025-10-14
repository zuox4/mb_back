import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import EmailLog


class SMTPEmailService:

    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS

    def send_verification_email(
            self,
            db: Session,
            email: str,
            verification_token: str,
            user_name: str = None
    ) -> bool:
        """
        Отправка email с ссылкой подтверждения через SMTP
        """
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

            # Создаем HTML и текстовый контент
            html_content = self._create_verification_email_html(
                user_name=user_name,
                verification_url=verification_url
            )
            text_content = self._create_verification_email_text(
                user_name=user_name,
                verification_url=verification_url
            )

            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Подтверждение регистрации - {settings.SCHOOL_NAME}"
            msg['From'] = f"{settings.SCHOOL_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = email
            msg['Reply-To'] = f"support@{settings.SCHOOL_DOMAIN}"

            # Добавляем текстовую и HTML версии
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)

            # Отправка email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            # Логируем успешную отправку
            email_log = EmailLog(
                email=email,
                subject=msg['Subject'],
                template_name="email_verification",
                status="sent"
            )
            db.add(email_log)
            db.commit()

            print(f"✅ Verification email sent to: {email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send verification email to {email}: {e}")

            # Логируем ошибку
            email_log = EmailLog(
                email=email,
                subject="Email Verification",
                template_name="email_verification",
                status="failed",
                error_message=str(e)
            )
            db.add(email_log)
            db.commit()
            return False

    def send_password_reset_email(
            self,
            db: Session,
            email: str,
            new_password: str,
            user_name: str = None
    ) -> bool:
        """
        Отправка email с новым паролем через SMTP
        """
        try:
            # Создаем HTML и текстовый контент

            text_content = self._create_password_reset_email_text(
                user_name=user_name,
                new_password=new_password
            )

            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Восстановление пароля - {settings.SCHOOL_NAME}"
            msg['From'] = f"{settings.SCHOOL_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = email
            msg['Reply-To'] = f"support@{settings.SCHOOL_DOMAIN}"

            # Добавляем текстовую и HTML версии
            part1 = MIMEText(text_content, 'plain', 'utf-8')

            msg.attach(part1)


            # Отправка email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            # Логируем успешную отправку
            email_log = EmailLog(
                email=email,
                subject=msg['Subject'],
                template_name="password_reset",
                status="sent"
            )
            db.add(email_log)
            db.commit()

            print(f"✅ Password reset email sent to: {email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send password reset email to {email}: {e}")

            # Логируем ошибку
            email_log = EmailLog(
                email=email,
                subject="Password Reset",
                template_name="password_reset",
                status="failed",
                error_message=str(e)
            )
            db.add(email_log)
            db.commit()
            return False

    def _create_password_reset_email_text(self, user_name: str, new_password: str) -> str:
        """
        Создание текстовой версии письма для восстановления пароля
        """
        return f"""
Здравствуйте, {user_name}!

Вы запросили восстановление пароля для доступа к электронной системе учета достижений учеников профильных классов Школы 1298.

Ваш новый пароль для входа в систему:
{new_password}

Рекомендуем после входа в систему изменить пароль в личном кабинете.

Основные возможности платформы:
• Электронная зачетная книжка
• Учет достижений и мероприятий
• Отслеживание прогресса обучения
• Доступ к материалам профильных классов

Если вы не запрашивали восстановление пароля, пожалуйста, свяжитесь с администратором системы.

С уважением,
Команда Школы 1298 «Профиль Курикно»

📧 Это письмо сгенерировано автоматически. Пожалуйста, не отвечайте на него.
Школа 1298 © 2024. Все права защищены.
"""
    def send_welcome_email(
            self,
            db: Session,
            email: str,
            user_name: str = None
    ) -> bool:
        """
        Отправка приветственного email после подтверждения
        """
        try:
            # Создаем HTML и текстовый контент
            html_content = self._create_welcome_email_html(user_name)
            text_content = self._create_welcome_email_text(user_name)

            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Добро пожаловать в {settings.SCHOOL_NAME}!"
            msg['From'] = f"{settings.SCHOOL_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = email

            # Добавляем текстовую и HTML версии
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part1)
            msg.attach(part2)

            # Отправка email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            # Логируем успешную отправку
            email_log = EmailLog(
                email=email,
                subject=msg['Subject'],
                template_name="welcome_email",
                status="sent"
            )
            db.add(email_log)
            db.commit()

            print(f"✅ Welcome email sent to: {email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send welcome email: {e}")

            # Логируем ошибку
            email_log = EmailLog(
                email=email,
                subject="Welcome Email",
                template_name="welcome_email",
                status="failed",
                error_message=str(e)
            )
            db.add(email_log)
            db.commit()
            return False

    def _create_verification_email_text(self, user_name: str, verification_url: str) -> str:
        """
        Создание текстовой версии письма для подтверждения
        """
        return f"""
Здравствуйте, {user_name}!

Рады Вашей регистрации в электронной системе учета достижений учеников профильных классов Школы 1298. 
Платформа является электронной зачетной книжкой и поможет отслеживать ключевые мероприятия профиля 
и Ваши достижения за 10-11 класс.

Основные возможности платформы:
• Электронная зачетная книжка
• Учет достижений и мероприятий
• Отслеживание прогресса обучения
• Доступ к материалам профильных классов

Для завершения регистрации необходимо подтвердить e-mail адрес, перейдя по ссылке:
{verification_url}

⏰ Ссылка действительна в течение 24 часов.

Если вы не регистрировались в нашей системе, пожалуйста, проигнорируйте это письмо.

С уважением,
Команда Школы 1298 «Профиль Курикно»

📧 Это письмо сгенерировано автоматически. Пожалуйста, не отвечайте на него.
Школа 1298 © 2024. Все права защищены.
"""

    def _create_verification_email_html(self, user_name: str, verification_url: str) -> str:
        """
        Создание HTML письма для подтверждения (оставляем ваш существующий HTML)
        """
        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Регистрация в системе учета достижений</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333333;
            margin: 0;
            padding: 0;
            background-color: #ffffff;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: #043951;
            color: white;
            padding: 40px 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .logo {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
            color: white;
        }}
        .subtitle {{
            font-size: 18px;
            opacity: 0.9;
            margin-bottom: 0;
            color: white;
        }}
        .content {{
            padding: 40px 30px;
            color: #333333;
            background: white;
        }}
        .greeting {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 25px;
            color: #043951;
        }}
        .button {{
            display: inline-block;
            background: #00a713;
            color: white;
            padding: 16px 35px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 18px;
            margin: 25px 0;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0, 167, 19, 0.3);
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }}
        .button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 167, 19, 0.4);
        }}
        .verification-code {{
            background: #f8f9fa;
            border: 2px dashed #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            word-break: break-all;
            text-align: center;
            color: #495057;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 30px;
            border-top: 1px solid #e9ecef;
            color: #6c757d;
            font-size: 14px;
            background: white;
        }}
        .highlight {{
            background: linear-gradient(120deg, #e3f2fd 0%, #e3f2fd 100%);
            padding: 15px;
            border-left: 4px solid #2196f3;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        @media (max-width: 600px) {{
            .container {{
                margin: 10px;
            }}
            .content {{
                padding: 25px 20px;
            }}
            .header {{
                padding: 30px 20px;
            }}
            .logo {{
                font-size: 28px;
            }}
        }}
        /* Отключаем темную тему */
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #ffffff;
                color: #333333;
            }}
            .container {{
                background: white;
            }}
            .content {{
                background: white;
                color: #333333;
            }}
            .footer {{
                background: white;
                color: #6c757d;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">Школа 1298 «Профиль Курикно»</div>
            <div class="subtitle">Регистрация в системе учета достижений</div>
        </div>

        <div class="content">
            <div class="greeting">Здравствуйте, {user_name}!</div>

            <p>Рады Вашей регистрации в электронной системе учета достижений учеников профильных классов Школы 1298. Платформа является электронной зачетной книжкой и поможет отслеживать ключевые мероприятия профиля и Ваши достижения за 10-11 класс.</p>

            <div class="highlight">
                <strong>📚 Основные возможности платформы:</strong><br>
                • Электронная зачетная книжка<br>
                • Учет достижений и мероприятий<br>
                • Отслеживание прогресса обучения<br>
                • Доступ к материалам профильных классов
            </div>

            <p>Для завершения регистрации необходимо подтвердить e-mail адрес:</p>

            <div style="text-align: center;">
                <a href="{verification_url}" class="button">
                    ✅ Подтвердить Email
                </a>
            </div>

            <p>Или скопируйте и вставьте в браузер следующую ссылку:</p>

            <div class="verification-code">
                {verification_url}
            </div>

            <p><strong>⏰ Ссылка действительна в течение 24 часов.</strong></p>

            <p>Если вы не регистрировались в нашей системе, пожалуйста, проигнорируйте это письмо.</p>

            <div class="footer">
                <p>С уважением,<br>
                <strong>Команда Школы 1298 «Профиль Курикно»</strong></p>
                <p>📧 Это письмо сгенерировано автоматически. Пожалуйста, не отвечайте на него.</p>
                <p style="font-size: 12px; margin-top: 10px; color: #adb5bd;">
                    Школа 1298 © 2024. Все права защищены.
                </p>
            </div>
        </div>
    </div>
</body>
</html>"""

    def _create_welcome_email_text(self, user_name: str) -> str:
        """
        Создание текстовой версии приветственного письма
        """
        return f"""
Здравствуйте{', ' + user_name if user_name else ''}!

Мы рады приветствовать вас в образовательной платформе {settings.SCHOOL_NAME}!

Теперь вам доступны все возможности системы:
• 📊 Просмотр достижений в мероприятиях и олимпиадах

Если у вас возникнут вопросы, обращайтесь к администратору.

С уважением,
Команда {settings.SCHOOL_NAME}
"""

    def _create_welcome_email_html(self, user_name: str) -> str:
        """
        Создание приветственного письма (оставляем ваш существующий HTML)
        """
        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: #043951;
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }}
                .content {{
                    background: white;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
            @media (prefers-color-scheme: dark) {{
                body {{
                    background-color: #ffffff;
                    color: #333333;
                }}
                .container {{
                    background: white;
                }}
                .content {{
                    background: white;
                    color: #333333;
                }}
                .footer {{
                    background: white;
                    color: #6c757d;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 Добро пожаловать!</h1>
                <p>Ваш аккаунт успешно активирован</p>
            </div>
            <div class="content">
                <h2>Здравствуйте{', ' + user_name if user_name else ''}!</h2>
                <p>Мы рады приветствовать вас в образовательной платформе <strong>{settings.SCHOOL_NAME}</strong>!</p>

                <p>Теперь вам доступны все возможности системы:</p>
                <ul>
                    <li>📊 Просмотр ваших достижений и оценок</li>
                    <li>📅 Доступ к расписанию занятий</li>
                    <li>👨‍🏫 Общение с преподавателями</li>
                    <li>🏆 Участие в мероприятиях и олимпиадах</li>
                </ul>

                <p>Если у вас возникнут вопросы, обращайтесь к администратору системы.</p>

                <p>С уважением,<br>
                <strong>Команда {settings.SCHOOL_NAME}</strong></p>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def generate_verification_token() -> str:
        """Генерация безопасного токена для верификации"""
        return secrets.token_urlsafe(32)


# Создаем экземпляр сервиса для удобного использования
email_service = SMTPEmailService()