# Data Analytics Portfolio
# Chocolate Sales & Marketing Performance

Репозиторий содержит комплексные решения для анализа бизнес-показателей: от глубокой сегментации базы данных на SQL до визуализации маркетинговых KPI на Python.

## SQL Аналитика продаж (Chocolate Sales)
## Цель: Трансформация «сырых» транзакций в стратегические инсайты для управления ассортиментом.

Ключевой функционал:
Deep Categorization: Автоматическая сегментация товаров по типам (Dark, White, Nuts, etc.) через паттерны в CASE WHEN.
RFM-сегментация: Классификация стран на группы (Champions, At Risk, Big Spenders) с использованием статистической функции NTILE(3).
Data Integrity: Скрипт автоматической проверки финансовых аномалий (поиск расхождений между выручкой и ценой/количеством).
Time Series: Расчет скользящего среднего (Moving Average) за 7 дней для сглаживания сезонных колебаний.

## Marketing Dashboard (Python)
## Цель: Автоматизация отчетности по рекламным кампаниям и расчет эффективности затрат.

Ключевой функционал:
Расчет KPI: Автоматический расчет Spend, Revenue, ROI и CPL (Cost Per Lead).
Cross-Platform Analysis: Сравнение прибыльности различных рекламных площадок.
Data Visualization: Построение графиков распределения прибыли и динамики затрат через Seaborn и Matplotlib.

## 🛠 Стек:
- Python
- pandas
- matplotlib
- seaborn

## Общий технологический стек
Базы данных: PostgreSQL
Аналитика: RFM-моделирование, маркетинговые метрики (ROI, CPL).
Разработка: Python 3.x, Jupyter Notebooks.

## ▶ Запуск:
pip install pandas matplotlib seaborn openpyxl  
python analysis.py
python analysis2.py


Для SQL: Импортируйте ваш датасет в таблицу chocolate_sales и запустите файлы из папки /PSQL Analysis.

## 📷 Preview
[Dashboard](analysisphoto.png)
[Dashboard_2](Dashboard2.png)
