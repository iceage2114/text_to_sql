"""
Shared SQLAlchemy engine singleton.

Supports two MSSQL_CONN_STR formats:

  1) Raw ODBC string (what SSMS / connection dialogs give you):
       DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=MyDB;Trusted_Connection=yes

  2) SQLAlchemy URL (backslash in instance name must be %-encoded as %5C):
       mssql+pyodbc://@localhost%5CSQLEXPRESS/MyDB?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes

Set whichever form you prefer in .env as MSSQL_CONN_STR.
"""
from __future__ import annotations

import urllib.parse

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config import settings


def _build_engine() -> Engine:
    conn_str = settings.mssql_conn_str.strip()

    # Detect raw ODBC string (contains DRIVER= keyword)
    if "DRIVER=" in conn_str.upper():
        quoted = urllib.parse.quote_plus(conn_str)
        url = f"mssql+pyodbc:///?odbc_connect={quoted}"
    else:
        url = conn_str

    return create_engine(
        url,
        pool_pre_ping=True,   # detect stale connections
        pool_size=5,
        max_overflow=10,
    )


# Module-level singleton — imported by all tools and schema modules
engine: Engine = _build_engine()
