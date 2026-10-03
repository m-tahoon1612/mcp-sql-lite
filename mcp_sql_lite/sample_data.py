"""Fake shop schema so the server has something to answer about.

Loaded into an in-memory sqlite db on startup. Numbers are made up.
"""
import sqlite3

SCHEMA = {
    "customers": [
        ("customer_id", "INTEGER", "primary key"),
        ("name", "TEXT", ""),
        ("country", "TEXT", "ISO-2"),
        ("signup_date", "TEXT", "YYYY-MM-DD"),
    ],
    "products": [
        ("product_id", "INTEGER", "primary key"),
        ("title", "TEXT", ""),
        ("category", "TEXT", ""),
        ("price_eur", "REAL", "list price"),
    ],
    "orders": [
        ("order_id", "INTEGER", "primary key"),
        ("customer_id", "INTEGER", "-> customers"),
        ("product_id", "INTEGER", "-> products"),
        ("qty", "INTEGER", ""),
        ("order_date", "TEXT", "YYYY-MM-DD"),
        ("status", "TEXT", "paid / refunded / pending"),
    ],
}

CUSTOMERS = [
    (1, "Lena Hoffmann", "DE", "2025-11-02"),
    (2, "Omar Saleh", "EG", "2025-12-14"),
    (3, "Julia Rossi", "IT", "2026-01-09"),
    (4, "Tom Becker", "DE", "2026-02-21"),
    (5, "Aisha Khan", "GB", "2026-03-03"),
    (6, "Pieter de Vries", "NL", "2026-04-17"),
]

PRODUCTS = [
    (10, "Mechanical keyboard", "hardware", 89.0),
    (11, "USB-C hub", "hardware", 34.5),
    (12, "Notebook A5 dotted", "stationery", 7.9),
    (13, "Desk lamp", "home", 42.0),
    (14, "Noise cancelling headphones", "hardware", 199.0),
]

ORDERS = [
    (100, 1, 10, 1, "2026-05-02", "paid"),
    (101, 2, 12, 3, "2026-05-03", "paid"),
    (102, 3, 14, 1, "2026-05-10", "refunded"),
    (103, 1, 11, 2, "2026-06-01", "paid"),
    (104, 4, 13, 1, "2026-06-11", "pending"),
    (105, 5, 10, 1, "2026-07-19", "paid"),
    (106, 6, 12, 5, "2026-07-20", "paid"),
    (107, 2, 14, 1, "2026-08-02", "paid"),
    (108, 3, 11, 1, "2026-08-15", "paid"),
    (109, 4, 10, 1, "2026-09-01", "refunded"),
]


def build_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    for table, cols in SCHEMA.items():
        coldefs = ", ".join(f"{c} {t}" for c, t, _ in cols)
        conn.execute(f"CREATE TABLE {table} ({coldefs})")
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?)", CUSTOMERS)
    conn.executemany("INSERT INTO products VALUES (?,?,?,?)", PRODUCTS)
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", ORDERS)
    conn.commit()
    return conn
