WITH yearly AS (
  SELECT release_year, COUNT(*) AS releases
  FROM workspace.gold.fact_games
  WHERE release_year IS NOT NULL
  GROUP BY release_year
)
SELECT release_year, releases,
       LAG(releases) OVER (ORDER BY release_year) AS prior_year,
       ROUND(100.0 * (releases - LAG(releases) OVER (ORDER BY release_year))
             / NULLIF(LAG(releases) OVER (ORDER BY release_year), 0), 1) AS yoy_growth_pct
FROM yearly
ORDER BY release_year;

SELECT publisher, COUNT(*) AS games,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM workspace.gold.fact_games), 2) AS pct_of_catalog
FROM workspace.gold.fact_games
GROUP BY publisher
ORDER BY games DESC
LIMIT 10;