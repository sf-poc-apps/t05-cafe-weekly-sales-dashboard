# Cafe Weekly Sales Dashboard

A single-page Streamlit dashboard built by the Software Factory POC.

Shows a cafe owner their weekly sales at a glance: headline totals (revenue,
items sold, days), a sales-by-category bar chart, a daily trend line chart and
a top-5 items table, all filterable by category.

## Usage

- Run locally: `streamlit run app.py` (the app also respects `$PORT`, default 8080).
- The dashboard opens with bundled sample data from `data/sample_sales.csv`.
- Upload your own CSV (max 5 MB) with columns `date, category, item, quantity, amount`;
  invalid uploads are rejected with an error and the previous data stays on screen.
- Use the category multiselect to filter every view. Nothing is persisted; all data
  stays in memory for the session.
- Health endpoint: `/_stcore/health`.

## Development

- Install: `pip install -r requirements-dev.txt`
- Tests: `python -m pytest -q`
- Policy scan: `python3 .sf/policy_scan.py`
