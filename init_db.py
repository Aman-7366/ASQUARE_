"""Initialize the local database and load the sample catalogue."""
from database import init_db
from seed import seed

if __name__ == "__main__":
    init_db()
    seed()
    print("A SQUARE database initialized and sample catalogue loaded.")
