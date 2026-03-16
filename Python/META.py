import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
from scipy import stats
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

print("Загрузка данных...")

df = pd.read_csv('META stocks.csv')

print("Даннные загруженны...")
print(df.head())

df.columns = df.columns.str.lower()

df['date'] = pd.to_datetime(df['date'])

df = df.sort_values(by='date')

# РАСЧЕТ БАЗОВЫХ МЕТРИК И ИНДИКАТОРОВ

# Процентное изменение цены закрытия - показывает дневную доходность
df['return'] = df['close'].pct_change()
# Логарифмическая доходность
df['log_return'] = np.log(df["close"] / df["close"].shift(1))
# Доходность последнего дня в %
last_return = df['return'].iloc[-1] * 100
# Максимальный дневной рост
day_max_revenue = df.loc[df['return'].idxmax(), "return"] * 100
# Максимальное дневное падение
day_min_revenue = df.loc[df['return'].idxmin(), "return"] * 100
# Средняя цена за весь период
df["average_price"] = df["close"].mean()
# Достигла ли цена новых максимумов
df["recovered"] = df["close"] >= df["close"].cummax()
# Стандартное отклонение доходности (риск) 
standart_deviation = df['return'].std() * 100
# Скользящая волатильность (20 дней)
df['volatility_20d'] = df['return'].rolling(window=20).std() * 100
# MA50 - средняя цена за последние 50 дней 
df['ma50'] = df['close'].rolling(window=50).mean()
# MA200 - средняя цена за последние 200 дней 
df['ma200'] = df['close'].rolling(window=200).mean()

# ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ (ДЛЯ ТЕХНИЧЕСКОГО АНАЛИЗА)

def calculate_rsi(data, window=14):
    delta = data.diff() 
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

df['rsi'] = calculate_rsi(df['close'])

df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
df['macd'] = df['ema12'] - df['ema26']
df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
df['mac_histogram'] = df['macd'] - df['signal']  

df['bb_middle'] = df['close'].rolling(window=20).mean()
df['bb_upper'] = df['bb_middle'] + (df['close'].rolling(window=20).std() * 2)
df['bb_lower'] = df['bb_middle'] - (df['close'].rolling(window=20).std() * 2)

stat, p_value = stats.shapiro(df['return'].dropna())
normality_status = "Нормальное" if p_value > 0.05 else "Не нормальное"

autocorrelation = df['return'].autocorr()

# ТРЕНДОВЫЙ АНАЛИЗ С МАШИННЫМ ОБУЧЕНИЕМ

x = np.arange(len(df)).reshape(-1, 1)
y = df['close'].values.reshape(-1, 1)

model = LinearRegression()
model.fit(x, y)

trend_slope = model.coef_[0][0]
trend_direction = "Восходящий" if trend_slope > 0 else "Нисходящий"

# АНАЛИЗ СЕЗОННОСТИ
df['day_of_week'] = df['date'].dt.day_name()
df['month'] = df['date'].dt.month

daily_returns = df.groupby('day_of_week')['return'].mean() * 100

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
daily_returns = daily_returns.reindex(day_order)

best_day = daily_returns.idxmax()
worst_day = daily_returns.idxmin()

# РАСЧЕТ РИСК-МЕТРИК

current_price = df['close'].iloc[-1]
ma200_last = df['ma200'].iloc[-1]

trend_status = "ВЫШЕ средней" if current_price > ma200_last else "НИЖЕ средней"
rsi_last = df['rsi'].iloc[-1]

cumulative_max = df['close'].cummax()
drawdown = (df['close'] - cumulative_max) / cumulative_max
max_drawdown = drawdown.min() * 100  

annual_volatility = df['return'].std() * (252**0.5) * 100

sharpe_ratio = (df['return'].mean() / df['return'].std()) * (252**0.5)

# ВИЗУАЛИЗАЦИЯ ДАННЫХ

sns.set_theme(style="white")
plt.rcParams['font.family'] = 'sans-serif'

fig = plt.figure(figsize=(16, 22))

