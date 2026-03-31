-- 1. СИСТЕМНЫЕ ТАБЛИЦЫ 


-- 1.1 Версионирование схемы 
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,           
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,                          
    applied_by VARCHAR(100) DEFAULT CURRENT_USER, 
    script_name TEXT,                          
    checksum VARCHAR(64)                       
);

COMMENT ON TABLE schema_migrations IS 'История изменений структуры БД';
COMMENT ON COLUMN schema_migrations.version IS 'Семантическая версия или timestamp';

-- 1.2 Логирование ETL процессов
CREATE TABLE IF NOT EXISTS etl_execution_log (
    execution_id SERIAL PRIMARY KEY,
    etl_name VARCHAR(100) NOT NULL,             
    start_time TIMESTAMP NOT NULL,             
    end_time TIMESTAMP,                         
    status VARCHAR(20) NOT NULL,               
    rows_processed INT,                         
    rows_inserted INT,                          
    rows_updated INT,                           
    error_message TEXT,                         
    execution_time_ms INT,                     
    triggered_by VARCHAR(100) DEFAULT CURRENT_USER,
    metadata JSONB                              
);

COMMENT ON TABLE etl_execution_log IS 'Аудит всех процессов загрузки и трансформации данных';

-- 1.3 Контроль качества данных
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    metric_id SERIAL PRIMARY KEY,
    check_date DATE NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    expected_value NUMERIC,
    threshold NUMERIC,
    status VARCHAR(20),                        
    error_details TEXT,
    checked_by VARCHAR(100) DEFAULT CURRENT_USER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE data_quality_metrics IS 'Метрики качества данных для мониторинга';

-- 1.4 Справочник бизнес-параметров
CREATE TABLE IF NOT EXISTS business_config (
    config_key VARCHAR(50) PRIMARY KEY,
    config_value NUMERIC NOT NULL,
    description TEXT NOT NULL,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by VARCHAR(100) DEFAULT CURRENT_USER
);

COMMENT ON TABLE business_config IS 'Бизнес-параметры для аналитических расчетов';


INSERT INTO business_config (config_key, config_value, description) VALUES
    ('sma_short_period', 20, 'Короткий период для скользящей средней (быстрые тренды)'),
    ('sma_medium_period', 50, 'Средний период для скользящей средней (основной тренд)'),
    ('sma_long_period', 200, 'Длинный период для скользящей средней (долгосрочный тренд)'),
    ('z_score_high_threshold', 2.0, 'Порог для высокой волатильности (2 sigma)'),
    ('z_score_extreme_threshold', 3.0, 'Порог для экстремальной волатильности (3 sigma)'),
    ('risk_free_rate', 5.0, 'Безрисковая ставка для расчета Sharpe ratio (%)'),
    ('volatility_window_days', 252, 'Окно для расчета годовой волатильности (торговых дней)')
ON CONFLICT (config_key) DO NOTHING;


-- 2. ОСНОВНАЯ ТАБЛИЦА С ДАННЫМИ (с партиционированием)


-- Создаем основную таблицу с партиционированием по годам
CREATE TABLE IF NOT EXISTS google_stocks (
    date DATE NOT NULL,
    open_price NUMERIC(12,4),
    high NUMERIC(12,4),
    low NUMERIC(12,4),
    close_price NUMERIC(12,4),
    volume BIGINT,
    
    -- Производные поля для оптимизации (денормализация)
    daily_return_pct NUMERIC(10,4),
    price_range NUMERIC(12,4),
    year SMALLINT GENERATED ALWAYS AS (EXTRACT(YEAR FROM date)) STORED,
    month SMALLINT GENERATED ALWAYS AS (EXTRACT(MONTH FROM date)) STORED,
    quarter SMALLINT GENERATED ALWAYS AS (EXTRACT(QUARTER FROM date)) STORED,
    day_of_week SMALLINT GENERATED ALWAYS AS (EXTRACT(DOW FROM date)) STORED,
    week_num SMALLINT GENERATED ALWAYS AS (EXTRACT(WEEK FROM date)) STORED,
    
    -- Системные поля для аудита
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50) DEFAULT 'CSV_IMPORT',
    is_valid BOOLEAN DEFAULT TRUE,
    
    -- Констрейнты для обеспечения целостности данных
    CONSTRAINT pk_google_stocks PRIMARY KEY (date),
    CONSTRAINT valid_prices CHECK (
        high >= low AND 
        high >= open_price AND 
        high >= close_price AND
        open_price > 0 AND
        volume >= 0
    ),
    CONSTRAINT valid_daily_return CHECK (
        daily_return_pct IS NULL OR 
        daily_return_pct BETWEEN -50 AND 50
    )
) PARTITION BY RANGE (date);

