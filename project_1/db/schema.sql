DROP TABLE IF EXISTS list;
CREATE TABLE list (
    url TEXT PRIMARY KEY,
    name TEXT
);

DROP TABLE IF EXISTS item;
CREATE TABLE item (
    name TEXT PRIMARY KEY
);

DROP TABLE IF EXISTS item_list;
CREATE TABLE item_list (
    id_item INTEGER,
    id_list INTEGER,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (id_item) REFERENCES item(name),
    FOREIGN KEY (id_list) REFERENCES list(url),
    PRIMARY KEY (id_item, id_list)
);

