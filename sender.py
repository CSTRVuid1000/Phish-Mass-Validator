# Это не просто отправка электронных писем.
# Это проверка целевой аудитории и взаимодействие с ней.
# Мы находим живые цели. Кто читает и отвечает.
# Отвечаем что ошиблись снимая подозрения.
# Чистим ящики от невалид авто-ответов.

import csv
import time
import json
import re
from datetime import datetime
from functions.send import send_mail

def is_valid_email(email):
    """Проверяет корректность формата email"""
    # Удаляем возможные пробелы
    email = email.strip()
    # Проверяем базовый формат email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def clean_email(email):
    """Очищает email от некорректных символов"""
    # Удаляем пробелы и слеши
    email = email.strip().replace('/', '')
    # Удаляем все символы после последней точки в домене
    parts = email.split('@')
    if len(parts) == 2:
        domain_parts = parts[1].split('.')
        if len(domain_parts) > 1:
            parts[1] = '.'.join(domain_parts[:-1]) + '.' + domain_parts[-1]
        return '@'.join(parts)
    return email

def read_disabled_accounts():
    """Читает список отключенных аккаунтов из файла"""
    try:
        with open('data/disabled_accounts.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_disabled_accounts(disabled_accounts):
    """Сохраняет список отключенных аккаунтов в файл"""
    with open('data/disabled_accounts.json', 'w', encoding='utf-8') as f:
        json.dump(disabled_accounts, f, ensure_ascii=False, indent=2)

def read_senders(max_accounts=None):
    senders = []
    disabled_accounts = read_disabled_accounts()
    disabled_emails = {acc['email'] for acc in disabled_accounts}
    
    with open('data/senders.txt', 'r', encoding='utf-8') as f:
        for line in f:
            email, password, name = line.strip().split(':')
            if email not in disabled_emails:  # Пропускаем отключенные аккаунты
                senders.append({
                    'email': email,
                    'password': password,
                    'name': name,
                    'attempts': 0,
                    'is_active': True
                })
    return senders[:max_accounts] if max_accounts else senders

def read_recipients():
    recipients = []
    invalid_emails = []
    with open('data/mails.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['send'] != '1':  # Проверяем, не было ли уже отправлено
                email = clean_email(row['email'])
                if is_valid_email(email):
                    row['email'] = email
                    recipients.append(row)
                else:
                    invalid_emails.append({
                        'original': row['email'],
                        'cleaned': email,
                        'row': row
                    })
    if invalid_emails:
        print("\nОбнаружены некорректные email адреса:")
        for invalid in invalid_emails:
            print(f"Оригинальный: {invalid['original']}")
            print(f"Очищенный: {invalid['cleaned']}")
            print("---")
    
    return recipients

def update_send_status(email):
    rows = []
    with open('data/mails.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    for row in rows:
        if row['email'] == email:
            row['send'] = '1'
    
    with open('data/mails.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['email', 'subject', 'message', 'send'])
        writer.writeheader()
        writer.writerows(rows)

def print_status(current, total, success, failed):
    print(f"\rОтправка: [{current}/{total}] Успешно: {success} Ошибок: {failed}", end="", flush=True)

def get_next_active_sender(senders, current_index, failed_senders):
    """Получает следующий активный аккаунт, включая резервные"""
    total_senders = len(senders)
    checked = 0
    
    while checked < total_senders:
        current_index = (current_index + 1) % total_senders
        sender = senders[current_index]
        
        if current_index not in failed_senders and sender['is_active']:
            return current_index, sender
            
        checked += 1
    
    return None, None

def disable_account(sender, reason):
    """Отключает аккаунт и сохраняет информацию о нем"""
    disabled_accounts = read_disabled_accounts()
    
    disabled_info = {
        'email': sender['email'],
        'name': sender['name'],
        'disabled_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'reason': reason,
        'attempts': sender['attempts']
    }
    
    disabled_accounts.append(disabled_info)
    save_disabled_accounts(disabled_accounts)
    
    print(f"\nАккаунт {sender['email']} отключен и сохранен в data/disabled_accounts.json")
    print(f"Причина: {reason}")
    print(f"Время отключения: {disabled_info['disabled_at']}")

def main():
    max_accounts = 0
    
    all_senders = read_senders()  # Читаем все аккаунты
    active_senders = all_senders[:max_accounts] if max_accounts else all_senders
    
    # Инициализируем статусы аккаунтов
    for sender in active_senders:
        sender['is_active'] = True
    
    recipients = read_recipients()
    
    if not recipients:
        print("\nНет корректных получателей для отправки!")
        return
    
    current_sender_index = 0
    emails_sent_in_cycle = 0
    failed_senders = set()
    
    total_recipients = len(recipients)
    current_recipient = 0
    success_count = 0
    failed_count = 0
    
    print(f"\nНачинаем отправку {total_recipients} писем используя {len(active_senders)} аккаунтов...")
    
    for recipient in recipients:
        current_recipient += 1
        while True:
            if len(failed_senders) >= len(active_senders):
                print("\nВсе активные SMTP в текущем цикле проблемные. Ожидание 7 минут...")
                time.sleep(420)
                failed_senders.clear()
                emails_sent_in_cycle = 0
                current_sender_index = 0
                
                # Проверяем наличие резервных аккаунтов
                if len(active_senders) < len(all_senders):
                    print("\nАктивируем резервные аккаунты...")
                    next_reserve = len(active_senders)
                    while next_reserve < len(all_senders) and len(active_senders) < max_accounts:
                        all_senders[next_reserve]['is_active'] = True
                        active_senders.append(all_senders[next_reserve])
                        next_reserve += 1
                    print(f"Активировано {len(active_senders)} аккаунтов")
            
            # Получаем следующий активный аккаунт
            next_index, sender = get_next_active_sender(active_senders, current_sender_index, failed_senders)
            if next_index is None:
                print("\nНет доступных аккаунтов. Ожидание 7 минут...")
                time.sleep(420)
                continue
                
            current_sender_index = next_index
            message = recipient['message'].replace('{rep_name}', sender['name'])
            
            try:
                result = send_mail(
                    sender['email'],
                    sender['password'],
                    recipient['email'],
                    recipient['subject'],
                    message,
                    sender['name'],
                    # use_proxy=True
                )
            except Exception as e:
                print(f"\nОшибка при отправке на {recipient['email']}: {str(e)}")
                result = False
            
            if result:
                update_send_status(recipient['email'])
                emails_sent_in_cycle += 1
                success_count += 1
                sender['attempts'] = 0  # Сбрасываем счетчик попыток при успехе
                print_status(current_recipient, total_recipients, success_count, failed_count)
                
                if emails_sent_in_cycle >= len(active_senders):
                    print("\nЦикл завершен. Ожидание 7 минут...")
                    time.sleep(420)
                    emails_sent_in_cycle = 0
                    failed_senders.clear()
                
                break
            else:
                sender['attempts'] += 1
                if sender['attempts'] >= 3:  # Если достигнуто 3 попытки
                    failed_senders.add(current_sender_index)
                    sender['is_active'] = False
                    disable_account(sender, "3 неудачные попытки отправки")
                    
                    # Если есть резервные аккаунты, активируем следующий
                    if len(active_senders) < len(all_senders):
                        next_reserve = len(active_senders)
                        if next_reserve < len(all_senders):
                            all_senders[next_reserve]['is_active'] = True
                            active_senders.append(all_senders[next_reserve])
                            print(f"Активирован резервный аккаунт: {all_senders[next_reserve]['email']}")
                
                failed_count += 1
                print_status(current_recipient, total_recipients, success_count, failed_count)
                time.sleep(60)
    
    print("\n\nОтправка завершена!")

if __name__ == "__main__":
    main() 