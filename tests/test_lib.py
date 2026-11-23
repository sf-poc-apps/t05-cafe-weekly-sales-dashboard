import io
import pathlib

import pandas as pd

from lib import (
    compute_totals,
    filter_categories,
    load_sample,
    parse_uploaded,
    required_columns,
    sales_by_category,
    sales_by_day,
    top_items,
    validate_columns,
)

APP = pathlib.Path(__file__).resolve().parent.parent / "app.py"


def fixture_df():
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-11-16", "2026-11-16", "2026-11-17", "2026-11-18", "2026-11-18", "2026-11-18"]),
            "category": ["Coffee", "Pastry", "Coffee", "Tea", "Coffee", "Pastry"],
            "item": ["Latte", "Croissant", "Espresso", "Green Tea", "Latte", "Muffin"],
            "quantity": [2, 3, 4, 1, 5, 2],
            "amount": [7.5, 9.0, 12.0, 3.0, 25.0, 6.0],
        }
    )


def test_load_sample_returns_expected_columns():
    df = load_sample()
    for col in required_columns():
        assert col in df.columns
    assert len(df) > 0
    assert str(df["date"].dtype).startswith("datetime")


def test_validate_columns_accepts_correct_schema():
    ok, msg = validate_columns(fixture_df())
    assert ok
    assert msg == ""


def test_validate_columns_rejects_missing_columns():
    bad = fixture_df().drop(columns=["amount"])
    ok, msg = validate_columns(bad)
    assert not ok
    assert "amount" in msg


def test_totals_match_filtered_data():
    totals = compute_totals(fixture_df())
    assert totals["revenue"] == 62.5
    assert totals["items"] == 17
    assert totals["days"] == 3


def test_category_aggregation():
    out = sales_by_category(fixture_df())
    assert list(out["category"]) == ["Coffee", "Pastry", "Tea"]
    assert list(out["amount"]) == [44.5, 15.0, 3.0]


def test_daily_aggregation():
    out = sales_by_day(fixture_df())
    assert list(out["date"]) == list(pd.to_datetime(["2026-11-16", "2026-11-17", "2026-11-18"]))
    assert list(out["amount"]) == [16.5, 12.0, 34.0]


def test_top_5_items():
    out = top_items(fixture_df(), n=5)
    assert len(out) == 5
    assert list(out.columns) == ["item", "amount", "quantity"]
    amounts = list(out["amount"])
    assert amounts == sorted(amounts, reverse=True)
    assert out.iloc[0]["item"] == "Latte"
    assert out.iloc[0]["amount"] == 32.5


def test_category_filter_subsets_data():
    df = fixture_df()
    filtered = filter_categories(df, ["Coffee"])
    assert len(filtered) < len(df)
    assert set(filtered["category"]) == {"Coffee"}
    totals = compute_totals(filtered)
    assert totals["revenue"] == 44.5
    assert totals["items"] == 11


def test_parse_uploaded_rejects_bad_values():
    df = pd.DataFrame(
        {
            "date": ["2026-11-16", "not-a-date"],
            "category": ["Coffee", "Tea"],
            "item": ["Latte", "Green Tea"],
            "quantity": [2, 1],
            "amount": [7.5, 3.0],
        }
    )
    ok, msg, parsed = parse_uploaded(df)
    assert not ok
    assert parsed is None


def test_parse_uploaded_accepts_valid_csv_string():
    csv = "date,category,item,quantity,amount\n2026-11-16,Coffee,Latte,2,7.5\n"
    ok, msg, parsed = parse_uploaded(
        pd.read_csv(io.StringIO(csv))
    )
    assert ok
    assert parsed is not None
    assert compute_totals(parsed)["revenue"] == 7.5


def test_banner_present():
    assert "sf-banner" in APP.read_text()
