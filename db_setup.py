import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import datetime

# --- Database Connection for Remote PostgreSQL ---
# This is for your one-time local execution.
DIALECT = ""
USERNAME = ""
PASSWORD = ""
HOST = ""
PORT = 1111
DATABASE = ""

DATABASE_URL = f"{DIALECT}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    store = relationship("Store", back_populates="owner", uselist=False)
    orders = relationship("Order", back_populates="buyer")


class Store(Base):
    __tablename__ = 'stores'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    owner = relationship("User", back_populates="store")
    products = relationship("Product", back_populates="store", cascade="all, delete-orphan")
    # NEW RELATIONSHIP: A store can have many categories
    categories = relationship("Category", back_populates="store", cascade="all, delete-orphan")


# NEW MODEL: Category
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    store_id = Column(Integer, ForeignKey('stores.id'))

    # Relationships
    store = relationship("Store", back_populates="categories")
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Integer, nullable=False)
    store_id = Column(Integer, ForeignKey('stores.id'))
    # MODIFIED: Add a foreign key to the Category table. It can be null.
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)

    # Relationships
    store = relationship("Store", back_populates="products")
    category = relationship("Category", back_populates="products")  # NEW


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity_purchased = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    buyer = relationship("User", back_populates="orders")
    product = relationship("Product")


def setup_remote_db():
    print("Connecting to the remote database...")
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        print("Tables created/updated successfully on the remote database!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    setup_remote_db()