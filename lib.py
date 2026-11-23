"""Pure data logic for the cafe weekly sales dashboard. No Streamlit imports."""
import pathlib

import pandas as pd

MAX_ROWS = 50_000
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

SAMPLE_PATH = pathlib.Path(__file__).parent / "data" / "sample_sales.csv"

REQUIRED_COLUMNS = ["date", "category", "item", "quantity", "amount"]


def required_columns() -> list[str]:
    """Return the columns every valid sales CSV must have."""
    return list(REQUIRED_COLUMNS)


def _coerce(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["category"] = df["category"].astype(str)
    df["item"] = df["item"].astype(str)
    return df


def validate_columns(df: pd.DataFrame) -> tuple[bool, str]:
    """Check that df has the required columns. Returns (ok, message)."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return False, "Missing column(s): " + ", ".join(missing)
    return True, ""


def load_sample() -> pd.DataFrame:
    """Load the bundled sample CSV, coerced and sorted by date."""
    df = pd.read_csv(SAMPLE_PATH, nrows=MAX_ROWS)
    df.columns = [str(c).strip().lower() for c in df.columns]
    ok, msg = validate_columns(df)
    if not ok:
        raise ValueError(msg)
    df = _coerce(df).sort_values("date").reset_index(drop=True)
    return df


def load_upload(source) -> pd.DataFrame:
    """Read an uploaded CSV into a DataFrame, without coercing."""
    df = pd.read_csv(source, nrows=MAX_ROWS)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def parse_uploaded(df: pd.DataFrame) -> tuple[bool, str, "pd.DataFrame | None"]:
    """Validate and coerce an uploaded DataFrame. Returns (ok, message, data)."""
    ok, msg = validate_columns(df)
    if not ok:
        return False, "Invalid CSV: " + msg, None
    coerced = _coerce(df)
    if coerced["date"].isna().any() or coerced["quantity"].isna().any() or coerced["amount"].isna().any():
        return False, "Invalid CSV: could not parse every date, quantity or amount value.", None
    coerced = coerced.sort_values("date").reset_index(drop=True)
    return True, "", coerced


def compute_totals(df: pd.DataFrame) -> dict:
    """Return revenue, items sold and distinct-day count for the given rows."""
    if df is None or len(df) == 0:
        return {"revenue": 0.0, "items": 0, "days": 0}
    dates = df["date"].dropna()
    days = int(dates.dt.normalize().nunique()) if len(dates) else 0
    return {
        "revenue": float(df["amount"].fillna(0).sum()),
        "items": int(df["quantity"].fillna(0).sum()),
        "days": days,
    }


def sales_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Summed amount per category, descending by amount."""
    if df is None or len(df) == 0:
        return pd.DataFrame({"category": [], "amount": []})
    out = (
        df.groupby("category", dropna=False)["amount"].sum().sort_values(ascending=False).reset_index()
    )
    out.columns = ["category", "amount"]
    return out


def sales_by_day(df: pd.DataFrame) -> pd.DataFrame:
    """Summed amount per calendar day, in date order."""
    if df is None or len(df) == 0:
        return pd.DataFrame({"date": pd.Series([], dtype="datetime64[ns]"), "amount": pd.Series([], dtype="float64")})
    out = df.copy()
    out["day"] = out["date"].dt.normalize()
    out = out.groupby("day")["amount"].sum().sort_index().reset_index()
    out.columns = ["date", "amount"]
    return out


def top_items(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Top-n items by summed amount, highest first."""
    if df is None or len(df) == 0:
        return pd.DataFrame({"item": [], "amount": [], "quantity": []})
    out = (
        df.groupby("item")
        .agg(amount=("amount", "sum"), quantity=("quantity", "sum"))
        .sort_values("amount", ascending=False)
        .head(n)
        .reset_index()
    )
    return out[["item", "amount", "quantity"]]


def filter_categories(df: pd.DataFrame, selected) -> pd.DataFrame:
    """Keep only rows whose category is in `selected` (empty selection = all rows)."""
    if df is None or selected is None or len(selected) == 0:
        return df
    return df[df["category"].isin(list(selected))]