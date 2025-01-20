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

CREATE TABLE cetes (
    instrumento TEXT,
    invertido REAL,
    plusminus REAL, 
    disp REAL,
    valuado REAL
);

INSERT INTO cetes (instrumento, invertido, plusminus, disp, valuado)
VALUES
    ('BONDIA', 10800.58, 468.36, 10800.58, 10800.58),
    ('CETES', 93109.63, 1284.46, 93469.98, 93394.06),
    ('ENERFIN', 57962.9, 3792.33, 61755.24, 61755.24);
