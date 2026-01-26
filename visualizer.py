import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import sqlite3
import numpy as np
from datetime import datetime, timedelta
import matplotlib.patheffects as pe 

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
            ) >= 7
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
            
            if len(data_points) >= 7:
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
                label=f"{user_data['user_name']}",
                color=color,
                alpha=1.0  # Полная непрозрачность
            )
        
        # Настройка внешнего вида
        ax.set_title('Динамика веса', 
                    fontsize=16, fontweight='bold', pad=20, color='#2C3E50')
        
        ax.set_xlabel('Дата', fontsize=12, labelpad=10)
        ax.set_ylabel('Вес (кг)', fontsize=12, labelpad=10)
        
        # Форматирование дат
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%y'))
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


class StepsCompetitionVisualizer:
    def __init__(self, db_path='fitness.db'):
        self.db_path = db_path
    
    def get_steps_competition_data(self, days=30, limit=10):
        """Возвращает данные для рейтинга: общая сумма / 30 дней"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        period_start = (today - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT 
                u.first_name,
                SUM(m.steps) as total_steps
            FROM measurements m
            JOIN users u ON m.user_id = u.id
            WHERE m.date >= ? AND m.steps IS NOT NULL
            GROUP BY u.id
            HAVING COUNT(m.steps) >= 3
            ORDER BY SUM(m.steps) DESC
            LIMIT ?
        ''', (period_start, limit))
        
        competitors = cursor.fetchall()
        conn.close()
        
        if not competitors:
            return None
        
        data = []
        for name, total_steps in competitors:
            monthly_avg = total_steps / days
            
            data.append({
                'name': name,
                'monthly_avg': int(monthly_avg)
            })
        
        data.sort(key=lambda x: x['monthly_avg'], reverse=True)
        return data
    
    def generate_monthly_competition_chart(self):
        """Чистый график рейтинга"""
        data = self.get_steps_competition_data(days=30, limit=10)
        
        if not data:
            print("Недостаточно данных за последний месяц (нужно минимум 3 дня активности)")
            return
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        names = [d['name'] for d in data]
        monthly_avg = [d['monthly_avg'] for d in data]
        
        # Градиент цветов от лучшего к худшему
        colors = plt.cm.YlOrRd(np.linspace(0.3, 0.9, len(data)))
        
        # Создаем бары
        bars = ax.barh(names, monthly_avg, color=colors, edgecolor='white', linewidth=2, height=0.65)
        
        # Находим максимальное значение
        max_steps = max(monthly_avg)
        
        # Добавляем номера мест СЛЕВА (больший отступ)
        for i, bar in enumerate(bars):
            y = bar.get_y() + bar.get_height()/2
            
            # Номер места слева с большим отступом
            ax.text(-max_steps * 0.12, y, f'{i+1}.',
                   va='center', ha='right', fontweight='bold', 
                   fontsize=13, color='#2C3E50')
        
        # Добавляем значения шагов справа от баров
        for bar, avg in zip(bars, monthly_avg):
            width = bar.get_width()
            y = bar.get_y() + bar.get_height()/2
            
            # Значение шагов
            ax.text(width + max_steps * 0.005, y,
                   f'{avg:,}'.replace(',', ' '),
                   va='center', fontweight='bold', fontsize=12,
                   color='#2C3E50')
        
        # Настройки графика
        ax.set_title(' ТОП-10 ПО ШАГАМ', 
                    fontsize=16, fontweight='bold', pad=20, color='#2C3E50')
        
        # Инвертируем чтобы 1 место было сверху
        ax.invert_yaxis()
        
        # Сетка только по X
        ax.grid(True, axis='x', alpha=0.2, linestyle='--')
        
        # Убираем ненужные рамки
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(True)
        
        # Убираем подпись и цифры оси X
        ax.set_xlabel('')
        ax.set_xticklabels([])
        ax.set_xticks([])
        
        # Фон
        ax.set_facecolor('#F8F9FA')
        fig.patch.set_facecolor('white')
        
        plt.tight_layout()
        plt.show()


def test_all_visualizations():
    print("📊 Генерация графиков...")
    
    # 1. График веса
    print("\n📈 График веса (6+ записей):")
    WeightVisualizer().generate_weight_chart()
    
    # 2. Рейтинг шагов
    print("\n🏆 Рейтинг шагов (топ-10 за 30 дней):")
    StepsCompetitionVisualizer().generate_monthly_competition_chart()


if __name__ == "__main__":
    test_all_visualizations()