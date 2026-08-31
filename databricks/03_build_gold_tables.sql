
CREATE OR REPLACE TABLE workspace.gold.fact_games AS
WITH platform_pivot AS (
  SELECT
    appid,
    MAX(CASE WHEN platform = 'windows' THEN 1 ELSE 0 END) = 1 AS has_windows,
    MAX(CASE WHEN platform = 'mac'     THEN 1 ELSE 0 END) = 1 AS has_mac,
    MAX(CASE WHEN platform = 'linux'   THEN 1 ELSE 0 END) = 1 AS has_linux
  FROM workspace.silver.game_platforms
  GROUP BY appid
)
SELECT
  g.appid,
  g.name,
  g.developer,
  g.publisher,
  g.release_date,
  g.release_year,
  g.english,
  g.required_age,
  g.price,
  CASE
    WHEN g.price = 0        THEN 'Free'
    WHEN g.price < 5         THEN 'Budget ($0.01-$4.99)'
    WHEN g.price < 15        THEN 'Standard ($5-$14.99)'
    WHEN g.price < 30        THEN 'Premium ($15-$29.99)'
    ELSE 'AAA ($30+)'
  END AS price_tier,
  g.is_free,
  g.positive_ratings,
  g.negative_ratings,
  (g.positive_ratings + g.negative_ratings) AS total_ratings,
  CASE WHEN (g.positive_ratings + g.negative_ratings) > 0
       THEN ROUND(g.positive_ratings / (g.positive_ratings + g.negative_ratings), 4)
       ELSE NULL
  END AS positive_review_rate,
  g.achievements,
  g.owners_min,
  g.owners_max,
  g.owners_avg,
  COALESCE(p.has_windows, FALSE) AS has_windows,
  COALESCE(p.has_mac, FALSE)     AS has_mac,
  COALESCE(p.has_linux, FALSE)   AS has_linux
FROM workspace.silver.games g
LEFT JOIN platform_pivot p ON g.appid = p.appid;


CREATE OR REPLACE TABLE workspace.gold.game_genres AS
SELECT sg.appid, sg.genre
FROM workspace.silver.game_genres sg
INNER JOIN workspace.gold.fact_games fg ON sg.appid = fg.appid;