ax1 = plt.subplot(7, 1, 1)  
ax2 = plt.subplot(7, 1, 2)  
ax3 = plt.subplot(7, 1, 3)  
ax4 = plt.subplot(7, 1, 4)  
ax5 = plt.subplot(7, 1, 5)  
ax6 = plt.subplot(7, 1, 6)  

plt.subplots_adjust(hspace=0.4, top=0.97, bottom=0.05, left=0.08, right=0.95)

# ===== ГРАФИК 1: Цена и скользящие средние =====

ax1.plot(df["date"], df["close"], linewidth=2, color='#1f77b4', label='Цена закрытия')
ax1.plot(df["date"], df["ma50"], linewidth=1.5, color='#ff7f0e', label='MA50', alpha=0.8)
ax1.plot(df["date"], df["ma200"], linewidth=1.5, color='#d62728', label='MA200', alpha=0.8)
ax1.fill_between(df["date"], df["close"], alpha=0.1, color='#1f77b4')
ax1.set_ylabel("Цена ($)", fontsize=11)
ax1.legend(loc='upper left', fontsize=8, frameon=True, fancybox=True, shadow=True)
ax1.grid(True, alpha=0.3, linestyle='--')
ax1.tick_params(axis='x', labelsize=8)
ax1.tick_params(axis='y', labelsize=8)

# ===== ГРАФИК 2: RSI =====

ax2.plot(df["date"], df["rsi"], linewidth=1.8, color='#9467bd', label='RSI')
ax2.axhline(y=70, color='#d62728', linestyle='--', alpha=0.7, linewidth=1, label='Перекуплен (70)')
ax2.axhline(y=30, color='#2ca02c', linestyle='--', alpha=0.7, linewidth=1, label='Перепродан (30)')
ax2.fill_between(df["date"], 70, 30, alpha=0.1, color='gray')
ax2.set_ylabel("RSI", fontsize=11)
ax2.set_ylim(0, 100)
ax2.legend(loc='upper right', fontsize=8, ncol=3, frameon=True)
ax2.grid(True, alpha=0.3, linestyle='--')
ax2.tick_params(axis='x', labelsize=8)
ax2.tick_params(axis='y', labelsize=8)

# ===== ГРАФИК 3: MACD =====

ax3.plot(df["date"], df["macd"], linewidth=1.5, color='#2c3e50', label='MACD')
ax3.plot(df["date"], df["signal"], linewidth=1.5, color='#e67e22', label='Signal')
ax3.bar(df["date"], df["mac_histogram"], color='#7f8c8d', alpha=0.3, label='Histogram', width=1)  
ax3.set_ylabel("MACD", fontsize=11)
ax3.legend(loc='upper right', fontsize=8, ncol=3, frameon=True)
ax3.grid(True, alpha=0.3, linestyle='--')
ax3.axhline(y=0, color='black', linewidth=0.5, alpha=0.5)
ax3.tick_params(axis='x', labelsize=8)
ax3.tick_params(axis='y', labelsize=8)

# ===== ГРАФИК 4: Bollinger Bands =====

ax4.plot(df["date"], df["close"], linewidth=1.8, color='#1f77b4', label='Цена')
ax4.plot(df["date"], df["bb_upper"], linewidth=1, color='#d62728', linestyle='--', alpha=0.7, label='Верхняя полоса (+2σ)')
ax4.plot(df["date"], df["bb_middle"], linewidth=1, color='#ff7f0e', alpha=0.7, label='Средняя (MA20)')
ax4.plot(df["date"], df["bb_lower"], linewidth=1, color='#2ca02c', linestyle='--', alpha=0.7, label='Нижняя полоса (-2σ)')
ax4.fill_between(df["date"], df["bb_upper"], df["bb_lower"], alpha=0.1, color='gray')
ax4.set_ylabel("Цена ($)", fontsize=11)
ax4.legend(loc='upper left', fontsize=8, ncol=2, frameon=True)
ax4.grid(True, alpha=0.3, linestyle='--')
ax4.tick_params(axis='x', labelsize=8)
ax4.tick_params(axis='y', labelsize=8)

# ===== ГРАФИК 5: Доходность по дням недели =====

