import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, BigInteger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from bot.config import DATABASE_URL

Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    full_name = Column(String(200))
    is_active = Column(Boolean, default=True)
    subscription_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    properties = relationship("Property", back_populates="owner", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")


class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    address = Column(Text)
    rent_amount = Column(Float, default=0.0)
    payment_day = Column(Integer, default=1)  # Day of month
    tenant_name = Column(String(200))
    tenant_phone = Column(String(50))
    tenant_tg = Column(String(100))
    deposit = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    owner = relationship("User", back_populates="properties")
    payments = relationship("RentPayment", back_populates="property", cascade="all, delete-orphan")
    photos = relationship("PropertyPhoto", back_populates="property", cascade="all, delete-orphan")


class RentPayment(Base):
    __tablename__ = "rent_payments"
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_type = Column(String(50), default="rent")  # rent, utilities, deposit
    status = Column(String(50), default="pending")  # pending, paid, overdue
    due_date = Column(DateTime, nullable=False)
    paid_date = Column(DateTime, nullable=True)
    comment = Column(Text)
    property = relationship("Property", back_populates="payments")


class PropertyPhoto(Base):
    __tablename__ = "property_photos"
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    file_id = Column(String(500), nullable=False)
    photo_type = Column(String(50), default="checkin")  # checkin, checkout, general
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    property = relationship("Property", back_populates="photos")


class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending")  # pending, succeeded, canceled
    provider_payment_id = Column(String(200))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="payments")


class ReminderLog(Base):
    __tablename__ = "reminder_logs"
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    reminder_type = Column(String(50), nullable=False)  # before_1day, on_day, overdue
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        return session