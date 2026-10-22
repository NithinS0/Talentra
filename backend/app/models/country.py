from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Country(Base):
    """Country reference table adhering to ISO 3166-1 and ITU-T E.164 standards."""

    __tablename__ = "country"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    country_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False, index=True)
    alpha3_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=True)
    numeric_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    calling_code: Mapped[str] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

