from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import create_access_token, get_current_user, get_password_hash, verify_password
from app.database import AsyncSessionLocal, init_db
from app.models import Accommodation, Amenity, Availability, Booking, Category, Location, Review, User, UserRole
from app.schemas import (
    AccommodationCreate,
    AccommodationRead,
    AmenityRead,
    AvailabilityCreate,
    AvailabilityRead,
    BookingCreate,
    BookingRead,
    CategoryCreate,
    CategoryRead,
    ReviewCreate,
    ReviewRead,
    TokenResponse,
    UserLogin,
    UserRead,
    UserRegister,
)
from app.seed import seed_data
from app.database import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with AsyncSessionLocal() as session:
        await seed_data(session)
    yield


app = FastAPI(title="سامانه رزرو اقامتگاه", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.scalar(
        select(User).where((User.email == payload.email) | (User.phone == payload.phone))
    )
    if existing:
        raise HTTPException(status_code=400, detail="User with this email or phone already exists")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        password_hash=get_password_hash(payload.password),
        role=UserRole.user,
        national_id=payload.national_id,
        is_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.post("/auth/login", response_model=TokenResponse)
async def login_user(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=user.email)
    return TokenResponse(access_token=token)


@app.get("/me", response_model=UserRead)
async def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/categories", response_model=list[CategoryRead])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.id))
    return result.scalars().all()


@app.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    if admin.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    category = Category(**payload.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@app.get("/amenities", response_model=list[AmenityRead])
async def list_amenities(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Amenity).order_by(Amenity.id))
    return result.scalars().all()


@app.get("/accommodations", response_model=list[AccommodationRead])
async def list_accommodations(
    city: str | None = None,
    province: str | None = None,
    category_id: int | None = None,
    guest_count: int | None = Query(default=None, ge=1),
    db: AsyncSession = Depends(get_db),
):
    query = select(Accommodation).options(
        selectinload(Accommodation.location),
        selectinload(Accommodation.amenities),
        selectinload(Accommodation.images),
    )

    if city or province:
           query = query.join(Location)

           if city:
               query = query.where(Location.city.ilike(f"%{city}%"))

           if province:
              query = query.where(Location.province.ilike(f"%{province}%"))
    if category_id:
        query = query.where(Accommodation.category_id == category_id)
    if guest_count:
        query = query.where(Accommodation.capacity >= guest_count)

    result = await db.execute(query)
    return result.scalars().unique().all()


@app.get("/accommodations/{accommodation_id}", response_model=AccommodationRead)
async def get_accommodation(accommodation_id: int, db: AsyncSession = Depends(get_db)):
    accommodation = await db.get(Accommodation, accommodation_id)
    if accommodation is None:
        raise HTTPException(status_code=404, detail="Accommodation not found")
    return accommodation


@app.post("/accommodations", response_model=AccommodationRead, status_code=status.HTTP_201_CREATED)
async def create_accommodation(
    payload: AccommodationCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    if admin.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    accommodation = Accommodation(
        category_id=payload.category_id,
        created_by=admin.id,
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        price_per_night=payload.price_per_night,
        capacity=payload.capacity,
        bedrooms=payload.bedrooms,
        beds=payload.beds,
        bathrooms=payload.bathrooms,
        check_in_time=payload.check_in_time,
        check_out_time=payload.check_out_time,
        min_nights=payload.min_nights,
        max_nights=payload.max_nights,
        status="active",
    )
    db.add(accommodation)
    await db.flush()

    location = Location(
        accommodation_id=accommodation.id,
        province=payload.province,
        city=payload.city,
        address=payload.address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        postal_code=payload.postal_code,
    )
    db.add(location)

    if payload.amenity_ids:
        amenities = await db.execute(select(Amenity).where(Amenity.id.in_(payload.amenity_ids)))
        accommodation.amenities = list(amenities.scalars().all())

    await db.commit()
    await db.refresh(accommodation)
    return accommodation


@app.post("/accommodations/{accommodation_id}/availability", response_model=AvailabilityRead)
async def upsert_availability(
    accommodation_id: int,
    payload: AvailabilityCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    if admin.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    existing = await db.scalar(
        select(Availability).where(
            Availability.accommodation_id == accommodation_id,
            Availability.date == payload.date,
        )
    )
    if existing:
        existing.is_available = payload.is_available
        existing.price_override = payload.price_override
        await db.commit()
        await db.refresh(existing)
        return existing

    item = Availability(
        accommodation_id=accommodation_id,
        date=payload.date,
        is_available=payload.is_available,
        price_override=payload.price_override,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@app.post("/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accommodation = await db.get(Accommodation, payload.accommodation_id)
    if accommodation is None:
        raise HTTPException(status_code=404, detail="Accommodation not found")

    nights = (payload.check_out_date - payload.check_in_date).days
    if nights <= 0:
        raise HTTPException(status_code=400, detail="Check-out must be after check-in")

    total_price = accommodation.price_per_night * nights
    booking = Booking(
        user_id=current_user.id,
        accommodation_id=accommodation.id,
        check_in_date=payload.check_in_date,
        check_out_date=payload.check_out_date,
        guests_count=payload.guests_count,
        total_price=total_price,
        status="pending",
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@app.get("/bookings", response_model=list[BookingRead])
async def list_bookings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.admin:
        result = await db.execute(select(Booking).order_by(Booking.created_at.desc()))
    else:
        result = await db.execute(
            select(Booking).where(Booking.user_id == current_user.id).order_by(Booking.created_at.desc())
        )
    return result.scalars().all()


@app.post("/accommodations/{accommodation_id}/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    accommodation_id: int,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = await db.scalar(
        select(Booking).where(
            Booking.accommodation_id == accommodation_id,
            Booking.user_id == current_user.id,
            Booking.status == "completed",
        )
    )
    if booking is None:
        raise HTTPException(status_code=400, detail="Only guests with a completed stay can review")

    existing_review = await db.scalar(select(Review).where(Review.booking_id == booking.id))
    if existing_review:
        raise HTTPException(status_code=400, detail="A review for this booking already exists")

    review = Review(
        user_id=current_user.id,
        accommodation_id=accommodation_id,
        booking_id=booking.id,
        rating=payload.rating,
        comment=payload.comment,
        is_approved=True,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@app.get("/reviews/{accommodation_id}", response_model=list[ReviewRead])
async def list_reviews(accommodation_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Review).where(Review.accommodation_id == accommodation_id).order_by(Review.created_at.desc())
    )
    return result.scalars().all()


@app.post("/seed")
async def manual_seed(db: AsyncSession = Depends(get_db)):
    await seed_data(db)
    return {"status": "ok", "message": "Seeded demo data"}
