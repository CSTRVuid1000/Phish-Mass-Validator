#!/usr/bin/env python3
import ssl
import smtplib
import argparse
from email.message import EmailMessage
from email.utils import formataddr

def send_mail(sender_email, sender_password, recipient, subject, body, sender_name="Sender", use_proxy=False):
    """Отправляет сообщение через SMTP."""
    try:
        # Создаем сообщение
        msg = EmailMessage()
        msg["From"] = formataddr((sender_name, sender_email))
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body, charset='utf-8')

        # Подключаемся к SMTP
        ctx = ssl.create_default_context()
        smtp = smtplib.SMTP("smtp.gmx.com", 587, timeout=30)
        smtp.set_debuglevel(0)  # Отключаем отладку SMTP-диалога
        
        # Для порта 587 используем STARTTLS
        smtp.starttls(context=ctx)
        
        # Авторизуемся и отправляем
        smtp.login(sender_email, sender_password)
        
        smtp.send_message(msg)
        smtp.quit()
        
        print("\n✅ Сообщение успешно отправлено")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Ошибка аутентификации: {e.smtp_error.decode(errors='ignore')}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Отправка сообщения через SMTP")
    parser.add_argument("sender", help="Email отправителя")
    parser.add_argument("-p", "--password", required=True, help="Пароль отправителя")
    parser.add_argument("-r", "--recipient", required=True, help="Email получателя")
    parser.add_argument("-s", "--subject", required=True, help="Тема письма")
    parser.add_argument("-b", "--body", required=True, help="Текст письма")
    parser.add_argument("-n", "--name", default="Sender", help="Имя отправителя")
    parser.add_argument("--proxy", action="store_true", help="Использовать прокси")
    
    args = parser.parse_args()
    send_mail(
        args.sender,
        args.password,
        args.recipient,
        args.subject,
        args.body,
        args.name,
        args.proxy
    )

if __name__ == "__main__":
    main() 