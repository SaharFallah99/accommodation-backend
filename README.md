# سامانه رزرو اقامتگاه آنلاین

این پروژه یک اپلیکیشن Full Stack برای سامانه رزرو اقامتگاه‌های ایرانی است که شامل بک‌اند FastAPI و بخش فرانت‌اند برای تعامل کاربر با سایت می‌شود.

## نمای کلی پروژه
- رزرو اقامتگاه‌های ایرانی با جست‌وجو، فیلتر، بررسی و رزرو
- احراز هویت با JWT
- نقش‌های `user` و `admin`
- مدیریت اقامتگاه‌ها، دسته‌بندی‌ها، امکانات، شهر/استان و قیمت
- سیستم نظرات و بررسی‌های کاربران
- اتصال بین فرانت‌اند و بک‌اند با CORS
- داده‌های نمونه ایرانی ساختگی برای توسعه و تست

## معماری پروژه
- `app/` — کد بک‌اند FastAPI
  - `app/main.py` — routerها و endpointها
  - `app/models.py` — مدل‌های SQLAlchemy
  - `app/schemas.py` — schemaهای Pydantic
  - `app/auth.py` — توکن و احراز هویت
  - `app/database.py` — اتصال دیتابیس
  - `app/config.py` — تنظیمات پروژه
  - `app/seed.py` — تولید داده‌های نمونه
- `data/` — داده‌های نمونه، JSONهای اقامتگاه و کاتالوگ‌های آماده
- `scripts/` — اسکریپت‌های جمع‌آوری داده و ابزارهای بررسی/پروب
- `docker-compose.yml` — سرویس PostgreSQL
- `requirements.txt` — وابستگی‌های Python
- فرانت‌اند — به‌صورت جداگانه یا در کنار پروژه اصلی اضافه شده و با API بک‌اند ارتباط می‌گیرد

## تکنولوژی‌های استفاده‌شده
- FastAPI
- SQLAlchemy / Async SQLAlchemy
- PostgreSQL
- Pydantic
- JWT
- CORS برای اتصال frontend/backend
- Docker Compose

## تنظیمات محیطی
یک فایل `.env` در ریشه پروژه بسازید. نمونه‌ای از مقادیر لازم در `.env.example` موجود است:

```env
APP_NAME="سامانه رزرو اقامتگاه"
APP_ENV=development
SECRET_KEY="change-me-in-production"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

POSTGRES_DB=accommodation_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

## راه‌اندازی سریع
### 1) اجرای دیتابیس
```bash
docker compose up -d
```

### 2) نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### 3) اجرای بک‌اند
```bash
uvicorn app.main:app --reload
```

پس از اجرا، API اصلی در آدرس زیر در دسترس است:
- Backend: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health: `http://localhost:8000/health`

### 4) اجرای فرانت‌اند
اگر فرانت‌اند به‌صورت پروژه جداگانه اضافه شده است، آن را به‌صورت مجزا اجرا کنید و روی یک پورت مثل `3000` یا `5173` راه‌اندازی نمایید. سپس در تنظیمات خود، آدرس API بک‌اند را به صورت زیر تنظیم کنید:

```text
http://localhost:8000
```

در صورت استفاده از CORS، بک‌اند برای ارتباط با فرانت‌اند آماده است و به‌صورت wildcard اجازه دسترسی می‌دهد.

## APIهای اصلی
### احراز هویت
- `POST /auth/register`
- `POST /auth/login`
- `GET /me`

### دسته‌بندی‌ها و امکانات
- `GET /categories`
- `POST /categories`
- `GET /amenities`

### اقامتگاه‌ها
- `GET /accommodations`
- `GET /accommodations/{id}`
- `POST /accommodations`

### دسترسی و رزرو
- `POST /accommodations/{id}/availability`
- `POST /bookings`
- `GET /bookings`

### بررسی‌ها و امتیازدهی
- `POST /accommodations/{id}/reviews`
- `GET /reviews/{id}`

## داده‌های نمونه
داده‌های نمونه در `data/` قرار دارند و برای توسعه و تست پروژه طراحی شده‌اند. این داده‌ها شامل اطلاعات اقامتگاه‌ها، شهرها، استان‌ها و قیمت‌های نمونه هستند.

## نکات مهم
- فایل‌های JSON در `data/` برای نمونه‌سازی و تخمین داده‌های UI استفاده می‌شوند.
- دیتابیس اصلی با PostgreSQL راه‌اندازی می‌شود.
- برای استفاده در محیط Production، مقادیر `.env` را به‌صورت امن تغییر دهید.
- فرانت‌اند و بک‌اند باید روی پورت‌های جداگانه اجرا شوند، اما به یکدیگر از طریق API متصل می‌شوند.

## پروژه‌های مشابه و مسیر توسعه
در نسخه فعلی، پروژه به‌صورت یک پروژه full-stack طراحی شده و آماده توسعه بیشتر است؛ از جمله:
- داشبورد ادمین
- فیلترهای پیشرفته جست‌وجو
- صفحه جزئیات اقامتگاه
- مدیریت رزروها و پرداخت
- سیستم بررسی و امتیازدهی کامل
- بهینه‌سازی UI/UX برای موبایل و دس‌کتاپ

## توسعه و مشارکت
برای اجرای پروژه در محیط محلی، ابتدا دیتابیس و سپس سرور بک‌اند را اجرا کنید. اگر فرانت‌اند هم در کنار آن پیاده‌سازی شده باشد، به‌صورت جداگانه اجرا شود و به API اصلی متصل گردد.
