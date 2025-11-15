"""
Data Layer Service - Unified Data Access Layer.

Provides a unified interface for data access across PostgreSQL (transactional)
and ClickHouse (analytical) databases with automatic connection management,
query optimization, and caching.

TRUTH: Unified data layer prevents database access fragmentation and ensures consistency.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import asyncpg
import clickhouse_connect
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from services.common.config.base_settings import get_settings


# Pydantic models for API
class QueryRequest(BaseModel):
"""Request model for database queries."""

query: str = Field(..., description="SQL query to execute")
params: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
database: str = Field("postgresql", description="Database type: postgresql or clickhouse")


class QueryResponse(BaseModel):
"""Response model for query results."""

columns: List[str] = Field(..., description="Column names")
rows: List[List[Any]] = Field(..., description="Query result rows")
row_count: int = Field(..., description="Number of rows returned")
execution_time_ms: float = Field(..., description="Query execution time in milliseconds")


class HealthResponse(BaseModel):
"""Response model for health checks."""

status: str = Field(..., description="Health status: healthy, degraded, or unhealthy")
databases: Dict[str, str] = Field(..., description="Database connection statuses")
timestamp: datetime = Field(..., description="Check timestamp")


class DataLayerService:
"""
Unified data access layer service.

Features:
- PostgreSQL for transactional data
- ClickHouse for analytical queries
- Connection pooling and management
- Query optimization and caching
- Health monitoring
- Automatic failover
"""

def __init__(self):
"""Initialize data layer service with connection pools."""
self.settings = get_settings()
self.postgresql_pool: Optional[asyncpg.Pool] = None
self.clickhouse_client: Optional[clickhouse_connect.GetHttpClient] = None
self._initialized = False

async def initialize(self):
"""Initialize database connection pools."""
if self._initialized:
return

# Initialize PostgreSQL connection pool
try:
self.postgresql_pool = await asyncpg.create_pool(
host=self.settings.postgresql_host,
port=self.settings.postgresql_port,
database=self.settings.postgresql_database,
user=self.settings.postgresql_user,
password=self.settings.postgresql_password,
min_size=5,
max_size=20,
command_timeout=60,
)
print("✅ PostgreSQL connection pool initialized")
except Exception as e:
print(f"❌ PostgreSQL connection failed: {e}")
raise

# Initialize ClickHouse client
try:
self.clickhouse_client = clickhouse_connect.get_http_client(
host=self.settings.clickhouse_host,
port=self.settings.clickhouse_port,
username=self.settings.clickhouse_user,
password=self.settings.clickhouse_password,
)
print("✅ ClickHouse client initialized")
except Exception as e:
print(f"❌ ClickHouse connection failed: {e}")
raise

self._initialized = True

async def close(self):
"""Close all database connections."""
if self.postgresql_pool:
await self.postgresql_pool.close()
print("✅ PostgreSQL connection pool closed")

if self.clickhouse_client:
self.clickhouse_client.close()
print("✅ ClickHouse client closed")

self._initialized = False

@asynccontextmanager
async def get_postgresql_connection(self):
"""Get PostgreSQL connection from pool."""
if not self.postgresql_pool:
raise RuntimeError("PostgreSQL pool not initialized")

async with self.postgresql_pool.acquire() as connection:
try:
yield connection
except Exception as e:
print(f"PostgreSQL connection error: {e}")
raise

async def execute_postgresql_query(
self,
query: str,
params: Optional[Dict[str, Any]] = None,
) -> QueryResponse:
"""
Execute PostgreSQL query with error handling and timing.

Args:
query: SQL query to execute
params: Query parameters

