from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class LocalityPrice(Base):
    __tablename__ = "locality_prices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    avg_price_per_sqft = Column(Float)
    min_price_per_sqft = Column(Float)
    max_price_per_sqft = Column(Float)
    avg_price_2bhk_lakhs = Column(Float)
    avg_price_3bhk_lakhs = Column(Float)
    yoy_change_pct = Column(Float, default=0.0)
    demand_level = Column(String, default="Medium")
    listing_count = Column(Integer, default=0)
    scraped_at = Column(DateTime, default=datetime.utcnow)


class PropertyListing(Base):
    __tablename__ = "property_listings"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    title = Column(String)
    locality = Column(String, index=True)
    sub_locality = Column(String, nullable=True)
    price_lakhs = Column(Float)
    area_sqft = Column(Float)
    price_per_sqft = Column(Float)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    property_type = Column(String)  # Apartment, Villa, Plot, Independent House
    furnishing = Column(String, nullable=True)  # Furnished, Semi-Furnished, Unfurnished
    source = Column(String)  # MagicBricks, 99acres, Housing.com, NoBroker, SquareYards
    source_url = Column(String, nullable=True)
    is_new_launch = Column(Boolean, default=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)


class PriceTrend(Base):
    __tablename__ = "price_trends"

    id = Column(Integer, primary_key=True, index=True)
    locality = Column(String, index=True)
    month = Column(String)  # YYYY-MM
    avg_price_per_sqft = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)


class MarketInsight(Base):
    __tablename__ = "market_insights"

    id = Column(Integer, primary_key=True, index=True)
    insight_text = Column(Text)
    market_summary = Column(Text)
    avg_price_per_sqft = Column(Float)
    total_listings = Column(Integer)
    hottest_locality = Column(String)
    yoy_change_pct = Column(Float)
    generated_at = Column(DateTime, default=datetime.utcnow)


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String)
    status = Column(String)  # success, failed, partial
    listings_scraped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    run_at = Column(DateTime, default=datetime.utcnow)
