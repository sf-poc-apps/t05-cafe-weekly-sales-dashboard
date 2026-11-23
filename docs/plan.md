# Cafe Weekly Sales Dashboard

## Summary
A cafe owner wants to understand weekly sales at a glance without spreadsheets. This Streamlit dashboard loads a bundled sample CSV by default, lets the owner upload a same-shape CSV, and shows revenue/items/day totals, a category bar chart, a daily trend line, and a top-5-items table, all filterable by category. Data stays in memory using made-up sample data.

## Similar initiatives
- **LP-005 — Weekly store sales dashboard**: Reuses the upload-CSV-and-show-totals pattern; this plan differs by charting a cafe's category and daily trend rather than per-store totals.
- **LP-010 — Delivery time analysis**: Reuses the uploaded-CSV charting approach; differs in that we aggregate sales amount (sum) rather than average times, and group by category not region.
- **LP-023 — Budget vs actual viewer**: Reuses column-validation-on-upload and tabular summaries; differs by showing totals/top-items instead of budget variance.

## Scope
1. **Bundled sample data on first load**
   - *Story*: As the cafe owner, I want the dashboard populated with sample data immediately so I can explore it without uploading anything.
   - Given I open the app for the first time / When no file has been uploaded / Then all views render from the bundled `sample_sales.csv`.
2. **Upload a same-shape CSV**
   - *Story*: As the cafe owner, I want to upload my own weekly CSV so the dashboard shows my numbers.
   - Given I upload a CSV with columns `date, category, item, quantity, amount` / When the upload succeeds / Then all totals, charts and the table use the uploaded data.
   - Given I upload a CSV with missing or wrong columns / When validation fails / Then a clear error is shown and the previously loaded data stays in all views.
3. **Totals: revenue, items sold, number of days**
   - *Story*: As the cafe owner, I want headline totals so I can see performance at a glance.
   - Given data is loaded and a filter applied / When the page renders / Then revenue (sum of `amount`), items sold (sum of `quantity`) and number of distinct days match the filtered rows.
4. **Sales amount by category (bar chart)**
   - *Story*: As the cafe owner, I want to see which categories drive sales.
   - Given data is loaded / When the page renders / Then a bar chart shows summed `amount` per `category`.
5. **Daily sales trend (line chart)**
   - *Story*: As the cafe owner, I want to see daily revenue movement.
   - Given data is loaded / When the page renders / Then a line chart shows summed `amount` per `date` in date order.
6. **Top 5 items table**
   - *Story*: As the cafe owner, I want my best sellers listed.
   - Given data is loaded / When the page renders / Then a table lists the top 5 `item` values by summed `amount`, highest first.
7. **Category filter updates all views**
   - *Story*: As the cafe owner, I want to focus on selected categories.
   - Given a multiselect of categories / When I change the selection / Then totals, both charts and the top-5 table recompute from the filtered data.

## Out of scope
- Saving uploaded data (in-memory only).
- Logins or user accounts.
- Exporting data or reports.
- Forecasting.
- Real cafe data (sample/made-up only).
- Switching charts between amount and quantity.

## Data model
No database. Data is an in-memory pandas DataFrame for the current session.

Expected CSV schema (bundled sample and uploads):

| Field | Type | Notes |
|---|---|---|
| date | date (parseable string, e.g. `YYYY-MM-DD`) | parsed to datetime |
| category | string | used for grouping and filter |
| item | string | used for top-5 |
| quantity | integer | summed for "items sold" |
| amount | number (float) | summed for revenue |

## Pages and endpoints
Single-page Streamlit app (no custom HTTP routes).

| Path | Purpose | Who uses it |
|---|---|---|
| `/` (Streamlit app) | Upload control, category filter, totals, charts, top-5 table | Cafe owner |
| `/healthz` (template health endpoint) | Liveness check | Ops / CI |

## Test plan
**Automated (unit, pytest):**
- `test_load_sample_returns_expected_columns`: bundled sample loads with the five required columns.
- `test_validate_columns_accepts_correct_schema` and `test_validate_columns_rejects_missing_columns`.
- `test_totals_match_filtered_data`: revenue = sum(amount), items = sum(quantity), days = distinct date count on a fixed fixture.
- `test_category_aggregation` and `test_daily_aggregation` produce correct sums/ordering.
- `test_top_5_items`: returns 5 rows ordered by summed amount descending.
- `test_category_filter_subsets_data`: filtering reduces rows and recomputes totals.

Put the data logic in pure functions (no Streamlit calls) so they are unit-testable.

**Manual UAT checklist (staging):**
1. Open app; confirm sample data renders with no upload and the POC banner is visible.
2. Confirm totals (revenue, items sold, days) look correct for the sample.
3. Confirm bar chart (by category) and line chart (daily) render.
4. Confirm top-5 items table shows 5 rows, highest first.
5. Upload a valid CSV; confirm all views update.
6. Upload a CSV with a missing column; confirm a clear error appears and previous data remains.
7. Change the category filter; confirm totals, both charts and the table all update.

## Risks and guardrails
- **In-memory only (template rule)**: uploaded data must not be persisted to disk or any store; it lives in `st.session_state` for the session.
- **No external services / no outbound HTTP / no auth / no email / no payments**: the "user" is the single cafe owner with no login — do not add any.
- **Validation safety**: invalid uploads must not corrupt current state; validate before replacing data.
- **Bad data handling**: coerce `quantity`/`amount` to numeric and `date` to datetime defensively; show a clear error if parsing fails rather than crashing.
- **Keep it small**: single app file plus one sample CSV and one helpers module; stay under a 40-minute build.
- **Do not change** the template banner, `/healthz` endpoint, Dockerfile or CI files.

## Builder instructions
1. In the template's main Streamlit entry (e.g. `app.py`), keep the existing **POC banner** and health endpoint wiring unchanged.
2. Add `data/sample_sales.csv` with made-up cafe rows covering ~7 days, several categories (e.g. Coffee, Pastry, Sandwich, Tea) and multiple items, with columns `date, category, item, quantity, amount`.
3. Create `logic.py` with pure functions: `load_sample()`, `required_columns()`, `validate_columns(df)`, `compute_totals(df)`, `sales_by_category(df)`, `sales_by_day(df)`, `top_items(df, n=5)`, `filter_categories(df, selected)`. No Streamlit imports here.
4. In `app.py`, initialise `st.session_state["data"]` from `load_sample()` on first run.
5. Add a `st.file_uploader` for CSV; on upload, parse with pandas, run `validate_columns`; if valid, replace session data; if invalid, call `st.error(...)` with a clear message and keep existing data.
6. Add a `st.multiselect` category filter populated from the current data; apply `filter_categories` to produce the working DataFrame for all views.
7. Render totals with `st.metric` (revenue, items sold, number of days) from `compute_totals`.
8. Render the category bar chart (`sales_by_category`) and daily line chart (`sales_by_day`) using `st.bar_chart` / `st.line_chart`.
9. Render the top-5 items table with `st.dataframe(top_items(...))`.
10. Add `tests/test_logic.py` with the unit tests listed above, using small in-code fixtures.
11. Ensure new dependencies (pandas already typical for this template) are in the template's requirements file; do not add charting libraries beyond what Streamlit provides.
12. Run the existing CI/tests locally; confirm the banner, `/healthz`, Dockerfile and CI files are untouched.
