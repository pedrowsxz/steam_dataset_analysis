SELECT ROUND(corr(price, positive_review_rate), 4) AS price_review_correlation
FROM workspace.gold.fact_games
WHERE positive_review_rate IS NOT NULL;

SELECT is_free, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM workspace.gold.fact_games
GROUP BY is_free;