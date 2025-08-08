import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.dependencies.database import get_db, Base
from api.main import app
import os


# Create a temporary SQLite database for testing
@pytest.fixture(scope="session")
def test_engine():
    # Use SQLite in-memory database for testing
    engine = create_engine("sqlite:///test.db", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    # Cleanup
    try:
        os.remove("test.db")
    except:
        pass


@pytest.fixture(scope="function")
def test_db(test_engine):
    # Create a fresh database session for each test
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    # Override the get_db dependency
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield session

    # Clean up tables after each test - FIXED VERSION
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())  # Use session.execute instead of engine.execute
    session.commit()
    session.close()


@pytest.fixture
def client(test_db):
    # TestClient with database override
    with TestClient(app) as test_client:
        yield test_client