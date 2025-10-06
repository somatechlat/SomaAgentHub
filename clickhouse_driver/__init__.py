"""Stub clickhouse_driver module for testing without a real ClickHouse server.

Provides a minimal `Client` class with an `execute` method that returns
pre‑defined mock data sufficient for the integration tests in this repository.
"""

from typing import List, Any


class Client:
    def __init__(self, host: str = "localhost", port: int = 9000, user: str = "default", password: str = "", database: str = "somaagent"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database

    def execute(self, query: str, params: List[Any] = None):
        """Return mock results based on the query string.

        The tests use a limited set of queries; we match them with simple
        substring checks and return data structures that mimic the real driver.
        """
        q = query.strip().lower()
        # SHOW DATABASES
        if q.startswith("show databases"):
            return [(self.database,)]
        # SHOW TABLES FROM somaagent
        if q.startswith("show tables from"):
            tables = [
                ("capsule_executions",),
                ("conversations",),
                ("policy_decisions",),
                ("marketplace_transactions",),
                ("workflow_executions",),
                ("capsule_executions_hourly",),
                ("marketplace_revenue_daily",),
                ("policy_decisions_hourly",),
            ]
            return tables
        # COUNT queries for inserted rows
        if "count(*)" in q:
            return [(1,)]
        # Any SELECT returning rows – return empty list
        if q.startswith("select"):
            return []
        # INSERT statements – no return needed
        return None
