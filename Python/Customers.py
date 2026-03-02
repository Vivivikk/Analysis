import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import FancyBboxPatch

print("Загрузка данных...")

df = pd.read_excel('client_online.xlsx')

print("Данные загружены...")
print(df.head())

df.columns = (
    df.columns
    .str.lower()
    .str.replace(" ", "_")
)
print("Columns: ")
print(df.columns)

# МЕТРИКИ
total_spend = df["spend"].sum()
total_revenue = df["revenue"].sum()
total_profit = total_revenue - total_spend
total_clicks = df["clicks"].sum()
total_conversions = df["conversions"].sum()
roi = (total_profit / total_spend) * 100
cpl = total_spend / total_conversions

print("\nОсновные метрики:")
print(f"Общий расход: {total_spend}")
print(f"Общий доход: {total_revenue}")
print(f"Общая прибыль: {total_profit}")
print(f"Общее количество кликов: {total_clicks}")
print(f"Общее количество конверсий: {total_conversions}")
print(f"ROI: {roi:.1f}%")
print(f"CPL: ${cpl:.2f}")

platform_status = (
    df.groupby("platform")
    .agg({
        "spend": "sum",
        "revenue": "sum",
        "clicks": "sum",
        "conversions": "sum"
    })
    .reset_index()
)
print(platform_status)

platform_status["profit"] = platform_status["revenue"] - platform_status["spend"]
platform_status["roi"] = (platform_status["profit"] / platform_status["spend"]) * 100
platform_status["roas"] = platform_status["revenue"] / platform_status["spend"]
platform_stats = platform_status.sort_values("profit", ascending=False)

print("\nПО ПЛАТФОРМАМ")
print("-------------")
print(platform_stats)

plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'figure.facecolor': "#FFFFFF",
    'axes.facecolor': "#FFFFFF",
    'axes.edgecolor': "#E2E0E0",
    'grid.color': "#F5F5F5",
    'font.family': "sans-serif",
    'text.color': '#1B263B',
    'axes.labelcolor': '#778DA9'
})


class ProfessionalDashboard:
    def __init__(self, data_file):
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"Файл {data_file} не найден!")
        self.df = pd.read_excel(data_file)
        self.df.columns = self.df.columns.str.lower().str.replace(" ", "_")
        self.prepare_data()

    def prepare_data(self):
        self.stats = self.df.groupby("platform").agg({
            "spend": "sum",
            "revenue": "sum",
            "clicks": "sum",
            "conversions": "sum"
        }).reset_index()
        self.stats["profit"] = self.stats["revenue"] - self.stats["spend"]
        self.stats["roi"] = (self.stats["profit"] / self.stats["spend"]) * 100
        self.stats["cpl"] = self.stats["spend"] / self.stats["conversions"]
        self.stats = self.stats.sort_values("profit", ascending=False)

    def draw(self):
        c1 = "#1B263B"
        c2 = "#415A77"
        c3 = "#778DA9"

        fig = plt.figure(figsize=(14, 12), facecolor="#FFFFFF")
        gs = fig.add_gridspec(3, 3, height_ratios=[0.7, 1.5, 0.6], hspace=0.4)

        fig.suptitle('МАРКЕТИНГОВЫЙ АНАЛИЗ ЭФФЕКТИВНОСТИ',
                     fontsize=22, fontweight='bold', x=0.05, ha='left', color=c1)

        # --- KPI карточки ---
        metrics = [
            ("ОБЩИЙ РАСХОД", f"${self.stats['spend'].sum():,.0f}", 0),
            ("ОБЩИЙ ДОХОД", f"${self.stats['revenue'].sum():,.0f}", 1),
            ("СРЕДНИЙ ROI", f"{self.stats['roi'].mean():.1f}%", 2)
        ]

        for label, value, col in metrics:
            ax = fig.add_subplot(gs[0, col])
            ax.axis('off')
            ax.text(0.5, 0.65, value, fontsize=30, fontweight='bold', ha='center', color=c1)
            ax.text(0.5, 0.35, label, fontsize=9, fontweight='bold', ha='center', color=c3)
            rect = FancyBboxPatch((0.05, 0.15), 0.9, 0.7, boxstyle="round,pad=0.05",
                                  ec="#CAC8C8", fc="#F9F8F8", transform=ax.transAxes, lw=1)
            ax.add_patch(rect)

        # --- График прибыли ---
        ax1 = fig.add_subplot(gs[1, 0:2])
        sns.barplot(data=self.stats, x="profit", y="platform",
                    palette=[c1, c2, c3], ax=ax1, hue="platform", legend=False)
        ax1.set_title("ПРИБЫЛЬ ПО КАНАЛАМ", loc='left', pad=20,
                      fontsize=14, fontweight='bold', color=c1)

        for i, v in enumerate(self.stats["profit"]):
            ax1.text(v + (max(self.stats["profit"]) * 0.01), i, f'${v:,.0f}',
                     va='center', fontsize=11, fontweight='medium', color=c2)
        sns.despine(left=True, bottom=True)

        # --- Пончик расходов ---
        ax2 = fig.add_subplot(gs[1, 2])
        ax2.pie(self.stats["spend"], labels=self.stats["platform"], autopct='%1.1f%%',
                pctdistance=0.75, startangle=110, colors=[c1, c2, c3, "#E0E1DD"],
                wedgeprops={'edgecolor': 'white', 'linewidth': 2})
        ax2.add_artist(plt.Circle((0, 0), 0.70, fc='white'))
        ax2.set_title("ДОЛЯ РАСХОДОВ", pad=20, fontsize=13, fontweight='bold', color=c1)

        # --- Таблица CPL ---
        ax3 = fig.add_subplot(gs[2, :])
        ax3.axis('off')

        table_data = self.stats[["platform", "conversions", "cpl"]].copy()
        table_data["cpl"] = table_data["cpl"].map("${:,.2f}".format)
        table_data.columns = ["ПЛАТФОРМА", "КОНВЕРСИИ", "CPL (ЦЕНА ЛИДА)"]

        table = ax3.table(cellText=table_data.values,
                          colLabels=table_data.columns,
                          cellLoc='center', loc='center',
                          colColours=[c1] * 3)
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.8)

        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor('#F5F5F5')
            if row == 0:
                cell.get_text().set_color('white')
                cell.get_text().set_weight('bold')
            else:
                cell.get_text().set_color(c1)

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()


if __name__ == "__main__":
    db = ProfessionalDashboard('client_online.xlsx')
    db.draw()
