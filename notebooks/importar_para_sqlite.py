"""Importa dados/transacoes_cafeterias.csv para o banco SQLite dados/cafeterias.db.

Uso (na raiz do repositório):
    python scripts/importar_para_sqlite.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CSV = RAIZ / "dados" / "transacoes_cafeterias.csv"
BANCO = RAIZ / "dados" / "cafeterias.db"

SCHEMA = """
DROP TABLE IF EXISTS transacoes;
CREATE TABLE transacoes (
    transaction_id    INTEGER PRIMARY KEY,
    transaction_date  TEXT    NOT NULL,   -- AAAA-MM-DD
    transaction_time  TEXT    NOT NULL,   -- HH:MM:SS
    store_id          INTEGER NOT NULL,
    store_location    TEXT    NOT NULL,
    product_id        INTEGER NOT NULL,
    transaction_qty   INTEGER NOT NULL,
    unit_price        REAL    NOT NULL,
    total_bill        REAL    NOT NULL,
    product_category  TEXT    NOT NULL,
    product_type      TEXT    NOT NULL,
    product_detail    TEXT    NOT NULL,
    size              TEXT,
    month_name        TEXT,
    day_name          TEXT,
    hour              INTEGER,
    month             INTEGER,
    day_of_week       INTEGER               -- 0 = segunda-feira
);
"""

INDICES = [
    "CREATE INDEX idx_data ON transacoes(transaction_date)",
    "CREATE INDEX idx_loja ON transacoes(store_location)",
    "CREATE INDEX idx_categoria ON transacoes(product_category)",
]


def main() -> None:
    df = pd.read_csv(CSV, parse_dates=["transaction_date"])
    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")
    df = df.rename(columns=str.lower).rename(
        columns={"month name": "month_name", "day name": "day_name",
                 "day of week": "day_of_week"}
    )

    with sqlite3.connect(BANCO) as con:
        con.executescript(SCHEMA)
        df.to_sql("transacoes", con, if_exists="append", index=False)
        for comando in INDICES:
            con.execute(comando)
        total = con.execute("SELECT COUNT(*) FROM transacoes").fetchone()[0]

    print(f"{total:,} linhas importadas para {BANCO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
