import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

# Replace the following with your actual MongoDB connection string
MONGO_CONNECTION_STRING = (
    "mongodb+srv://workerllyapp:fGbE276ePop1iapV@backendking.y6lcith.mongodb.net/"
)
# Create PyMongo client

client = MongoClient(MONGO_CONNECTION_STRING, tlsCAFile=certifi.where())
db = client.workerlly  # Use the actual database name

# Create Motor client
motor_client = AsyncIOMotorClient(MONGO_CONNECTION_STRING, tlsCAFile=certifi.where())
motor_db = motor_client.workerlly

db.categories.create_index("name", unique=True)
db.cities.create_index("name", unique=True)


# Function to get the PyMongo database instance
def get_pymongo_db():
    return db


# Function to get the Motor database instance
async def get_motor_db():
    return motor_db


# Set up indexes for PyMongo
def setup_pymongo_indexes():
    db.users.create_index("mobile", unique=True)
    db.categories.create_index("name", unique=True)
    db.cities.create_index("name", unique=True)


# Set up indexes for Motor
async def setup_motor_indexes():
    await motor_db.users.create_index("mobile", unique=True)
    await motor_db.categories.create_index("name", unique=True)
    await motor_db.cities.create_index("name", unique=True)


# Initialize both PyMongo and Motor databases
def initialize_pymongo():
    setup_pymongo_indexes()
    print("PyMongo indexes have been set up.")


async def initialize_motor():
    await setup_motor_indexes()
    print("Motor indexes have been set up.")


# You should call both initialize functions when your application starts
async def initialize_databases():
    initialize_pymongo()
    await initialize_motor()
    print("Both PyMongo and Motor databases have been initialized.")


# Utility function to switch between PyMongo and Motor
def get_db(use_motor: bool = False):
    return get_motor_db() if use_motor else get_pymongo_db()
