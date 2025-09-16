import certifi
from pymongo import MongoClient

# Replace the following with your actual MongoDB connection string
MONGO_CONNECTION_STRING = (
    "mongodb+srv://workerllyapp:fGbE276ePop1iapV@backendking.y6lcith.mongodb.net/"
)

# Create PyMongo client
client = MongoClient(MONGO_CONNECTION_STRING, tlsCAFile=certifi.where())
db = client.workerlly  # Use the actual database name


# Function to extract unique states from the cities collection
def extract_unique_states():
    unique_states = db.cities.distinct("state")
    print(f"Extracted unique states: {unique_states}")
    return unique_states


# Function to create the states collection and insert unique states
def create_states_collection(unique_states):
    states = [{"name": state} for state in unique_states]
    result = db.states.insert_many(states)
    print(f"Inserted states with IDs: {result.inserted_ids}")
    return result.inserted_ids


# Function to update the cities collection with state_id references
def update_cities_with_state_id():
    # Get all states from the states collection
    states = db.states.find()
    state_map = {state["name"]: state["_id"] for state in states}

    # Update cities with the corresponding state_id
    for state_name, state_id in state_map.items():
        result = db.cities.update_many(
            {"state": state_name}, {"$set": {"state_id": state_id}}
        )
        print(
            f"Updated {result.modified_count} cities with state_id for state: {state_name}"
        )

    # Optionally remove the old state field if no longer needed
    db.cities.update_many({}, {"$unset": {"state": ""}})
    print("Removed 'state' field from all cities.")


# Main function to execute the migration
def migrate_states_and_cities():
    print("Starting migration...")

    # Step 1: Extract unique states
    unique_states = extract_unique_states()

    # Step 2: Create states collection and insert unique states
    create_states_collection(unique_states)

    # Step 3: Update cities with state_id references
    update_cities_with_state_id()

    print("Migration completed.")


# Run the migration
if __name__ == "__main__":
    migrate_states_and_cities()
