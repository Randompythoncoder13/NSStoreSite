from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
import datetime

DIALECT = ""
USERNAME = ""
PASSWORD = ""
HOST = ""
PORT = 0000
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


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Integer, nullable=False)
    store_id = Column(Integer, ForeignKey('stores.id'))
    store = relationship("Store", back_populates="products")


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
        print("Tables created successfully on the remote database!")
        print("You can now deploy your Streamlit app.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check the following:")
        print("1. Is the PostgreSQL server running on your hosting machine?")
        print("2. Is port correctly port-forwarded on your router?")
        print("3. Is the firewall on your home machine allowing connections on the port?")
        print("4. Are the username, password, host, and database name correct?")

if __name__ == "__main__":
    setup_remote_db()
