from mautrix.util.async_db import Connection, UpgradeTable

upgrade_table = UpgradeTable()


@upgrade_table.register(description="Initial revision")
async def upgrade_v1(conn: Connection) -> None:
    await conn.execute(
        """CREATE TABLE oncall (
         username TEXT PRIMARY KEY,
         mxid TEXT NOT NULL,
         timezone TEXT NOT NULL
    )"""
    )
