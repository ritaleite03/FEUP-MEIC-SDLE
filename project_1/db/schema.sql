DROP TABLE IF EXISTS client;
CREATE TABLE client (
    id INTEGER PRIMARY KEY
);

DROP TABLE IF EXISTS list;
CREATE TABLE list (
    url TEXT PRIMARY KEY,
    name TEXT,
    owner INTEGER,
    FOREIGN KEY (owner) REFERENCES client(id)
);

DROP TABLE IF EXISTS item_list;
CREATE TABLE item_list (
    item TEXT,
    list TEXT,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (list) REFERENCES list(url),
    PRIMARY KEY (item, list)
);

