# Reminder
Файл .env содержит:
# APP name
APP_NAME=Reminder
# Telegram
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# JWT Secret (сгенерируй сам: openssl rand -hex 32)
SECRET_KEY=000d00efb0fb00fba000ceb000d0b0f00f000006abc111f222222f3af3f33af3
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASS=postgres
DB_NAME=reminder_db