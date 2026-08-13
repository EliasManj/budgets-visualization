import logging
import os
import sqlite3
import warnings

import pandas as pd

import utils

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
warnings.filterwarnings("ignore", message="Workbook contains no default style")

DB_PATH = "db/database.db"


def _get_xlsx_files(data_dir: str) -> list[str]:
    return [f for f in os.listdir(data_dir) if f.endswith(".xlsx")]


def _insert_transaction(cursor, conn, fecha, descripcion, importe, tag, card):
    if importe <= 0.0:
        return
    cursor.execute(
        "SELECT COUNT(*) FROM transactions WHERE date = ? AND description = ? AND amount = ?",
        (fecha, descripcion, importe),
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO transactions (date, description, amount, tag, card) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT (date, description, amount) DO NOTHING;",
            (fecha, descripcion, importe, tag, card),
        )
        conn.commit()


def _insert_import(cursor, conn, fecha, importe):
    if importe <= 0.0:
        return
    cursor.execute(
        "SELECT COUNT(*) FROM imports WHERE date = ? AND amount = ?",
        (fecha, importe),
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO imports (date, amount) VALUES (?, ?) "
            "ON CONFLICT (date, amount) DO NOTHING;",
            (fecha, importe),
        )
        conn.commit()


def import_bbva_debit():
    data_dir = "./data/bbva_debit"
    keywords = utils.load_keywords()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        for file in _get_xlsx_files(data_dir):
            df = pd.read_excel(os.path.join(data_dir, file), skiprows=[0, 1, 2])
            expected_cols = {"FECHA", "DESCRIPCIÓN", "CARGO", "ABONO", "SALDO"}
            if not expected_cols.issubset(df.columns):
                logger.error(
                    "[bbva_debit] Unexpected format in '%s': expected columns %s, got %s",
                    file, expected_cols, set(df.columns)
                )
                continue
            df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d/%m/%Y", errors="coerce")
            df = df.dropna(subset=["FECHA"])

            abonos_df = df[df["ABONO"].notna()][["FECHA", "ABONO"]].rename(
                columns={"ABONO": "amount", "FECHA": "date"}
            )
            abonos_df["amount"] = (
                abonos_df["amount"].astype(str).str.replace(",", "").astype(float).abs()
            )

            charges_df = df.dropna(subset=["CARGO"]).drop(columns=["ABONO", "SALDO"])
            charges_df = charges_df.rename(
                columns={"DESCRIPCIÓN": "description", "CARGO": "amount", "FECHA": "date"}
            )
            charges_df["description"] = (
                charges_df["description"].str.lower().str.split().str.join(" ")
            )
            charges_df["TAG"] = charges_df["description"].apply(
                lambda x: utils.infer_tag(keywords, x)
            )
            charges_df = charges_df[charges_df["TAG"] != "Ignore"]
            charges_df["amount"] = (
                charges_df["amount"].str.replace(",", "").astype(float).abs()
            )

            for _, row in abonos_df.iterrows():
                _insert_import(cursor, conn, row["date"].date(), row["amount"])

            for _, row in charges_df.iterrows():
                _insert_transaction(
                    cursor, conn,
                    row["date"].date(), row["description"], row["amount"], row["TAG"],
                    "bbva_debit",
                )


def import_bbva_credit():
    data_dir = "./data/bbva"
    keywords = utils.load_keywords()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        for file in _get_xlsx_files(data_dir):
            df = pd.read_excel(os.path.join(data_dir, file), skiprows=[0, 1, 3])
            expected_cols = {"FECHA", "DESCRIPCIÓN", "CARGO", "ABONO", "SALDO"}
            if not expected_cols.issubset(df.columns):
                logger.error(
                    "[bbva_credit] Unexpected format in '%s': expected columns %s, got %s",
                    file, expected_cols, set(df.columns)
                )
                continue
            df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d/%m/%Y", errors="coerce")
            df = df.dropna(subset=["FECHA", "CARGO"])
            df = df[df["CARGO"] >= 0].drop(columns=["ABONO", "SALDO"])
            df = df.rename(
                columns={"DESCRIPCIÓN": "description", "CARGO": "amount", "FECHA": "date"}
            )
            df["description"] = df["description"].str.split().str.join(" ")
            df["TAG"] = df["description"].apply(lambda x: utils.infer_tag(keywords, x))

            for _, row in df.iterrows():
                _insert_transaction(
                    cursor, conn,
                    row["date"].date(), row["description"], float(row["amount"]), row["TAG"],
                    "bbva_credit",
                )


if __name__ == "__main__":
    import_bbva_credit()
    import_bbva_debit()