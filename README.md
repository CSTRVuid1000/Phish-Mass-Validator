# Phish Mass Validator - Структура файлов данных

## Описание проекта
Проект Email Validator предназначен для валидации email-адресов и отправки писем. В папке `data/`(создать в корне) хранятся все необходимые данные для работы системы.

## Структура файлов в папке `data/`

### 1. `blacklist.txt`
**Назначение:** Список заблокированных email-адресов и доменов  
**Формат:** Текстовый файл, одна запись на строку  
**Содержимое:** Email-адреса, которые не должны получать письма  
**Пример:**
```
Mailer-Daemon@google.com
mailer-daemon@google.com
noreply@google.com
mailer-daemon@google.com
security-noreply@linkedin.com
```

### 2. `disabled_accounts.json`
**Назначение:** Список отключенных аккаунтов  
**Формат:** JSON массив  
**Содержимое:** Пустой массив (в данный момент нет отключенных аккаунтов)  
**Пример:**
```json
[]
```

### 3. `mails.csv`
**Назначение:** Основная база данных email-адресов для отправки писем  
**Формат:** CSV файл с разделителем запятая  
**Структура колонок:**
- `email` - Email-адрес получателя
- `subject` - Тема письма
- `message` - Содержимое письма
- `send` - Флаг отправки (пусто - отправить, 1 - не отправлять/отправлено)

**Пример записи:**
```csv
email,subject,message,send
ppnavaro2020@ukr.net,"john Валерійович, Кадрове супроводження","Вітаємо! {rep_name} з Здорівська Гімназія Васильківської Міської Ради Київської Області звертається до вас. Чи маємо честь спілкуватися з Фабріка? Не вдалося до вас додзвонитися за +38 073 0930162, тут у 101Систем, шановний директоре, невиконані зобов'язання з Москаленка 10, ви на зв'язку?",
```

### 4. `responded_emails.txt`
**Назначение:** Список email-адресов, которые ответили на письма  
**Формат:** Текстовый файл, одна запись на строку  
**Содержимое:** Email-адреса, которые уже ответили  
**Пример:**
```
mail123@gmail.com
mailsgg@gmail.com
maildfas@gmx.pl
mail213@gmail.com
mail5342@gmail.com
```

### 5. `senders.txt`
**Назначение:** Список отправителей с их учетными данными  
**Формат:** Текстовый файл, одна запись на строку  
**Структура записи:** `email:password:name`  
**Содержимое:** Данные для входа в почтовые аккаунты отправителей  
**Пример:**
```
mail1@gmail.com:o2UOF329o9:Роман Шиян
mail2@gmail.com:oK4c2Dq55qh:Антон Beliy
mail3@gmail.com:DKq5e3s56mBU:Frank Banano
mail4@gmail.com:X3LbHLssRtv9:Валентин Назаренко
mail5@gmail.com:Qa2au5wswf:john Bobrov
```

## Воспроизведение структуры файлов

### Для создания пустых файлов:

1. **blacklist.txt** - создать текстовый файл с заблокированными адресами
2. **disabled_accounts.json** - создать JSON файл с пустым массивом `[]`
3. **mails.csv** - создать CSV файл с заголовками: `email,subject,message,send`
4. **responded_emails.txt** - создать пустой текстовый файл
5. **senders.txt** - создать текстовый файл с данными отправителей в формате `email:password:name`

### Команды для создания файлов:

```bash
# Создание папки data
mkdir -p data

# Создание blacklist.txt
touch data/blacklist.txt

# Создание disabled_accounts.json
echo "[]" > data/disabled_accounts.json

# Создание mails.csv с заголовками
echo "email,subject,message,send" > data/mails.csv

# Создание responded_emails.txt
touch data/responded_emails.txt

# Создание senders.txt
touch data/senders.txt
```
