from aiohttp import TCPConnector, ClientTimeout, ClientSession
from contextlib import asynccontextmanager
from config.settings import API_TIMEOUT

# Constants
MAX_CONNECTIONS = 100

@asynccontextmanager
async def get_session():
    """Get a session from the connection pool with retry and timeout settings."""
    connector = TCPConnector(limit=MAX_CONNECTIONS, ttl_dns_cache=300)
    timeout = ClientTimeout(total=API_TIMEOUT, connect=10)
    async with ClientSession(connector=connector, timeout=timeout) as session:
        yield session
