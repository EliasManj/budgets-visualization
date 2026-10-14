from datetime import datetime
from typing import List

import pandas as pd
import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.db import execute_sql, fetch_data
from api.finance import calculate_compound_interest_with_monthly_addition
from amex import import_amex
from banamex import import_banamex_credit, import_banamex_debit
from bbva import import_bbva_credit, import_bbva_debit
from cetes import import_cetes

app = FastAPI(title="Budgets API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_now = datetime.now()
DEFAULT_MONTH = _now.month
DEFAULT_YEAR = _now.year

ALL_CARDS = ["amex", "bbva_debit", "bbva_credit", "banamex_debit", "banamex_credit"]


def _load_budget_df() -> pd.DataFrame:
    with open("budgets.yaml", "r") as f:
        data = yaml.safe_load(f)
    df = pd.DataFrame(data["budgets"])
    df.columns = ["tag", "category", "budget"]
    return df


def _filter_transactions(
    month: int,
    year: int,
    day_start: int,
    day_end: int,
    tags: List[str],
    cards: List[str],
) -> pd.DataFrame:
    """Return transactions merged with budget info, filtered by the given params."""
    df = fetch_data("SELECT * FROM transactions")
    budget_df = _load_budget_df()
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df = pd.merge(df, budget_df, on="tag", how="left")
    return df[
        (df["date"].dt.month == month)
        & (df["date"].dt.year == year)
        & (df["date"].dt.day >= day_start)
        & (df["date"].dt.day <= day_end)
        & (df["tag"].isin(tags))
        & (df["card"].isin(cards))
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/budgets")
def get_budgets():
    """Return the budget configuration from budgets.yaml."""
    with open("budgets.yaml", "r") as f:
        data = yaml.safe_load(f)
    return data["budgets"]


@app.get("/api/transactions")
def get_transactions(
    month: int = DEFAULT_MONTH,
    year: int = DEFAULT_YEAR,
    day_start: int = 1,
    day_end: int = 31,
    tags: List[str] = Query(default=None),
    cards: List[str] = Query(default=None),
    sort_column: str = "date",
    sort_order: str = "Ascending",
):
    budget_df = _load_budget_df()
    if tags is None:
        tags = list(budget_df["tag"])
    if cards is None:
        cards = ALL_CARDS

    filtered = _filter_transactions(month, year, day_start, day_end, tags, cards)
    filtered = filtered.sort_values(
        by=sort_column, ascending=(sort_order == "Ascending")
    )
    filtered = filtered.copy()
    filtered["date"] = filtered["date"].dt.strftime("%Y-%m-%d")
    filtered = filtered.drop(columns=["budget"], errors="ignore")
    return filtered.to_dict(orient="records")


@app.get("/api/transactions/by-tag")
def get_transactions_by_tag(
    month: int = DEFAULT_MONTH,
    year: int = DEFAULT_YEAR,
    day_start: int = 1,
    day_end: int = 31,
    tags: List[str] = Query(default=None),
    cards: List[str] = Query(default=None),
):
    budget_df = _load_budget_df()
    if tags is None:
        tags = list(budget_df["tag"])
    if cards is None:
        cards = ALL_CARDS

    filtered = _filter_transactions(month, year, day_start, day_end, tags, cards)
    grouped = filtered.groupby("tag")["amount"].sum().reset_index()
    merged = pd.merge(grouped, budget_df, on="tag", how="inner")
    merged = merged[["tag", "category", "budget", "amount"]]

    expense_df = merged[merged["category"] == "Expense"]
    investment_df = merged[merged["category"] == "Investment"]

    totals = pd.DataFrame(
        [
            {
                "tag": "",
                "category": "Total (expense)",
                "budget": float(expense_df["budget"].sum()),
                "amount": float(expense_df["amount"].sum()),
            },
            {
                "tag": "",
                "category": "Total (investment)",
                "budget": float(investment_df["budget"].sum()),
                "amount": float(investment_df["amount"].sum()),
            },
        ]
    )

    result = pd.concat([merged, totals], ignore_index=True)
    return result.to_dict(orient="records")


@app.get("/api/imports")
def get_imports(
    month: int = DEFAULT_MONTH,
    year: int = DEFAULT_YEAR,
    day_start: int = 1,
    day_end: int = 31,
):
    df = fetch_data("SELECT * FROM imports")
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    filtered = df[
        (df["date"].dt.month == month)
        & (df["date"].dt.year == year)
        & (df["date"].dt.day >= day_start)
        & (df["date"].dt.day <= day_end)
    ].copy()
    filtered["date"] = filtered["date"].dt.strftime("%Y-%m-%d")
    return filtered.to_dict(orient="records")


@app.get("/api/summary")
def get_summary(
    month: int = DEFAULT_MONTH,
    year: int = DEFAULT_YEAR,
    day_start: int = 1,
    day_end: int = 31,
    tags: List[str] = Query(default=None),
    cards: List[str] = Query(default=None),
):
    budget_df = _load_budget_df()
    if tags is None:
        tags = list(budget_df["tag"])
    if cards is None:
        cards = ALL_CARDS

    total_expenses_budget = float(
        budget_df[budget_df["category"] == "Expense"]["budget"].sum()
    )

    filtered = _filter_transactions(month, year, day_start, day_end, tags, cards)
    total_expense = float(filtered[filtered["category"] != "Investment"]["amount"].sum())
    total_invested = float(filtered[filtered["category"] == "Investment"]["amount"].sum())
    total = float(filtered["amount"].sum())

    overspent = max(0.0, total_expense - total_expenses_budget)

    imports_df = fetch_data("SELECT * FROM imports")
    imports_df["date"] = pd.to_datetime(imports_df["date"], format="%Y-%m-%d", errors="coerce")
    income = float(
        imports_df[
            (imports_df["date"].dt.month == month)
            & (imports_df["date"].dt.year == year)
            & (imports_df["date"].dt.day >= day_start)
            & (imports_df["date"].dt.day <= day_end)
        ]["amount"].sum()
    )

    bank_delta = income - total_expense
    saved = max(0.0, bank_delta)

    return {
        "total": total,
        "total_expense": total_expense,
        "budget_overspent": overspent,
        "total_income": income,
        "total_invested": total_invested,
        "saved_cash": saved,
        "remaining_in_bank": bank_delta,
        "projections": {
            "5yr_no_interest": total_invested * 5 * 12,
            "5yr_10pct_compound": calculate_compound_interest_with_monthly_addition(
                total_invested, 0.1, 5, total_invested
            ),
            "5yr_20pct_compound": calculate_compound_interest_with_monthly_addition(
                total_invested, 0.2, 5, total_invested
            ),
        },
    }


@app.get("/api/budget-usage")
def get_budget_usage(
    month: int = DEFAULT_MONTH,
    year: int = DEFAULT_YEAR,
    day_start: int = 1,
    day_end: int = 31,
    tags: List[str] = Query(default=None),
    cards: List[str] = Query(default=None),
):
    budget_df = _load_budget_df()
    if tags is None:
        tags = list(budget_df["tag"])
    if cards is None:
        cards = ALL_CARDS

    filtered = _filter_transactions(month, year, day_start, day_end, tags, cards)
    spending = filtered.groupby("tag")["amount"].sum().reset_index()
    merged = pd.merge(spending, budget_df, on="tag", how="left")
    merged["percentage_used"] = (merged["amount"] / merged["budget"]) * 100
    merged["color"] = merged["percentage_used"].apply(
        lambda x: "yellow" if 100 < x < 130 else ("red" if x >= 130 else "green")
    )
    return merged.to_dict(orient="records")


@app.get("/api/cetes")
def get_cetes(
    month: int = DEFAULT_MONTH,
    year: int = DEFAULT_YEAR,
):
    padded_month = f"{month:02d}"
    query = f"""
        SELECT * FROM cetes
        WHERE strftime('%m', date) = '{padded_month}'
          AND strftime('%Y', date) = '{year}'
    """
    return fetch_data(query).to_dict(orient="records")


@app.post("/api/refresh")
def refresh_data():
    """Re-import all bank data files into the database."""
    import_bbva_credit()
    import_bbva_debit()
    import_amex()
    import_banamex_debit()
    import_banamex_credit()
    import_cetes()
    return {"status": "ok", "message": "Data refreshed successfully"}


@app.post("/api/reset")
def reset_data():
    """Delete all transaction, import, and cetes data from the database."""
    execute_sql("DELETE FROM transactions")
    execute_sql("DELETE FROM imports")
    execute_sql("DELETE FROM cetes")
    return {"status": "ok", "message": "Data reset successfully"}


# Serve the frontend — mount last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
