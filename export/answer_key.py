"""
export/answer_key.py

Single source of truth for the "known good" Gold-layer aggregates, originally
computed from the 27,075-row Databricks Gold tables via sql/validate_*.sql.
Every script that checks correctness (profile_data.py, validate_load.py, and
later api/tests/) should import from here instead of hardcoding numbers.
"""

EXPECTED_TOTAL_GAMES = 27_075
EXPECTED_AVG_PAID_PRICE = 6.71             # AVG(price) WHERE is_free = false, USD
EXPECTED_FREE_SHARE_PCT = 9.5              # % of games where is_free = true
EXPECTED_INDIE_SHARE_PCT = 71.73           # % of games tagged 'Indie' (multi-label; doesn't sum to 100 with others)
EXPECTED_ACTION_SHARE_PCT = 43.96          # % of games tagged 'Action'
EXPECTED_RPG_COUNT = 4_311                 # count of games tagged 'RPG'
EXPECTED_2018_RELEASES = 8_160
EXPECTED_YOY_2018_PCT = 28.4               # (2018 releases / 2017 releases - 1) * 100
EXPECTED_YOY_2017_PCT = 45.8
EXPECTED_PRICE_REVIEW_CORRELATION = 0.0765  # Pearson r, price vs positive_review_rate

# 2019 is a partial year (data ends 2019-05-01) - YoY MUST be null/omitted, never computed.
PARTIAL_YEAR = 2019
# Years with <50 releases are historically noisy and get trimmed from trend charts.
MIN_RELEASES_FOR_TREND_YEAR = 50