COMMENT ON TABLE google_stocks IS 'Исторические данные по акциям Google с партиционированием по годам';
COMMENT ON COLUMN google_stocks.daily_return_pct IS 'Дневная доходность в процентах: (close/prev_close - 1)*100';
COMMENT ON COLUMN google_stocks.price_range IS 'Внутридневной размах цен: high - low';


-- 3. СОЗДАНИЕ ПАРТИЦИЙ


-- Создаем партиции для каждого года
CREATE TABLE google_stocks_2004_2010 PARTITION OF google_stocks
    FOR VALUES FROM ('2004-01-01') TO ('2011-01-01');

CREATE TABLE google_stocks_2011_2015 PARTITION OF google_stocks
    FOR VALUES FROM ('2011-01-01') TO ('2016-01-01');

CREATE TABLE google_stocks_2016_2020 PARTITION OF google_stocks
    FOR VALUES FROM ('2016-01-01') TO ('2021-01-01');

CREATE TABLE google_stocks_2021 PARTITION OF google_stocks
    FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');

CREATE TABLE google_stocks_2022 PARTITION OF google_stocks
    FOR VALUES FROM ('2022-01-01') TO ('2023-01-01');

CREATE TABLE google_stocks_2023 PARTITION OF google_stocks
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');

CREATE TABLE google_stocks_2024 PARTITION OF google_stocks
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE google_stocks_2025 PARTITION OF google_stocks
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE google_stocks_2026 PARTITION OF google_stocks
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- 4. Создаем индексы на партициях
CREATE INDEX idx_google_stocks_date ON google_stocks(date);
CREATE INDEX idx_google_stocks_year ON google_stocks((EXTRACT(YEAR FROM date)));

-- Просто посмотреть все таблицы, связанные с google_stocks
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE tablename LIKE 'google_stocks%'
ORDER BY tablename;


-- 4. ОПТИМИЗАЦИЯ: ИНДЕКСЫ ДЛЯ ЧАСТЫХ ЗАПРОСОВ


-- Составные индексы для ускорения аналитических запросов
CREATE INDEX IF NOT EXISTS idx_google_stocks_year_month ON google_stocks(year, month);
CREATE INDEX IF NOT EXISTS idx_google_stocks_volume ON google_stocks(volume DESC) WHERE volume IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_google_stocks_daily_return ON google_stocks(daily_return_pct DESC) WHERE daily_return_pct IS NOT NULL;

-- Индекс для полнотекстового поиска по датам
CREATE INDEX IF NOT EXISTS idx_google_stocks_date_range ON google_stocks(date) INCLUDE (close_price, volume);


-- 5. ТРИГГЕР ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ updated_at


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_google_stocks_updated_at
    BEFORE UPDATE ON google_stocks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- 6. СЛОЙ АГРЕГАЦИИ: МАТЕРИАЛИЗОВАННЫЕ ПРЕДСТАВЛЕНИЯ


-- Материализованное представление для ежедневных метрик
DROP MATERIALIZED VIEW IF EXISTS mv_daily_metrics CASCADE;
CREATE MATERIALIZED VIEW mv_daily_metrics AS
WITH 
-- Базовые расчеты с оконными функциями
base_metrics AS (
    SELECT 
        date,
        close_price,
        volume,
        daily_return_pct,
        price_range,
        year,
        month,
        quarter,
        day_of_week,
        week_num,
        
        -- Технические индикаторы
        ROUND(((high - low) / NULLIF(open_price, 0) * 100)::NUMERIC, 2) AS intraday_volatility_pct,
        
        -- Множественные скользящие средние для разных стратегий
        AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS sma_20,
        AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS sma_50,
        AVG(close_price) OVER (ORDER BY date ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) AS sma_200,
        
        -- Экспоненциальная скользящая средняя (более чувствительная к изменениям)
        FIRST_VALUE(close_price) OVER (ORDER BY date) AS base_price,
        
$$$$$$$        -- Кумулятивные метрики 
        MAX(close_price) OVER (ORDER BY date) AS historical_max,
        MIN(close_price) OVER (ORDER BY date) AS historical_min,
        SUM(volume) OVER (ORDER BY date) AS cumulative_volume
    FROM google_stocks
    WHERE is_valid = TRUE
),

