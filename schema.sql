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
    ('BONDIA', 21409.76,	505.31,	21409.76,	21409.76),
    ('CETES', 83418.19,	1024.75, 84,507.89,	84442.92),
    ('ENERFIN', 72944.94, 4154.69,77099.64, 77099.64),
    ('TOTAL', 177773.90, 5684.75, 183019.11, 182954.14)
    ;
