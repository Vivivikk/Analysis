import pandas as pd 
import scipy as sp
from scipy import stats
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("KAG_conversion_data.csv")
print(df.head())
print(df.info())

# ============== 1. ВЫБОР МЕТРИКИ ДЛЯ АНАЛИЗА ==============

df["CTR"] = df["Clicks"] / df["Impressions"] * 100

print("\nСтатистика CTR:")
print(df['CTR'].describe())

# ============== 2. ОПРЕДЕЛЯЕМ ГРУППЫ ДЛЯ A/B ТЕСТА ==============

group_A = df[df['xyz_campaign_id'] == 916].copy()
group_B = df[df['xyz_campaign_id'] == 936].copy()

print(f"\nРазмер группы A (кампания 916): {len(group_A)} объявлений")
print(f"Размер группы B (кампания 936): {len(group_B)} объявлений")

# ============== 3. ВИЗУАЛИЗАЦИЯ ДАННЫХ ==============

plt.figure(figsize=(12,6))

# График 1: Box plot (ящик с усами) для CTR

plt.subplot(1,2,1)
sns.boxplot(x='xyz_campaign_id', y='CTR', data=df)
plt.title('Сравнение CTR: Кампания 916 vs Кампания 936')
plt.xlabel('Кампания')
plt.ylabel('CTR (%)')

# График 2: Гистограмма распределения CTR

plt.subplot(1,2,2)
plt.hist(group_A['CTR'], alpha=0.5, label='Кампания 916', bins=20)
plt.hist(group_B['CTR'], alpha=0.5, label='Кампания 936', bins=20)
plt.xlabel('CTR (%)')
plt.ylabel('Частота')
plt.legend()
plt.title('Распределение CTR по группам')

plt.tight_layout()
plt.show()

# ============== 4. ПРОВЕРКА НОРМАЛЬНОСТИ РАСПРЕДЕЛЕНИЯ ==============

shapiro_A = stats.shapiro(group_A['CTR'].dropna())
shapiro_B = stats.shapiro(group_B['CTR'].dropna())
print(f"Кампания 916 - p-value: {shapiro_A[1]:.4f}")
print(f"Кампания 936 - p-value: {shapiro_B[1]:.4f}")

if shapiro_A[1] < 0.05 or shapiro_B[1] < 0.05:
    print("Данные НЕ распределены нормально (p-value < 0.05)")
    print("Будем использовать непараметрический тест Манна-Уитни")
    use_parametric = False
else:
    print("Данные распределены нормально (p-value >= 0.05)")
    print("Можем использовать t-тест")
    use_parametric = True

# ============== 5. ПРОВЕДЕНИЕ СТАТИСТИЧЕСКОГО ТЕСТА ==============

print("\n=== Результаты A/B теста ===")
print(f"Средний CTR кампании 916: {group_A['CTR'].mean():.3f}%")
print(f"Средний CTR кампании 936: {group_B['CTR'].mean():.3f}%")
print(f"Разница: {group_B['CTR'].mean() - group_A['CTR'].mean():.3f}%")

if use_parametric:
    t_stat, p_value = stats.ttest_ind(group_A['CTR'], group_B['CTR'], equal_var = False)
    print(f"\nT-тест (параметрический):")
    print(f"t-статистика: {t_stat:.4f}")
    print(f"p-value: {p_value:.4f}")
else:
    u_stat, p_value = stats.mannwhitneyu(group_A['CTR'], group_B['CTR'],
    alternative='two-sided')
    print(f"\nU-тест Манна-Уитни (непараметрический):")
    print(f"U-статистика: {u_stat:.4f}")
    print(f"p-value: {p_value:.4f}")

# ============== 6. ИНТЕРПРЕТАЦИЯ РЕЗУЛЬТАТОВ ==============
print("\n=== Интерпретация результатов ===")

alpha = 0.05

if p_value < alpha:
    print(f"✅ Результат статистически значим (p-value = {p_value:.4f} < {alpha})")
    if group_B['CTR'].mean() > group_A['CTR'].mean():
        print("👉 Кампания 936 (группа B) показывает более высокий CTR")
        print("   Рекомендуется использовать кампанию 936 для лучших результатов")
    else:
        print("👉 Кампания 916 (группа A) показывает более высокий CTR")
        print("   Рекомендуется использовать кампанию 916 для лучших результатов")
else:
    print(f"❌ Результат НЕ статистически значим (p-value = {p_value:.4f} >= {alpha})")
    print("👉 Нет достаточных доказательств, что одна кампания лучше другой")
    print("   Рекомендуется провести дополнительное тестирование")

# ============== 7. ДОПОЛНИТЕЛЬНЫЙ АНАЛИЗ: ВЛИЯНИЕ ПОЛА ==============

male_data = df[df['gender'] == 'M']
female_data = df[df['gender'] == 'F']

print(f"Средний CTR для мужчин: {male_data['CTR'].mean():.3f}%")
print(f"Средний CTR для женщин: {female_data['CTR'].mean():.3f}%")

stat,p_gender = stats.mannwhitneyu(male_data['CTR'], female_data['CTR'], alternative='two-sided')

print(f"p-value (разница между полами): {p_gender:.4f}")

if p_gender < 0.05:
    print("✅ Есть статистически значимая разница в CTR между мужчинами и женщинами")
    if female_data['CTR'].mean() > male_data['CTR'].mean():
        print("👉 Женщины показывают более высокий CTR")
    else:
        print("👉 Мужчины показывают более высокий CTR")
else:
    print("❌ Нет статистически значимой разницы в CTR между полами")

# ============== 8. СОЗДАНИЕ ИТОГОВОГО ОТЧЕТА ==============

print("\n" + "="*50)
print("ИТОГОВЫЙ ОТЧЕТ A/B ТЕСТИРОВАНИЯ")
print("="*50)

print(f"""
1. Цель теста: Сравнить эффективность рекламных кампаний 916 и 936
   
2. Метрика: CTR (Click-Through Rate) - процент кликов от показов
   
3. Результаты:
   - Кампания 916 (группа A): средний CTR = {group_A['CTR'].mean():.3f}%
   - Кампания 936 (группа B): средний CTR = {group_B['CTR'].mean():.3f}%
   - Разница: {abs(group_B['CTR'].mean() - group_A['CTR'].mean()):.3f}%
   - Статистическая значимость: p-value = {p_value:.4f}
   
4. Вывод: { 'Есть статистически значимая разница' if p_value < 0.05 else 'Нет статистически значимой разницы' }
   
5. Рекомендация: { 'Использовать кампанию 936' if (p_value < 0.05 and group_B['CTR'].mean() > group_A['CTR'].mean()) else 'Использовать кампанию 916' if (p_value < 0.05 and group_A['CTR'].mean() > group_B['CTR'].mean()) else 'Провести дополнительное тестирование' }
""")