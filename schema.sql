-- schema.sql
CREATE TABLE transactions (
    date DATE,
    description TEXT,
    amount REAL,
    tag TEXT,
    card TEXT,
    PRIMARY KEY (date, description, amount)
);

CREATE TABLE imports (
    date DATE,
    amount REAL,
    PRIMARY KEY (date, amount)
);

CREATE TABLE budget_accumulations (
    date DATE,
    tag TEXT,
    amount REAL,
    PRIMARY KEY (date, tag)
);

CREATE TABLE IF NOT EXISTS cetes (
    date TEXT,
    instrumento TEXT,
    invertido REAL,
    plusminus REAL,
    disp REAL,
    valuado REAL,
    PRIMARY KEY (date, instrumento)
)
