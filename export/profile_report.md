# Gold export profile - 2026-09-01T04:11:06+00:00

## Shape
- fact_games: 27075 rows, 22 columns
- game_genres: 76462 rows, 29 distinct genres

## Nulls in fact_games (non-zero columns only)

## Structural checks
- duplicate appid rows: 0
- game_genres rows with no matching fact_games appid: 0

## Answer-key checks (tolerant of rounding)
[OK      ] total games: got 27075, expected 27075 (+/- 0)
[OK      ] avg paid price (USD): got 6.71, expected 6.71 (+/- 0.02)
[OK      ] free games share (%): got 9.46, expected 9.5 (+/- 0.1)
[OK      ] Indie share (%): got 71.73, expected 71.73 (+/- 0.1)
[OK      ] Action share (%): got 43.96, expected 43.96 (+/- 0.1)
[OK      ] RPG count: got 4311, expected 4311 (+/- 0)
[OK      ] 2018 releases: got 8160, expected 8160 (+/- 0)
[OK      ] price vs review-rate correlation: got 0.0829, expected 0.0765 (+/- 0.01)

## Result: PASS