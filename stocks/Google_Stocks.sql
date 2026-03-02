
-- 1. СОЗДАНИЕ СТРУКТУРЫ ТАБЛИЦЫ
-- Удаляем таблицу, если она уже существует 
DROP TABLE IF EXISTS google_stocks;

CREATE TABLE google_stocks (
    date DATE PRIMARY KEY,
    open_price NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close_price NUMERIC,
    volume BIGINT,
    daily_return_pct NUMERIC,
    price_range NUMERIC,
    year INT,
    month INT,
    quarter INT,
    day_of_week VARCHAR(15)
);

-- 2. ЗАГРУЗКА ДАННЫХ
COPY google_stocks FROM '/absolute/path/to/your/GOOGL_stock_data.csv' 
DELIMITER ',' 
CSV HEADER;

-- 3. КОМПЛЕКСНЫЙ АНАЛИЗ (CORE ANALYTICS)
-- Используем CTE (Common Table Expressions) для чистоты кода и читаемости
WITH calculated_metrics AS (
    SELECT 
        date,
        close_price,
        volume,
        -- Расчет внутридневной волатильности (размах цен в %)
        ROUND(((high - low) / open_price * 100), 2) AS intraday_volatility_pct,
        -- Определение цены IPO (самая первая запись)
        FIRST_VALUE(close_price) OVER(ORDER BY date) AS ipo_price,
        -- 50-дневная скользящая средняя (технический индикатор тренда)
        AVG(close_price) OVER(ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS sma_50
    FROM google_stocks
),
statistical_base AS (
    SELECT 
        *,
        -- Накопительная доходность (рост инвестиции в %)
        ROUND(((close_price / ipo_price) - 1) * 100, 2) AS total_return_pct,
        -- Средняя волатильность и стандартное отклонение для расчета Z-Score
        AVG(intraday_volatility_pct) OVER() AS avg_vol,
        STDDEV(intraday_volatility_pct) OVER() AS stddev_vol
    FROM calculated_metrics
)
SELECT 
    date,
    close_price,
    total_return_pct,
    ROUND(sma_50, 2) AS sma_50_trend,
    intraday_volatility_pct,
    -- Z-Score: показывает, на сколько стандартных отклонений текущий день аномальнее нормы
    ROUND((intraday_volatility_pct - avg_vol) / stddev_vol, 2) AS volatility_z_score,
    -- Классификация рисков на основе Z-Score
    CASE 
        WHEN (intraday_volatility_pct - avg_vol) / stddev_vol > 3 THEN '🔥 EXTREME ANOMALY'
        WHEN (intraday_volatility_pct - avg_vol) / stddev_vol > 2 THEN '⚠️ HIGH RISK'
        ELSE '✅ NORMAL'
    END AS risk_status
FROM statistical_base
ORDER BY date DESC;


-- Топ-10 самых волатильных (аномальных) дней в истории
SELECT 
    date, 
    open_price, 
    close_price, 
    ROUND(((high - low) / open_price * 100), 2) AS max_spike_pct
FROM google_stocks
ORDER BY max_spike_pct DESC
LIMIT 10;

-- Среднегодовая статистика: риск и доходность
SELECT 
    year,
    ROUND(AVG(close_price), 2) AS avg_price,
    ROUND(AVG(daily_return_pct), 4) AS avg_daily_return,
    SUM(volume) AS total_annual_volume
FROM google_stocks
GROUP BY year
ORDER BY year;

SELECT 
    (SELECT total_return_pct FROM risk_scoring ORDER BY date DESC LIMIT 1) AS final_return_pct,
    COUNT(*) AS total_days,
    COUNT(*) FILTER (WHERE z_score <= 2) AS normal_days,
    COUNT(*) FILTER (WHERE z_score > 2 AND z_score <= 3) AS high_risk_days,
    COUNT(*) FILTER (WHERE z_score > 3) AS extreme_anomaly_days,
    ROUND(AVG(intraday_volatility_pct), 2) AS average_volatility_pct
FROM risk_scoring;
