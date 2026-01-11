import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import sqlite3
import numpy as np

class WeightVisualizer:
    def __init__(self, db_path='fitness.db'):
        self.db_path = db_path
    
    def get_weight_chart_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.first_name
            FROM users u
            WHERE (
                SELECT COUNT(*) 
                FROM measurements m 
                WHERE m.user_id = u.id AND m.weight IS NOT NULL
            ) >= 6
        ''')
        
        eligible_users = cursor.fetchall()
        
        if not eligible_users:
            conn.close()
            return None
        
        chart_data = []
        
        for user_id, user_name in eligible_users:
            cursor.execute('''
                SELECT date, weight 
                FROM measurements 
                WHERE user_id = ? AND weight IS NOT NULL
                ORDER BY date
            ''', (user_id,))
            
            data_points = cursor.fetchall()
            
            if len(data_points) >= 6:
                dates = [datetime.strptime(date_str, "%Y-%m-%d") for date_str, _ in data_points]
                weights = [weight for _, weight in data_points]
                
                chart_data.append({
                    'user_name': user_name,
                    'dates': dates,
                    'weights': weights,
                    'count': len(data_points)
                })
        
        conn.close()
        return chart_data if chart_data else None
    
    def generate_weight_chart(self):
        data = self.get_weight_chart_data()
        
        if not data:
            print("Недостаточно данных (нужно 6+ записей веса)")
            return
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Яркие насыщенные цвета
        colors = [
            '#FF6B6B', '#4ECDC4', '#FFD166', '#06D6A0', '#118AB2',
            '#EF476F', '#073B4C', '#7209B7', '#F72585', '#3A86FF',
            '#FB5607', '#8338EC', '#3A86FF', '#FF006E', '#00BBF9',
            '#00F5D4', '#FF9E00', '#9B5DE5', '#F15BB5', '#00F5D4'
        ]
        
        # Находим общий диапазон весов
        all_weights = []
        for user_data in data:
            all_weights.extend(user_data['weights'])
        
        min_weight = min(all_weights)
        max_weight = max(all_weights)
        
        # Шкала Y с шагом 1 кг
        y_min = np.floor(min_weight) - 1
        y_max = np.ceil(max_weight) + 1
        y_ticks = np.arange(y_min, y_max + 0.5, 1)
        
        # Линии для каждого кг
        for y in y_ticks:
            ax.axhline(y=y, color='#F0F0F0', linestyle='-', linewidth=0.5, alpha=0.5)
        
        # Рисуем линии пользователей с яркими цветами
        for idx, user_data in enumerate(data):
            color = colors[idx % len(colors)]
            
            ax.plot(
                user_data['dates'], 
                user_data['weights'],
                marker='o',
                linewidth=3,
                markersize=10,
                markerfacecolor='white',
                markeredgecolor=color,
                markeredgewidth=2.5,
                label=f"{user_data['user_name']} ({user_data['count']} зап.)",
                color=color,
                alpha=1.0  # Полная непрозрачность
            )
        
        # Настройка внешнего вида
        ax.set_title('📈 Динамика веса (пользователи с 6+ записями)', 
                    fontsize=16, fontweight='bold', pad=20, color='#2C3E50')
        
        ax.set_xlabel('Дата', fontsize=12, labelpad=10)
        ax.set_ylabel('Вес (кг)', fontsize=12, labelpad=10)
        
        # Форматирование дат
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=45, ha='right')
        
        # Ось Y
        ax.set_ylim(y_min, y_max)
        ax.set_yticks(y_ticks)
        ax.yaxis.set_tick_params(labelsize=10)
        
        # Жирные линии каждые 5 кг
        for y in np.arange(y_min, y_max + 0.5, 5):
            ax.axhline(y=y, color='#DDDDDD', linestyle='-', linewidth=1, alpha=0.8)
        
        # Легенда
        ncol = 1 if len(data) <= 8 else 2
        ax.legend(loc='upper left', fontsize=11, framealpha=1.0,
                 edgecolor='#CCCCCC', facecolor='white', frameon=True,
                 borderpad=1, labelspacing=0.8)
        
        # Сетка
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        
        # Убираем рамки
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Яркий фон
        ax.set_facecolor('#FFFFFF')
        fig.patch.set_facecolor('white')
        
        plt.tight_layout()
        plt.show()


def test():
    viz = WeightVisualizer()
    viz.generate_weight_chart()

if __name__ == "__main__":
    test()