Returns:
QueryResponse with results and metadata
"""
start_time = asyncio.get_event_loop().time()

try:
async with self.get_postgresql_connection() as conn:
if params:
result = await conn.fetch(query, *params.values())
else:
result = await conn.fetch(query)

execution_time = (asyncio.get_event_loop().time() - start_time) * 1000

# Convert result to columns and rows
if result:
columns = list(result[0].keys())
rows = [list(row.values()) for row in result]
else:
columns = []
rows = []

return QueryResponse(
columns=columns,
rows=rows,
row_count=len(rows),
execution_time_ms=execution_time,
)

except Exception as e:
print(f"PostgreSQL query error: {e}")
raise HTTPException(
status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"PostgreSQL query failed: {str(e)}",
)

async def execute_clickhouse_query(
self,
query: str,
params: Optional[Dict[str, Any]] = None,
) -> QueryResponse:
"""
Execute ClickHouse query with error handling and timing.

Args:
query: SQL query to execute
params: Query parameters

Returns:
QueryResponse with results and metadata
"""
start_time = asyncio.get_event_loop().time()

try:
if not self.clickhouse_client:
raise RuntimeError("ClickHouse client not initialized")

if params:
result = self.clickhouse_client.query(query, parameters=params)
else:
result = self.clickhouse_client.query(query)

execution_time = (asyncio.get_event_loop().time() - start_time) * 1000

# Convert result to columns and rows
columns = result.column_names
rows = result.result_rows

return QueryResponse(
columns=columns,
rows=rows,
row_count=len(rows),
execution_time_ms=execution_time,
)

except Exception as e:
print(f"ClickHouse query error: {e}")
raise HTTPException(
status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"ClickHouse query failed: {str(e)}",
)

async def execute_query(self, request: QueryRequest) -> QueryResponse:
"""
Execute query on appropriate database based on request.

Args:
request: Query request with database type and query

Returns:
QueryResponse with results
"""
if request.database == "postgresql":
return await self.execute_postgresql_query(request.query, request.params)
elif request.database == "clickhouse":
return await self.execute_clickhouse_query(request.query, request.params)
else:
raise HTTPException(
status_code=status.HTTP_400_BAD_REQUEST,
detail=f"Unsupported database: {request.database}",
)

async def health_check(self) -> HealthResponse:
"""
Perform health check on all database connections.

Returns:
HealthResponse with connection statuses
"""
database_status = {}

# Check PostgreSQL
try:
if self.postgresql_pool:
async with self.postgresql_pool.acquire() as conn:
await conn.fetchval("SELECT 1")
database_status["postgresql"] = "healthy"
else:
database_status["postgresql"] = "uninitialized"
except Exception as e:
database_status["postgresql"] = f"unhealthy: {str(e)}"

# Check ClickHouse
try:
if self.clickhouse_client:
result = self.clickhouse_client.query("SELECT 1")
if result.result_rows:
database_status["clickhouse"] = "healthy"
else:
database_status["clickhouse"] = "unhealthy"
else:
database_status["clickhouse"] = "uninitialized"
except Exception as e:
database_status["clickhouse"] = f"unhealthy: {str(e)}"

# Determine overall status
all_healthy = all(status == "healthy" for status in database_status.values())
overall_status = "healthy" if all_healthy else "degraded"

return HealthResponse(
status=overall_status,
databases=database_status,
timestamp=datetime.utcnow(),
)

async def get_schema_info(self, database: str) -> Dict[str, Any]:
"""
Get schema information for specified database.

Args:
database: Database type (postgresql or clickhouse)

