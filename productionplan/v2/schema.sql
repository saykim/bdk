DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS plans;

CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    bom TEXT NOT NULL
);

CREATE TABLE plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    duration REAL NOT NULL,
    end_time TEXT NOT NULL,
    line INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    bom TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    notes TEXT,
    done INTEGER DEFAULT 0,
    FOREIGN KEY (product_id) REFERENCES products (id)
); 