colors_days = ['#2ca02c' if x >= 0 else '#d62728' for x in daily_returns.values]
bars = ax5.bar(daily_returns.index, daily_returns.values, color=colors_days, alpha=0.7, edgecolor='white', linewidth=1)
ax5.set_ylabel("Доходность (%)", fontsize=11)
ax5.set_xlabel("День недели", fontsize=11)
ax5.tick_params(axis='x', rotation=45, labelsize=8)
ax5.tick_params(axis='y', labelsize=8)
ax5.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax5.grid(True, alpha=0.3, axis='y', linestyle='--')

# ===== ГРАФИК 6: Объемы с цветовой кодировкой =====

colors_volume = ['#2ca02c' if r >= 0 else '#d62728' for r in df["return"].fillna(0)]  
ax6.bar(df['date'], df['volume'], color=colors_volume, alpha=0.6, width=1)
ax6.set_xlabel("Дата", fontsize=11)
ax6.set_ylabel("Объем", fontsize=11)
ax6.grid(True, alpha=0.3, axis='y', linestyle='--')
ax6.tick_params(axis='x', labelsize=8)
ax6.tick_params(axis='y', labelsize=8)

for bar in bars:
    height = bar.get_height()
    if height >= 0:
        ax5.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                 f'{height:+.2f}%', ha='center', va='bottom', fontsize=8, fontweight='bold')
    else:
        ax5.text(bar.get_x() + bar.get_width()/2., height - 0.08,
                 f'{height:+.2f}%', ha='center', va='top', fontsize=8, fontweight='bold')

ax6.ticklabel_format(axis='y', style='scientific', scilimits=(6,6))

green_patch = mpatches.Patch(color='#2ca02c', alpha=0.6, label='📈 Рост цены')
red_patch = mpatches.Patch(color='#d62728', alpha=0.6, label='📉 Падение цены')
ax6.legend(handles=[green_patch, red_patch], loc='upper left', fontsize=7, frameon=True)

for ax in [ax1, ax2, ax3, ax4, ax5, ax6]:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#bdc3c7')
    ax.spines['bottom'].set_color('#bdc3c7')
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)

plt.show()

print("\n" + "="*60)
print("     РАСШИРЕННЫЙ АНАЛИЗ АКЦИЙ META")
print("="*60)

print("\n📊 БАЗОВЫЕ МЕТРИКИ:")
print(f"  • Текущая цена: ${current_price:.2f}")
print(f"  • Статус MA200: {trend_status} (MA200 = ${ma200_last:.2f})")
print(f"  • RSI (14): {rsi_last:.1f}")
print(f"  • Доходность последней сессии: {last_return:+.2f}%")

print("\n📈 ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ:")
print(f"  • MACD: {df['macd'].iloc[-1]:.2f}")
print(f"  • Сигнал MACD: {df['signal'].iloc[-1]:.2f}")
print(f"  • Bollinger Bands: [{df['bb_lower'].iloc[-1]:.2f} | {df['bb_middle'].iloc[-1]:.2f} | {df['bb_upper'].iloc[-1]:.2f}]")

print("\n📉 РИСК-МЕТРИКИ:")
print(f"  • Годовая волатильность: {annual_volatility:.2f}%")
print(f"  • Максимальная просадка: {max_drawdown:.2f}%")
print(f"  • Коэффициент Шарпа: {sharpe_ratio:.2f}")

print("\n📅 СЕЗОННЫЕ ПАТТЕРНЫ:")
print(f"  • Лучший день для торговли: {best_day} ({daily_returns[best_day]:+.2f}%)")
print(f"  • Худший день для торговли: {worst_day} ({daily_returns[worst_day]:+.2f}%)")

print("\n🔬 СТАТИСТИЧЕСКИЙ АНАЛИЗ:")
print(f"  • Распределение доходностей: {normality_status}")
print(f"  • Автокорреляция: {autocorrelation:.3f}")

# Интерпретируем результаты статистических тестов
if autocorrelation > 0.1:
    print(f"    → Есть небольшая зависимость от предыдущего дня")
elif autocorrelation < -0.1:
    print(f"    → Есть небольшая обратная зависимость от предыдущего дня")
else:
    print(f"    → Доходность близка к случайному блужданию")