-- Добавляем статистические метрики для Z-Score
stats_calculations AS (
    SELECT 
        *,
        -- Статистики для Z-Score (глобальные, не оконные)
        (SELECT AVG(intraday_volatility_pct) FROM base_metrics) AS global_avg_volatility,
        (SELECT STDDEV(intraday_volatility_pct) FROM base_metrics) AS global_stddev_volatility,
        
        -- Скользящая волатильность (для более точной оценки)
        STDDEV(daily_return_pct) OVER (ORDER BY date ROWS BETWEEN 19 PRECEDING AND CURRENT ROW) AS rolling_volatility_20d
    FROM base_metrics
)

SELECT 
    date,
    close_price,
    volume,
    daily_return_pct,
    intraday_volatility_pct,
    
    -- Скользящие средние
    ROUND(sma_20, 2) AS sma_20,
    ROUND(sma_50, 2) AS sma_50,
    ROUND(sma_200, 2) AS sma_200,
    
    -- Трендовые индикаторы
    CASE 
        WHEN close_price > sma_50 AND sma_50 > sma_200 THEN 'STRONG_BULLISH'    
        WHEN close_price > sma_50 THEN 'BULLISH'                                  
        WHEN close_price < sma_50 AND sma_50 < sma_200 THEN 'STRONG_BEARISH'     
        WHEN close_price < sma_50 THEN 'BEARISH'                                 
        ELSE 'NEUTRAL'                                                           
    END AS market_trend,
    
    -- Относительная сила цены
    ROUND(((close_price - sma_50) / NULLIF(sma_50, 0) * 100)::NUMERIC, 2) AS price_vs_sma50_pct,
    
    -- Z-Score для выявления аномалий
    ROUND((intraday_volatility_pct - global_avg_volatility) / 
          NULLIF(global_stddev_volatility, 0), 2) AS volatility_z_score,
    
    -- Классификация риска (используем параметры из конфига)
    CASE 
        WHEN (intraday_volatility_pct - global_avg_volatility) / NULLIF(global_stddev_volatility, 0) > 
             (SELECT config_value FROM business_config WHERE config_key = 'z_score_extreme_threshold')
        THEN 'EXTREME_ANOMALY'
        WHEN (intraday_volatility_pct - global_avg_volatility) / NULLIF(global_stddev_volatility, 0) > 
             (SELECT config_value FROM business_config WHERE config_key = 'z_score_high_threshold')
        THEN 'HIGH_RISK'
        WHEN (intraday_volatility_pct - global_avg_volatility) / NULLIF(global_stddev_volatility, 0) < -1.5
        THEN 'LOW_VOLATILITY'
        ELSE 'NORMAL'
    END AS risk_category,
    
    -- Инвестиционные метрики
    ROUND(((close_price / base_price) - 1) * 100, 2) AS cumulative_return_pct,
    ROUND((close_price / historical_max * 100)::NUMERIC, 2) AS pct_of_historical_high,
    ROUND((close_price / historical_min * 100)::NUMERIC, 2) AS pct_of_historical_low,
    
    -- Волатильность (годовая)
    ROUND(rolling_volatility_20d * SQRT(252), 2) AS annualized_volatility_pct,
    
    -- Атрибуты для аналитики
    year, 
    month, 
    quarter, 
    day_of_week,
    week_num
    
FROM stats_calculations;

-- Создаем индексы для материализованного представления
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_metrics_date ON mv_daily_metrics(date);
CREATE INDEX IF NOT EXISTS idx_mv_daily_metrics_risk ON mv_daily_metrics(risk_category);
CREATE INDEX IF NOT EXISTS idx_mv_daily_metrics_trend ON mv_daily_metrics(market_trend);

