# سامانه رزرو اقامتگاه آنلاین

این پروژه یک بک‌اند FastAPI برای سامانه رزرو اقامتگاه‌های ایرانی است که بر اساس ERD ارائه‌شده طراحی شده است.

## ویژگی‌ها
- مدل‌های اصلی: `users`, `accommodations`, `categories`, `locations`, `amenities`, `bookings`, `reviews`, `availability`
- احراز هویت با JWT
- نقش‌های `user` و `admin`
- دیتابیس PostgreSQL با SQLAlchemy
- داده‌های نمونه ایرانی ساختگی
- APIهای لازم برای جست‌وجو، رزرو، بررسی، و مدیریت اقامتگاه‌ها

## ساختار پروژه
- `app/config.py` — تنظیمات محیطی
- `app/database.py` — اتصال و ساخته شدن دیتابیس
- `app/models.py` — مدل‌های SQLAlchemy
- `app/schemas.py` — schemaهای Pydantic
- `app/auth.py` — توکن و احراز هویت
- `app/seed.py` — تولید داده‌های نمونه
- `app/main.py` — API endpoints

## راه‌اندازی
1. PostgreSQL را اجرا کنید یا از `docker-compose.yml` استفاده کنید:
   `docker compose up -d`

2. فایل `.env` را از `.env.example` کپی کنید و مقادیر را تنظیم کنید.

3. وابستگی‌ها را نصب کنید:
   `pip install -r requirements.txt`

4. سرویس را اجرا کنید:
   `uvicorn app.main:app --reload`

5. آدرس‌ها:
   - Swagger: `http://localhost:8000/docs`
   - Health: `http://localhost:8000/health`

## APIهای اصلی
- `POST /auth/register`
- `POST /auth/login`
- `GET /me`
- `GET /accommodations`
- `GET /accommodations/{id}`
- `POST /accommodations`
- `POST /accommodations/{id}/availability`
- `POST /bookings`
- `GET /bookings`
- `POST /accommodations/{id}/reviews`
- `GET /reviews/{id}`

## نکته
داده‌های نمونه فقط برای اقامتگاه‌ها و شهرهای ایران هستند و برای استفادهٔ توسعه/تست طراحی شده‌اند.
