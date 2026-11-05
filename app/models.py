from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, Enum):
    user = "user"
    admin = "admin"


class BookingStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


accommodation_amenities = Table(
    "accommodation_amenities",
    Base.metadata,
    Column("accommodation_id", ForeignKey("accommodations.id"), primary_key=True),
    Column("amenity_id", ForeignKey("amenities.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, native_enum=False), default=UserRole.user, nullable=False)
    national_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user")
    accommodations: Mapped[list["Accommodation"]] = relationship(back_populates="creator")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)

    parent: Mapped["Category | None"] = relationship(remote_side="Category.id", backref="children")
    accommodations: Mapped[list["Accommodation"]] = relationship(back_populates="category")


class Amenity(Base):
    __tablename__ = "amenities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)

    accommodations: Mapped[list["Accommodation"]] = relationship(back_populates="amenities", secondary=accommodation_amenities)


class Accommodation(Base):
    __tablename__ = "accommodations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(12, 0), nullable=False, default=0)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    beds: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    bathrooms: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    check_in_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(14, 0))
    check_out_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(12, 0))
    min_nights: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_nights: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    avg_rating: Mapped[Decimal | None] = mapped_column(Numeric(2, 1), nullable=True)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    category: Mapped[Category | None] = relationship(back_populates="accommodations")
    creator: Mapped[User | None] = relationship(back_populates="accommodations")
    location: Mapped["Location | None"] = relationship(back_populates="accommodation", uselist=False)
    images: Mapped[list["AccommodationImage"]] = relationship(back_populates="accommodation")
    amenities: Mapped[list[Amenity]] = relationship(back_populates="accommodations", secondary=accommodation_amenities)
    bookings: Mapped[list["Booking"]] = relationship(back_populates="accommodation")
    reviews: Mapped[list["Review"]] = relationship(back_populates="accommodation")
    availability: Mapped[list["Availability"]] = relationship(back_populates="accommodation")


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    accommodation_id: Mapped[int] = mapped_column(ForeignKey("accommodations.id"), unique=True, nullable=False)
    province: Mapped[str] = mapped_column(String(80), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    accommodation: Mapped[Accommodation] = relationship(back_populates="location")


class AccommodationImage(Base):
    __tablename__ = "accommodation_images"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    accommodation_id: Mapped[int] = mapped_column(ForeignKey("accommodations.id"), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    is_cover: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    accommodation: Mapped[Accommodation] = relationship(back_populates="images")


class Availability(Base):
    __tablename__ = "availability"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    accommodation_id: Mapped[int] = mapped_column(ForeignKey("accommodations.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    price_override: Mapped[Decimal | None] = mapped_column(Numeric(12, 0), nullable=True)

    accommodation: Mapped[Accommodation] = relationship(back_populates="availability")

    __table_args__ = (UniqueConstraint("accommodation_id", "date", name="uq_accommodation_date"),)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    accommodation_id: Mapped[int] = mapped_column(ForeignKey("accommodations.id"), nullable=False)
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)
    guests_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 0), nullable=False, default=0)
    status: Mapped[BookingStatus] = mapped_column(SAEnum(BookingStatus, native_enum=False), default=BookingStatus.pending, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="bookings")
    accommodation: Mapped[Accommodation] = relationship(back_populates="bookings")
    reviews: Mapped[list["Review"]] = relationship(back_populates="booking")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    accommodation_id: Mapped[int] = mapped_column(ForeignKey("accommodations.id"), nullable=False)
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"), unique=True, nullable=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped[User] = relationship(back_populates="reviews")
    accommodation: Mapped[Accommodation] = relationship(back_populates="reviews")
    booking: Mapped[Booking | None] = relationship(back_populates="reviews")

    __table_args__ = (UniqueConstraint("booking_id", name="uq_review_booking"),)
