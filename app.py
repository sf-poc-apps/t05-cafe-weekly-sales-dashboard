import os
import pathlib

import pandas as pd
import streamlit as st

from lib import (
    compute_totals,
    filter_categories,
    load_sample,
    load_upload,
    parse_uploaded,
    required_columns,
    sales_by_category,
    sales_by_day,
    top_items,
)

st.set_page_config(page_title="Cafe Weekly Sales", layout="wide")

# sf-banner: required POC banner. Do not remove.
expires = os.environ.get("SF_EXPIRES", "")[:10] or "soon"
st.markdown(
    f"<div id='sf-banner' style='background:#4b1f7a;color:#fff;padding:6px 12px;border-radius:6px;"
    f"font-weight:600;text-align:center'>POC built by an AI software factory - expires on {expires}. "
    f"Do not upload personal or confidential data.</div>",
    unsafe_allow_html=True,
)

st.title("Cafe Weekly Sales")

# Load bundled sample data on first run (in-memory only, nothing persisted).
if "data" not in st.session_state:
    st.session_state["data"] = load_sample()

uploaded = st.file_uploader("Upload a CSV (max 5 MB)", type=["csv"])
if uploaded is not None:
    if uploaded.size > 5 * 1024 * 1024:
        st.error("File too large: please upload a CSV of 5 MB or less. Previous data is still shown.")
    else:
        try:
            candidate = load_upload(uploaded)
        except Exception:
            st.error("Could not read that file as CSV. Previous data is still shown.")
            candidate = None
        if candidate is not None:
            ok, msg, parsed = parse_uploaded(candidate)
            if ok:
                st.session_state["data"] = parsed
                st.caption("Using uploaded file: " + uploaded.name)
            else:
                st.error(
                    f"Invalid CSV: expected columns {', '.join(required_columns())}. "
                    f"Previous data is still shown. ({msg})"
                )
else:
    st.caption("Using bundled sample data")

df_all = st.session_state["data"]

# Category filter applied to every view below.
categories = sorted(df_all["category"].unique().tolist())
selected = st.multiselect("Filter by category", categories)
df = filter_categories(df_all, selected)

if len(df) == 0:
    st.info("No rows for the selected category filter.")
    st.stop()

totals = compute_totals(df)
c1, c2, c3 = st.columns(3)
c1.metric("Revenue", f"{totals['revenue']:,.2f}")
c2.metric("Items sold", f"{totals['items']:,}")
c3.metric("Days", totals["days"])

left, right = st.columns(2)
with left:
    st.subheader("Sales by category")
    st.bar_chart(sales_by_category(df).set_index("category")["amount"])
with right:
    st.subheader("Daily sales trend")
    st.line_chart(sales_by_day(df).set_index("date")["amount"])

st.subheader("Top 5 items")
st.dataframe(top_items(df, n=5), use_container_width=True)

st.subheader("Filtered rows")
st.caption(f"{len(df):,} rows" + (" (all categories)" if not selected else ""))
st.dataframe(df, use_container_width=True)
