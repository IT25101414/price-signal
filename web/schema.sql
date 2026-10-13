-- Price Signal web database (SQLite). Rebuilt from cards.csv (and prices_all.csv) by build_db.py.
DROP TABLE IF EXISTS cards;
DROP TABLE IF EXISTS prices;
DROP TABLE IF EXISTS meta;

-- One row per item per Colombo series, for the latest report. Same columns as ../cards.csv.
CREATE TABLE cards (
    report_date         TEXT NOT NULL,      -- ISO date of the report the card is based on
    item                TEXT NOT NULL,
    series              TEXT NOT NULL,      -- 'wholesale Pettah' | 'retail Pettah' | 'retail Narahenpita'
    dambulla_rs         REAL,
    colombo_rs          REAL,
    gap_vs_usual_pct    REAL,
    expected_change_pct REAL,
    low_pct             REAL,
    high_pct            REAL,
    direction           TEXT,               -- 'up' | 'down' | NULL
    signal              TEXT,               -- 'strong' | 'weak' | NULL
    status              TEXT NOT NULL,      -- ok | no_clear_signal | insufficient_data | ...
    reason              TEXT NOT NULL,
    PRIMARY KEY (item, series)
);

-- Price history, one row per report day and series. Optional: needs prices_all.csv.
CREATE TABLE prices (
    report_date TEXT NOT NULL,
    item        TEXT NOT NULL,
    series      TEXT NOT NULL,              -- 'wholesale Dambulla' plus the three Colombo series
    price_rs    REAL NOT NULL,
    PRIMARY KEY (report_date, item, series)
);
CREATE INDEX idx_prices_item ON prices (item, report_date);

CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