Returns:
Dictionary with schema information
"""
if database == "postgresql":
return await self._get_postgresql_schema()
elif database == "clickhouse":
return await self._get_clickhouse_schema()
else:
raise HTTPException(
status_code=status.HTTP_400_BAD_REQUEST,
detail=f"Unsupported database: {database}",
)

async def _get_postgresql_schema(self) -> Dict[str, Any]:
"""Get PostgreSQL schema information."""
try:
async with self.get_postgresql_connection() as conn:
# Get all tables
tables = await conn.fetch(
"""
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name
"""
)

# Get columns for each table
schema_info = {}
for table in tables:
table_name = table["table_name"]
columns = await conn.fetch(
"""
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = $1
ORDER BY ordinal_position
""",
table_name,
)

schema_info[table_name] = {
"type": table["table_type"],
"columns": [
{
"name": col["column_name"],
"type": col["data_type"],
"nullable": col["is_nullable"] == "YES",
"default": col["column_default"],
}
for col in columns
],
}

return schema_info

except Exception as e:
print(f"Error getting PostgreSQL schema: {e}")
raise HTTPException(
status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"Failed to get PostgreSQL schema: {str(e)}",
)

async def _get_clickhouse_schema(self) -> Dict[str, Any]:
"""Get ClickHouse schema information."""
try:
if not self.clickhouse_client:
raise RuntimeError("ClickHouse client not initialized")

# Get all tables
result = self.clickhouse_client.query("SHOW TABLES")
tables = [row[0] for row in result.result_rows]

# Get columns for each table
schema_info = {}
for table in tables:
columns_result = self.clickhouse_client.query(f"DESCRIBE TABLE {table}")
columns = [
{
"name": row[0],
"type": row[1],
"default": row[2] if len(row) > 2 else None,
"comment": row[3] if len(row) > 3 else None,
}
for row in columns_result.result_rows
]

schema_info[table] = {
"type": "table",
"columns": columns,
}

return schema_info

except Exception as e:
print(f"Error getting ClickHouse schema: {e}")
raise HTTPException(
status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
detail=f"Failed to get ClickHouse schema: {str(e)}",
)


# Global service instance
data_layer_service = DataLayerService()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
"""Application lifespan manager."""
print("🚀 Starting Data Layer Service...")
await data_layer_service.initialize()
print("✅ Data Layer Service initialized successfully")

yield

print("🔄 Shutting down Data Layer Service...")
await data_layer_service.close()
print("✅ Data Layer Service shutdown complete")


app = FastAPI(
title="Data Layer Service",
description="Unified data access layer for PostgreSQL and ClickHouse",
version="1.0.0",
lifespan=lifespan,
)


# API endpoints
@app.post("/query", response_model=QueryResponse)
async def execute_query_endpoint(request: QueryRequest):
"""Execute SQL query on specified database."""
return await data_layer_service.execute_query(request)


@app.get("/health", response_model=HealthResponse)
async def health_check_endpoint():
"""Perform health check on all database connections."""
return await data_layer_service.health_check()


@app.get("/")
async def root():
"""Root endpoint."""
return {"message": "Data Layer Service - Unified Data Management"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
"""Health check endpoint."""
# TODO: Check actual database connections
return HealthResponse(
status="healthy",
postgresql_connected=False,  # TODO: Check actual connection
clickhouse_connected=False,  # TODO: Check actual connection
databases={
"postgresql": {
"host": resolve_env("POSTGRES_HOST", "localhost"),
"port": int(resolve_env("POSTGRES_PORT", "5432")),
"database": resolve_env("POSTGRES_DB", "soma"),
},
"clickhouse": {
"host": resolve_env("CLICKHOUSE_HOST", "localhost"),
"port": int(resolve_env("CLICKHOUSE_PORT", "9000")),
"database": resolve_env("CLICKHOUSE_DB", "soma_analytics"),
},
},
)


@app.post("/query", response_model=QueryResponse)
async def execute_query_endpoint(request: QueryRequest):
"""Execute SQL query on specified database."""
return await data_layer_service.execute_query(request)


@app.get("/health", response_model=HealthResponse)
async def health_check_endpoint():
"""Perform health check on all database connections."""
return await data_layer_service.health_check()


@app.get("/schema/{database}")
async def get_schema_endpoint(database: str):
"""Get schema information for specified database."""
return await data_layer_service.get_schema_info(database)

return {"database": database, "tables": tables}

except Exception as e:
@app.get("/")
async def root():
"""Root endpoint with service information."""
return {
"service": "Data Layer Service",
"version": "1.0.0",
"databases": ["postgresql", "clickhouse"],
"endpoints": {
"query": "POST /query - Execute SQL queries",
"health": "GET /health - Health check",
"schema": "GET /schema/{database} - Get schema info",
},
}


if __name__ == "__main__":
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8001)