COMMENT ON MATERIALIZED VIEW mv_daily_metrics IS 'Ежедневные аналитические метрики для инвестиционного анализа';


-- 7. АГРЕГИРОВАННЫЕ ВИЗУАЛИЗАЦИИ ДЛЯ DASHBOARD


-- Ежемесячные агрегаты для дашбордов
DROP MATERIALIZED VIEW IF EXISTS mv_monthly_aggregates;
CREATE MATERIALIZED VIEW mv_monthly_aggregates AS
SELECT 
    year,
    month,
    TO_DATE(year || '-' || month || '-01', 'YYYY-MM-DD') AS month_start,
    
    -- Ценовые метрики
    ROUND(AVG(close_price), 2) AS avg_price,
    ROUND(MIN(close_price), 2) AS min_price,
    ROUND(MAX(close_price), 2) AS max_price,
    ROUND(STDDEV(close_price), 2) AS price_stddev,
    
    -- Доходность
    ROUND(AVG(daily_return_pct), 4) AS avg_daily_return,
    ROUND(SUM(daily_return_pct), 2) AS monthly_return_pct,
    ROUND(STDDEV(daily_return_pct), 4) AS volatility_stddev,
    
    -- Объемы
    SUM(volume) / 1000000 AS total_volume_millions,
    ROUND(AVG(volume) / 1000000, 2) AS avg_daily_volume_millions,
    
    -- Волатильность
    ROUND(AVG(intraday_volatility_pct), 2) AS avg_intraday_volatility,
    ROUND(MAX(intraday_volatility_pct), 2) AS max_intraday_volatility,
    
    -- Статистика дней
    COUNT(*) AS trading_days,
    COUNT(CASE WHEN daily_return_pct > 0 THEN 1 END) AS positive_days,
    COUNT(CASE WHEN daily_return_pct < 0 THEN 1 END) AS negative_days,
    ROUND(COUNT(CASE WHEN daily_return_pct > 0 THEN 1 END) * 100.0 / COUNT(*), 1) AS win_rate_pct,
    
    -- Риск-метрики
    COUNT(CASE WHEN risk_category IN ('HIGH_RISK', 'EXTREME_ANOMALY') THEN 1 END) AS high_risk_days,
    
    -- Трендовая статистика
    MODE() WITHIN GROUP (ORDER BY market_trend) AS dominant_trend
    
FROM mv_daily_metrics
GROUP BY year, month
ORDER BY year DESC, month DESC;

CREATE INDEX IF NOT EXISTS idx_mv_monthly_year ON mv_monthly_aggregates(year, month);


-- 8. ФУНКЦИЯ ДЛЯ РАСЧЕТА SHARPE RATIO (Key Performance Indicator)


CREATE OR REPLACE FUNCTION calculate_sharpe_ratio(
    p_start_date DATE,
    p_end_date DATE,
    p_annualize BOOLEAN DEFAULT TRUE
)
RETURNS NUMERIC
LANGUAGE plpgsql
AS $$
DECLARE
    v_avg_return NUMERIC;
    v_stddev_return NUMERIC;
    v_risk_free_rate NUMERIC;
    v_sharpe_ratio NUMERIC;
    v_trading_days INT;
BEGIN
    -- Получаем безрисковую ставку из конфига
    SELECT config_value INTO v_risk_free_rate 
    FROM business_config 
    WHERE config_key = 'risk_free_rate';
    
    -- Рассчитываем среднюю доходность и волатильность
    SELECT 
        AVG(daily_return_pct),
        STDDEV(daily_return_pct),
        COUNT(*)
    INTO v_avg_return, v_stddev_return, v_trading_days
    FROM mv_daily_metrics
    WHERE date BETWEEN p_start_date AND p_end_date
        AND daily_return_pct IS NOT NULL;
    
    -- Sharpe Ratio
    IF v_stddev_return > 0 THEN
        v_sharpe_ratio := (v_avg_return - v_risk_free_rate / 252) / v_stddev_return;
        
        -- Аннуализируем (умножаем на корень из количества торговых дней в году)
        IF p_annualize THEN
            v_sharpe_ratio := v_sharpe_ratio * SQRT(252);
        END IF;
    ELSE
        v_sharpe_ratio := NULL;
    END IF;
    
    RETURN ROUND(v_sharpe_ratio, 4);
