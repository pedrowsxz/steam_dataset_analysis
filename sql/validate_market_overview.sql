SELECT COUNT(*) AS total_games FROM workspace.gold.fact_games;

-- Paid games only — including $0 titles would understate "typical price";
-- free-to-play gets its own separate KPI instead
SELECT ROUND(AVG(price), 2) AS avg_price_paid
FROM workspace.gold.fact_games
WHERE is_free = FALSE;

-- % of catalog, not % of genre-tag rows — denominator is total games (27,075),
-- since genres are multi-label and tag-shares can't sum to 100%
SELECT genre, COUNT(*) AS game_count,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM workspace.gold.fact_games), 2) AS pct_of_catalog
FROM workspace.gold.game_genres
GROUP BY genre
ORDER BY game_count DESC
LIMIT 10;