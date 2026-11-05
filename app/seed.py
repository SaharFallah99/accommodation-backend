from __future__ import annotations

from datetime import date, datetime, timedelta, time
from decimal import Decimal

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_password_hash
from app.models import (
    Accommodation,
    AccommodationImage,
    Amenity,
    Availability,
    Booking,
    BookingStatus,
    Category,
    Location,
    Review,
    User,
    UserRole,
    accommodation_amenities,
)


async def seed_data(db: AsyncSession) -> None:
    if await db.scalar(select(User.id).limit(1)):
        return

    admin = User(
        full_name="مدیر سامانه",
        email="admin@iranstay.ir",
        phone="09120000000",
        password_hash=get_password_hash("admin123"),
        role=UserRole.admin,
        national_id="1111111111",
        is_verified=True,
    )
    db.add(admin)
    await db.flush()

    user1 = User(
        full_name="سارا احمدی",
        email="sara@example.com",
        phone="09121111111",
        password_hash=get_password_hash("pass1234"),
        role=UserRole.user,
        national_id="2222222222",
        is_verified=True,
    )
    user2 = User(
        full_name="علی رضایی",
        email="ali@example.com",
        phone="09122222222",
        password_hash=get_password_hash("pass1234"),
        role=UserRole.user,
        national_id="3333333333",
        is_verified=True,
    )
    db.add_all([user1, user2])
    await db.flush()

    category1 = Category(name="ویلا", slug="villa", icon="home")
    category2 = Category(name="سوئیت", slug="suite", icon="building")
    category3 = Category(name="کلبه", slug="cabin", icon="tree")
    db.add_all([category1, category2, category3])
    await db.flush()

    amenities = [
        Amenity(name="Wi-Fi", icon="wifi"),
        Amenity(name="پارکینگ", icon="car"),
        Amenity(name="استخر", icon="water"),
        Amenity(name="آب گرم", icon="hot"),
        Amenity(name="مبرد", icon="snowflake"),
        Amenity(name="تلویزیون", icon="tv"),
        Amenity(name="صبحانه", icon="coffee"),
        Amenity(name="حیوان خانگی", icon="paw"),
    ]
    db.add_all(amenities)
    await db.flush()

    accommodation1 = Accommodation(
        category_id=category1.id,
        created_by=admin.id,
        title="ویلا جنگلی دوخوابه در کیش",
        slug="villa-jangali-kish",
        description="ویلا با منظره دریا و فضای آرام برای خانواده‌ها و مهمان‌های کوتاه‌مدت",
        price_per_night=Decimal("5600000"),
        capacity=5,
        bedrooms=2,
        beds=3,
        bathrooms=2,
        check_in_time=time.fromisoformat("14:00:00"),
        check_out_time=time.fromisoformat("12:00:00"),
        min_nights=2,
        max_nights=7,
        status="active",
        avg_rating=Decimal("4.8"),
        reviews_count=2,
    )
    accommodation2 = Accommodation(
        category_id=category2.id,
        created_by=admin.id,
        title="سوئیت مدرن در تهران، منطقه پاسداران",
        slug="suite-modern-tehran-pasdaran",
        description="سوئیت لوکس نزدیک مراکز خرید و بیمارستان‌ها برای مسافران کاری و کوتاه‌مدت",
        price_per_night=Decimal("4200000"),
        capacity=3,
        bedrooms=1,
        beds=2,
        bathrooms=1,
        check_in_time=time.fromisoformat("15:00:00"),
        check_out_time=time.fromisoformat("11:00:00"),
        min_nights=1,
        max_nights=10,
        status="active",
        avg_rating=Decimal("4.6"),
        reviews_count=1,
    )
    accommodation3 = Accommodation(
        category_id=category3.id,
        created_by=admin.id,
        title="کلبه روستایی در اطراف شیلاتی ماسال",
        slug="cabin-roostai-masal",
        description="محیط آرام و بکر با حمام گرم و فضای باز مناسب تعطیلات تابستانی",
        price_per_night=Decimal("2900000"),
        capacity=4,
        bedrooms=1,
        beds=2,
        bathrooms=1,
        check_in_time=time.fromisoformat("14:00:00"),
        check_out_time=time.fromisoformat("12:00:00"),
        min_nights=2,
        max_nights=6,
        status="active",
        avg_rating=Decimal("4.4"),
        reviews_count=1,
    )
    db.add_all([accommodation1, accommodation2, accommodation3])
    await db.flush()

    await db.execute(
        insert(accommodation_amenities),
        [
            {"accommodation_id": accommodation1.id, "amenity_id": amenity.id}
            for amenity in amenities[:5]
        ],
    )
    await db.execute(
        insert(accommodation_amenities),
        [
            {"accommodation_id": accommodation2.id, "amenity_id": amenity.id}
            for amenity in [amenities[0], amenities[1], amenities[5], amenities[6]]
        ],
    )
    await db.execute(
        insert(accommodation_amenities),
        [
            {"accommodation_id": accommodation3.id, "amenity_id": amenity.id}
            for amenity in [amenities[0], amenities[2], amenities[3], amenities[7]]
        ],
    )

    location1 = Location(
        accommodation_id=accommodation1.id,
        province="هرمزگان",
        city="کیش",
        address="خیابان ساحلی، مجتمع گل‌ها، پلاک 12",
        latitude=Decimal("26.5320"),
        longitude=Decimal("53.9690"),
        postal_code="79416",
    )
    location2 = Location(
        accommodation_id=accommodation2.id,
        province="تهران",
        city="تهران",
        address="خیابان پاسداران، کوچه دهم، پلاک 56",
        latitude=Decimal("35.7150"),
        longitude=Decimal("51.3900"),
        postal_code="16718",
    )
    location3 = Location(
        accommodation_id=accommodation3.id,
        province="گیلان",
        city="ماسال",
        address="روستای لشکر، کنار جاده جنگل",
        latitude=Decimal("37.4200"),
        longitude=Decimal("49.1800"),
        postal_code="44718",
    )
    db.add_all([location1, location2, location3])

    img1 = AccommodationImage(accommodation_id=accommodation1.id, url="https://images.example.com/kish-1.jpg", is_cover=True, sort_order=1)
    img2 = AccommodationImage(accommodation_id=accommodation1.id, url="https://images.example.com/kish-2.jpg", is_cover=False, sort_order=2)
    img3 = AccommodationImage(accommodation_id=accommodation2.id, url="https://images.example.com/tehran-1.jpg", is_cover=True, sort_order=1)
    img4 = AccommodationImage(accommodation_id=accommodation3.id, url="https://images.example.com/masal-1.jpg", is_cover=True, sort_order=1)
    db.add_all([img1, img2, img3, img4])

    today = date.today()
    for acc in [accommodation1, accommodation2, accommodation3]:
        for offset in range(0, 30):
            d = today + timedelta(days=offset)
            db.add(
                Availability(
                    accommodation_id=acc.id,
                    date=d,
                    is_available=True,
                    price_override=None,
                )
            )

    booking1 = Booking(
        user_id=user1.id,
        accommodation_id=accommodation1.id,
        check_in_date=today + timedelta(days=10),
        check_out_date=today + timedelta(days=14),
        guests_count=2,
        total_price=Decimal("22400000"),
        status=BookingStatus.completed,
    )
    booking2 = Booking(
        user_id=user2.id,
        accommodation_id=accommodation2.id,
        check_in_date=today + timedelta(days=20),
        check_out_date=today + timedelta(days=23),
        guests_count=3,
        total_price=Decimal("12600000"),
        status=BookingStatus.confirmed,
    )
    db.add_all([booking1, booking2])
    await db.flush()

    review1 = Review(
        user_id=user1.id,
        accommodation_id=accommodation1.id,
        booking_id=booking1.id,
        rating=5,
        comment="ویلا بسیار تمیز و آرام بود و موقعیت عالی داشت.",
        is_approved=True,
    )
    review2 = Review(
        user_id=user2.id,
        accommodation_id=accommodation2.id,
        booking_id=booking2.id,
        rating=4,
        comment="سوئیت تمیز و نزدیکی به مراکز خرید خوب بود.",
        is_approved=True,
    )
    db.add_all([review1, review2])
    await db.commit()
