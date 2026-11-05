from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(..., min_length=9, max_length=20)
    password: str = Field(..., min_length=6, max_length=100)
    national_id: str | None = Field(default=None, max_length=20)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    phone: str
    role: str
    avatar_url: str | None = None
    is_verified: bool
    created_at: datetime


class CategoryCreate(BaseModel):
    name: str
    slug: str
    icon: str | None = None
    parent_id: int | None = None


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int | None = None
    name: str
    slug: str
    icon: str | None = None


class AmenityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    icon: str | None = None


class LocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    province: str
    city: str
    address: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    postal_code: str | None = None


class AccommodationImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    is_cover: bool = False
    sort_order: int = 0


class AccommodationCreate(BaseModel):
    category_id: int | None = None
    title: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=220)
    description: str | None = None
    price_per_night: Decimal = Field(..., gt=0)
    capacity: int = Field(..., ge=1)
    bedrooms: int = Field(..., ge=0)
    beds: int = Field(..., ge=0)
    bathrooms: int = Field(..., ge=0)
    check_in_time: time = time(14, 0)
    check_out_time: time = time(12, 0)
    min_nights: int = Field(..., ge=1)
    max_nights: int = Field(..., ge=1)
    province: str = Field(..., min_length=2)
    city: str = Field(..., min_length=2)
    address: str = Field(..., min_length=5)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    postal_code: str | None = None
    amenity_ids: list[int] = []


class AccommodationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int | None = None
    title: str
    slug: str
    description: str | None = None
    price_per_night: Decimal
    capacity: int
    bedrooms: int
    beds: int
    bathrooms: int
    check_in_time: time
    check_out_time: time
    min_nights: int
    max_nights: int
    status: str
    avg_rating: Decimal | None = None
    reviews_count: int
    created_at: datetime
    location: LocationRead | None = None
    amenities: list[AmenityRead] = []
    images: list[AccommodationImageRead] = []


class BookingCreate(BaseModel):
    accommodation_id: int
    check_in_date: date
    check_out_date: date
    guests_count: int = Field(..., ge=1)


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    accommodation_id: int
    user_id: int
    check_in_date: date
    check_out_date: date
    guests_count: int
    total_price: Decimal
    status: str
    created_at: datetime


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    accommodation_id: int
    booking_id: int | None = None
    rating: int
    comment: str | None = None
    created_at: datetime
    is_approved: bool


class AvailabilityCreate(BaseModel):
    date: date
    is_available: bool = True
    price_override: Decimal | None = None


class AvailabilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    accommodation_id: int
    date: date
    is_available: bool
    price_override: Decimal | None = None
