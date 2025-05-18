from app.db.base import Base, engine
import app.models  # Import all models so they are registered with SQLAlchemy

def init_db():
    """Initialize the database by creating all tables"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully") 