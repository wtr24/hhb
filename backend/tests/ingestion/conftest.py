import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_redis():
    """Mock Redis client for unit tests — avoids real Redis connection."""
    client = MagicMock()
    client.get = MagicMock(return_value=None)
    client.set = MagicMock(return_value=True)
    client.delete = MagicMock(return_value=1)
    client.exists = MagicMock(return_value=0)
    return client


@pytest.fixture
def mock_async_session():
    """Mock SQLAlchemy AsyncSession for unit tests — avoids real DB connection."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session
