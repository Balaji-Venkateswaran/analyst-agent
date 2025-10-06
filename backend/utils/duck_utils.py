import duckdb
import pandas as pd

# Keep a single global DuckDB connection
# Use ":memory:" for in-memory or a file path for persistence
con = duckdb.connect(database="analyst_agent.duckdb")

def store_dataframe(df: pd.DataFrame, table_name: str):
    """Store or replace a dataframe into DuckDB as a table."""
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")

def run_sql(sql: str) -> pd.DataFrame:
    """Execute SQL against DuckDB and return Pandas DataFrame."""
    return con.execute(sql).df()
