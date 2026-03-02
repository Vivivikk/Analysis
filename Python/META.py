import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches

print("Загрузка данных...")

df = pd.read_csv('META stocks.csv')

print("Данные загружены...")

print(df.head())

df.columns = (
  df.columns.str.lower()
)

df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')

print("Columns: ")
print(df.columns)

# Метрики
df["return"] = df["close"].pct_change()
last_return = df["return"].iloc[-1] * 100
day_max_revenue = df.loc[df["return"].idxmax(), "return"]
day_min_revenue = df.loc[df["return"].idxmin(), "return"]
df["average_price"] =df["close"].mean()
df["recovered"] = df["close"] >= df["close"].cummax()
standard_deviation = df["return"].std() * 100
df["rolling_std"] = df["return"].rolling(window=20).std() * 100
df['ma50'] = df['close'].rolling(window=50).mean()
df['ma200'] = df['close'].rolling(window=200).mean()
cumulative_max = df['close'].cummax()
drawdown = (df['close'] - cumulative_max) / cumulative_max
max_drawdown = drawdown.min() * 100
annual_volatility = df['return'].std() * (252**0.5) * 100
sharpe_ratio = (df['return'].mean() / df['return'].std()) * (252**0.5)

current_price = df['close'].iloc[-1]
ma200_last = df['ma200'].iloc[-1]
trend_status = "ВЫШЕ средней " if current_price > ma200_last else "НИЖЕ средней "

print("\n" + "="*40)
print("     ИТОГОВЫЙ АНАЛИЗ АКЦИЙ META")
print("="*40)
print(f"Текущая цена:            ${current_price:.2f}")
print(f"Статус относительно MA200: {trend_status}")
print("-" * 40)
print(f"Доходность последней сессии:  {last_return:+.2f}%")
print(f"Макс. рост за день (пик):     {day_max_revenue*100:+.2f}%")
print(f"Макс. падение за день:        {day_min_revenue*100:+.2f}%")
print("-" * 40)
print(f"ГОДОВОЙ РИСК (Волатильность): {annual_volatility:.2f}%")
print(f"МАКСИМАЛЬНЫЙ УБЫТОК (Drawdown): {max_drawdown:.2f}%")
print(f"Дней на новых максимумах:     {df['recovered'].sum()}")
print("="*40)
print(f"Коэффициент Шарпа: {sharpe_ratio:.2f}")


sns.set_theme(style="white")
plt.rcParams['font.family'] = 'sans-serif'

fig, (ax1, ax2, ax3) = plt.subplots(3,1, figsize=(15,18), sharex = True, gridspec_kw={'height_ratios': [2.5, 1, 1]})
plt.subplots_adjust(hspace=0.4)

stats = [
    (f"Макс. дох.:\n{day_max_revenue:.2f}%", 0.12),
    (f"Мин. дох.:\n{day_min_revenue:.2f}%", 0.37),
    (f"Станд. откл.:\n{standard_deviation:.2f}%", 0.62),
    (f"Посл. дох.:\n{last_return:+.2f}%", 0.85)
]

for text,x_pos in stats:
    fig.text(x_pos, 0.89, text, ha='center', va='center', fontsize=25,fontweight='bold', color='#2c3e50',
             bbox=dict(facecolor='#f8f9fa', edgecolor='#dee2e6',boxstyle='round,pad=1'))

# --- 1. ГРАФИК ЦЕНЫ ---
ax1.plot(df["date"], df["close"], linewidth=2.5, color='#3498db')
ax1.fill_between(df["date"], df["close"], alpha=0.2, color='#3498db')
ax1.set_xlabel("Дата")
ax1.set_ylabel("Цена акций")
ax1.set_title("Цена акций META", fontsize=18, fontweight='bold', pad=20, loc='left')
ax1.grid(True, linestyle = '--', alpha = 0.5)
ax1.legend()

# --- 2. ГРАФИК ОТКЛОНЕНИЙ (ДОХОДНОСТИ) ---
ax2.plot(df["date"], df["rolling_std"], color='#9b59b6', linewidth=1.5)
ax2.set_xlabel("Дата")
ax2.set_ylabel("Стандартное отклонение")
ax2.set_title("Стандартное отклонение доходности акций META", fontsize=18, fontweight='bold', loc='left')
ax2.fill_between(df["date"], df["return"], color='#9b59b6', alpha=0.2)
ax2.grid(True, linestyle = '--', alpha = 0.5)
ax2.legend()

# --- 3. ГРАФИК ОБЪЕМА (VOLUME) ---
colors = ['#2ecc71' if r >= 0 else '#e74c3c' for r in df["return"]]
ax3.bar(df['date'], df['volume'], label = "Обьем торгов", color = colors, alpha=0.6, width=1.5)
ax3.set_xlabel("Дата")
ax3.set_ylabel("Объем торгов")
ax3.set_title("Объем торгов акций META", fontsize=18, fontweight='bold', loc='left')
ax3.grid(True, linestyle = '--', alpha = 0.5)

for ax in [ax1, ax2, ax3]:
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#bdc3c7')
    ax.spines['bottom'].set_color('#bdc3c7')
    ax.grid(axis='y', linestyle='--', alpha=0.3)
    ax.tick_params(axis='both', labelsize=10, colors='#636e72') 

plt.tight_layout(rect=[0, 0, 1, 0.85])
plt.subplots_adjust(
    left=0.05,
    bottom=0.055,
    right=0.977,
    top=0.742,
    wspace=0.2,
    hspace=0.48
)


plt.show()
