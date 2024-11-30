DROP TABLE IF EXISTS list;
CREATE TABLE list (
    url TEXT PRIMARY KEY,
    name TEXT
);

DROP TABLE IF EXISTS item_list;
CREATE TABLE item_list (
    item TEXT,
    list TEXT,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (list) REFERENCES list(url),
    PRIMARY KEY (item, list)
);