END;
$$;

COMMENT ON FUNCTION calculate_sharpe_ratio IS 'Расчет коэффициента Шарпа - ключевая метрика risk-adjusted return';


-- ETL PIPELINE: Загрузка данных с логированием и обработкой ошибок


-- 1. ФУНКЦИЯ ЗАГРУЗКИ ДАННЫХ
CREATE OR REPLACE FUNCTION etl_load_google_stocks(
    p_file_path TEXT,
    p_batch_id VARCHAR(100) DEFAULT NULL
)
RETURNS TABLE(
    execution_status VARCHAR(20),
    rows_loaded INT,
    error_message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_execution_id INT;
    v_start_time TIMESTAMP;
    v_row_count INT;
    v_inserted INT := 0;
    v_updated INT := 0;
    v_batch_id VARCHAR(100);
BEGIN
    -- Генерируем batch_id, если не передан
    v_batch_id := COALESCE(p_batch_id, 'BATCH_' || TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDD_HH24MISS'));
    v_start_time := CURRENT_TIMESTAMP;
    
    -- Логируем начало выполнения
    INSERT INTO etl_execution_log (etl_name, start_time, status, triggered_by, metadata)
    VALUES ('LOAD_GOOGLE_STOCKS', v_start_time, 'RUNNING', CURRENT_USER, 
            jsonb_build_object('file_path', p_file_path, 'batch_id', v_batch_id))
    RETURNING execution_id INTO v_execution_id;
    
    -- Основная логика загрузки с обработкой ошибок
    BEGIN
        -- Создаем временную таблицу для загрузки
        CREATE TEMP TABLE temp_google_stocks_load (
            date DATE,
            open_price NUMERIC(12,4),
            high NUMERIC(12,4),
            low NUMERIC(12,4),
            close_price NUMERIC(12,4),
            volume BIGINT
        );
        
        -- Выполняем COPY с обработкой ошибок формата
        BEGIN
            EXECUTE format('
                COPY temp_google_stocks_load (date, open_price, high, low, close_price, volume)
                FROM %L 
                DELIMITER '','' 
                CSV HEADER
                NULL ''NULL''
            ', p_file_path);
            
            GET DIAGNOSTICS v_row_count = ROW_COUNT;
            
        EXCEPTION WHEN OTHERS THEN
            -- Логируем ошибку COPY и пробрасываем дальше
            INSERT INTO etl_execution_log (execution_id, error_message)
            VALUES (v_execution_id, 'COPY failed: ' || SQLERRM);
            RAISE;
        END;
        
        -- Валидация загруженных данных
        IF v_row_count = 0 THEN
            RAISE EXCEPTION 'No data loaded from file: %', p_file_path;
        END IF;
        
        -- Проверяем дубликаты
        WITH duplicates AS (
            SELECT date, COUNT(*)
            FROM temp_google_stocks_load
            GROUP BY date
            HAVING COUNT(*) > 1
        )
        SELECT COUNT(*) INTO v_row_count FROM duplicates;
        
        IF v_row_count > 0 THEN
            RAISE WARNING 'Found % duplicate dates in source file', v_row_count;
        END IF;
        
        -- Выполняем UPSERT (INSERT + UPDATE)
        WITH upsert_data AS (
            INSERT INTO google_stocks (
                date, open_price, high, low, close_price, volume,
                daily_return_pct, price_range, data_source
            )
            SELECT 
                t.date,
                t.open_price,
                t.high,
                t.low,
                t.close_price,
                t.volume,
                -- Рассчитываем дневную доходность (используем LAG)
                ROUND(((t.close_price - LAG(t.close_price) OVER (ORDER BY t.date)) / 
                       NULLIF(LAG(t.close_price) OVER (ORDER BY t.date), 0) * 100)::NUMERIC, 4),
                t.high - t.low,
                'CSV_IMPORT'
            FROM temp_google_stocks_load t
            ON CONFLICT (date) DO UPDATE SET
                open_price = EXCLUDED.open_price,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close_price = EXCLUDED.close_price,
                volume = EXCLUDED.volume,
                daily_return_pct = EXCLUDED.daily_return_pct,
                price_range = EXCLUDED.price_range,
                updated_at = CURRENT_TIMESTAMP,
                data_source = EXCLUDED.data_source
            RETURNING 
                CASE 
                    WHEN xmax = 0 THEN 'INSERTED' 
                    ELSE 'UPDATED' 
                END AS operation,
                1 AS cnt
        )
        SELECT 
            COUNT(*) FILTER (WHERE operation = 'INSERTED'),
            COUNT(*) FILTER (WHERE operation = 'UPDATED')
        INTO v_inserted, v_updated
        FROM upsert_data;
        
        -- Обновляем материализованное представление
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_metrics;
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_aggregates;
        
        -- Логируем успешное завершение
        UPDATE etl_execution_log 
        SET 
            end_time = CURRENT_TIMESTAMP,
            status = 'SUCCESS',
            rows_processed = v_inserted + v_updated,
            rows_inserted = v_inserted,
            rows_updated = v_updated,
            execution_time_ms = EXTRACT(MILLISECONDS FROM (CURRENT_TIMESTAMP - v_start_time))
        WHERE execution_id = v_execution_id;
        
        -- Возвращаем результат
        RETURN QUERY SELECT 
            'SUCCESS'::VARCHAR(20), 
            (v_inserted + v_updated)::INT, 
            NULL::TEXT;
            
    EXCEPTION WHEN OTHERS THEN
        -- Логируем ошибку
        UPDATE etl_execution_log 
        SET 
            end_time = CURRENT_TIMESTAMP,
            status = 'FAILED',
            error_message = SQLERRM,
            execution_time_ms = EXTRACT(MILLISECONDS FROM (CURRENT_TIMESTAMP - v_start_time))
        WHERE execution_id = v_execution_id;
        
        -- Возвращаем ошибку
        RETURN QUERY SELECT 
            'FAILED'::VARCHAR(20), 
            0::INT, 
            SQLERRM::TEXT;
    END;
    
    -- Очищаем временную таблицу
    DROP TABLE IF EXISTS temp_google_stocks_load;
END;
$$;

COMMENT ON FUNCTION etl_load_google_stocks IS 'Production ETL для загрузки данных по акциям с логированием и обработкой ошибок';


-- 2. ПРИМЕР ВЫЗОВА ФУНКЦИИ


-- Выполняем загрузку
SELECT * FROM etl_load_google_stocks('/data/google_stocks_2024.csv', 'BATCH_2024_ANNUAL');


-- 3. ФУНКЦИЯ ДЛЯ ИНКРЕМЕНТАЛЬНОЙ ЗАГРУЗКИ


CREATE OR REPLACE FUNCTION etl_incremental_load(
    p_new_data_path TEXT
)
RETURNS TABLE(
    status VARCHAR(20),
    new_records INT,
    message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_last_date DATE;
    v_new_count INT;
BEGIN
    -- Получаем последнюю дату в основной таблице
    SELECT MAX(date) INTO v_last_date FROM google_stocks;
    
    -- Загружаем только новые данные
    CREATE TEMP TABLE temp_new_data AS
    SELECT * FROM etl_load_google_stocks(p_new_data_path, NULL);
    
    -- Проверяем, что даты в загрузке новее существующих
    SELECT COUNT(*) INTO v_new_count 
    FROM temp_new_data 
    WHERE date > v_last_date;
    
    IF v_new_count = 0 THEN
        RETURN QUERY SELECT 'NO_NEW_DATA'::VARCHAR(20), 0::INT, 'All data is already loaded'::TEXT;
        RETURN;
    END IF;
    
    -- Выполняем загрузку
    RETURN QUERY SELECT * FROM etl_load_google_stocks(p_new_data_path, 'INCREMENTAL_' || TO_CHAR(CURRENT_TIMESTAMP, 'YYYYMMDD'));
    
    DROP TABLE temp_new_data;
END;
$$;
