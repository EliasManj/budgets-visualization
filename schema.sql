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

CREATE TABLE cetes (
    date DATE,
    amount REAL,
    PRIMARY KEY (date, amount)
);

CREATE TABLE cetes_detail (
    date DATE,
    emisora TEXT,
    serie TEXT,
    plazo INTEGER,
    titulos INTEGER,
    precio REAL,
    valuacion REAL,
    PRIMARY KEY (date, emisora, serie, titulos, plazo)
);

CREATE TABLE budget_accumulations (
    date DATE,
    tag TEXT,
    amount REAL,
    PRIMARY KEY (date, tag)
);