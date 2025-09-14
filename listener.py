#!/usr/bin/env python3
import imaplib
import email
import time
import schedule
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from email.utils import formataddr
import ssl

def read_senders():
    """Читает список отправителей из файла"""
    senders = []
    with open('data/senders.txt', 'r', encoding='utf-8') as f:
        for line in f:
            email, password, name = line.strip().split(':')
            senders.append({
                'email': email,
                'password': password,
                'name': name
            })
    return senders

def send_auto_reply(sender_email, sender_password, recipient_email, sender_name, original_subject, original_message):
    """Отправляет автоматический ответ на письмо с цитированием"""
    try:
        msg = MIMEMultipart()
        msg["From"] = formataddr((sender_name, sender_email))
        msg["To"] = recipient_email
        msg["Subject"] = f"Re: {original_subject}"
        
        # Формируем ответ с цитированием
        reply_body = f"""Вітаю!

Вибачаюсь за занепокоєння. Питання вирішено. Дякую!

З повагою,
{sender_name}

-------- Початкове повідомлення --------
{original_message}"""

        msg.attach(MIMEText(reply_body, 'plain', 'utf-8'))

        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmx.com", 587) as server:
            server.starttls(context=ctx)
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"✅ Автоматический ответ отправлен на {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки ответа: {e}")
        return False

def save_responded_email(email_address):
    """Сохраняет адрес электронной почты в файл"""
    try:
        with open('data/responded_emails.txt', 'a', encoding='utf-8') as f:
            f.write(f"{email_address}\n")
        print(f"📝 Адрес {email_address} сохранен в файл")
    except Exception as e:
        print(f"❌ Ошибка сохранения адреса: {e}")

def read_blacklist():
    """Читает список заблокированных email адресов"""
    with open('data/blacklist.txt', 'r', encoding='utf-8') as f:
        return {line.strip().lower() for line in f if line.strip()}

def is_blacklisted(email):
    """Проверяет, находится ли email в блэклисте"""
    return email.lower() in read_blacklist()

def safe_decode(text, encodings=('utf-8', 'cp1251', 'koi8-r', 'iso-8859-1')):
    """Безопасно декодирует текст, пробуя различные кодировки"""
    if isinstance(text, str):
        return text
    
    for encoding in encodings:
        try:
            return text.decode(encoding)
        except UnicodeDecodeError:
            continue
    
    # Если все кодировки не сработали, возвращаем текст с заменой нечитаемых символов
    return text.decode('utf-8', errors='replace')

def read_responded_emails():
    """Читает список уже отвеченных email адресов"""
    try:
        with open('data/responded_emails.txt', 'r', encoding='utf-8') as f:
            return {line.strip().lower() for line in f if line.strip()}
    except FileNotFoundError:
        print("ℹ️ Файл responded_emails.txt не найден. Создаем новый.")
        with open('data/responded_emails.txt', 'w', encoding='utf-8') as f:
            pass
        return set()
    except Exception as e:
        print(f"❌ Ошибка чтения списка отвеченных адресов: {e}")
        return set()

def delete_message(mail, msg_id):
    """Удаляет письмо с указанным ID"""
    try:
        mail.store(msg_id, '+FLAGS', '\\Deleted')
        mail.expunge()
        return True
    except Exception as e:
        print(f"❌ Ошибка удаления письма: {e}")
        return False

def check_and_reply_to_unread(sender):
    """Проверяет и отвечает на непрочитанные письма"""
    try:
        # Подключаемся к IMAP серверу
        mail = imaplib.IMAP4_SSL("imap.gmx.com")
        mail.login(sender['email'], sender['password'])
        mail.select('inbox')

        # Получаем список уже отвеченных адресов
        responded_emails = read_responded_emails()

        # Ищем непрочитанные письма
        status, messages = mail.search(None, 'UNSEEN')
        
        if status != 'OK':
            print(f"❌ Ошибка поиска писем для {sender['email']}")
            return

        # Получаем список ID непрочитанных писем
        unread_messages = messages[0].split()
        
        if not unread_messages:
            print(f"ℹ️ Нет новых писем для {sender['email']}")
            return

        print(f"📧 Найдено {len(unread_messages)} непрочитанных писем для {sender['email']}")

        # Обрабатываем каждое непрочитанное письмо
        for msg_id in unread_messages:
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            if status != 'OK' or not msg_data or not msg_data[0]:
                print(f"⚠️ Не удалось получить данные письма для {msg_id}")
                continue

            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Получаем адрес отправителя
            from_header = email_message.get('From', '')
            if not from_header:
                print(f"⚠️ Письмо {msg_id} не содержит заголовок From")
                continue
                
            from_addr = email.utils.parseaddr(from_header)[1]
            if not from_addr:
                print(f"⚠️ Не удалось извлечь адрес отправителя из {from_header}")
                continue
            
            # Проверяем, не в блэклисте ли отправитель и не отвечали ли мы уже
            if is_blacklisted(from_addr):
                print(f"⛔ Удаляем письмо от {from_addr} (в блэклисте)")
                if delete_message(mail, msg_id):
                    print(f"✅ Письмо от {from_addr} успешно удалено")
                continue
                
            if from_addr.lower() in responded_emails:
                print(f"ℹ️ Пропускаем письмо от {from_addr} (уже отвечали)")
                mail.store(msg_id, '+FLAGS', '\\Seen')
                continue
            
            # Получаем тему и текст оригинального письма
            original_subject = email_message['Subject'] or 'Без теми'
            original_message = ""
            
            # Извлекаем текст письма
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                original_message = safe_decode(payload)
                            break
                        except Exception as e:
                            print(f"⚠️ Ошибка декодирования части письма: {e}")
                            original_message = "Не удалось декодировать текст письма"
            else:
                try:
                    payload = email_message.get_payload(decode=True)
                    if payload:
                        original_message = safe_decode(payload)
                    else:
                        original_message = "Пустое письмо"
                except Exception as e:
                    print(f"⚠️ Ошибка декодирования письма: {e}")
                    original_message = "Не удалось декодировать текст письма"
            
            # Отправляем автоматический ответ
            if send_auto_reply(sender['email'], sender['password'], from_addr, sender['name'], 
                             original_subject, original_message):
                # Отмечаем письмо как прочитанное
                mail.store(msg_id, '+FLAGS', '\\Seen')
                print(f"✅ Письмо от {from_addr} отмечено как прочитанное")
                # Сохраняем адрес в файл только если он не в блэклисте
                if not is_blacklisted(from_addr):
                    save_responded_email(from_addr)

        mail.close()
        mail.logout()

    except Exception as e:
        print(f"❌ Ошибка обработки писем для {sender['email']}: {e}")

def check_all_accounts():
    """Проверяет все аккаунты на наличие непрочитанных писем"""
    print("\n🔄 Начало проверки писем...")
    senders = read_senders()
    
    for sender in senders:
        print(f"\n📧 Проверка аккаунта {sender['email']}")
        check_and_reply_to_unread(sender)
        time.sleep(5)  # Небольшая пауза между аккаунтами

def main():
    print("🚀 Запуск IMAP-слушателя...")
    
    # Запускаем первую проверку сразу
    check_all_accounts()
    
    # Планируем проверку каждые 10 минут
    schedule.every(10).minutes.do(check_all_accounts)
    
    # Бесконечный цикл для выполнения запланированных задач
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main() 