import sqlite3

conn = sqlite3.connect("bluestock_mf.db")
tables = [row[0] for row in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
)]

for t in tables:
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})").fetchall()]
    print(f"{t}: {cols}")

conn.close()