from sqlite3 import IntegrityError

from asyncpg.exceptions import UniqueViolationError
from mautrix.util.async_db import Connection, UpgradeTable

UNIQUE_ERROR = (UniqueViolationError, IntegrityError)

upgrade_table = UpgradeTable()


@upgrade_table.register(description="Initial revision")  # type: ignore
async def upgrade_v1(conn: Connection) -> None:
    await conn.execute("""CREATE TABLE oncall (
         username TEXT PRIMARY KEY,
         mxid TEXT NOT NULL,
         timezone TEXT NOT NULL
    )""")


@upgrade_table.register(description="Add cookies table")  # type: ignore
async def upgrade_v2(conn: Connection) -> None:
    await conn.execute("""
        CREATE TABLE cookies (
            from_user VARCHAR(254) NOT NULL,
            to_user VARCHAR(254) NOT NULL,
            release VARCHAR(63) NOT NULL,
            value INTEGER NOT NULL DEFAULT 1,
            date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (from_user, to_user, release)
        )
    """)
    await conn.execute("""
        CREATE INDEX idx_cookies_to_user_release ON cookies (to_user, release);
    """)


@upgrade_table.register(description="Add index on cookie.to_user")  # type: ignore
async def upgrade_v3(conn: Connection) -> None:
    await conn.execute("""
        CREATE INDEX idx_cookies_to_user ON cookies (to_user);
    """)
