import sqlite3
import datetime

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('fitness.db', check_same_thread=False)
        self.create_users_table()
    
    def create_users_table(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        print("✅ База данных готова (новая структура)")
    
    def save_measurement(self, telegram_id, username, first_name, mtype, value):
        today = datetime.date.today().isoformat()
        cursor = self.conn.cursor()
        
        print(f"🔄 DEBUG save_measurement: {first_name} - {mtype}: {value}")
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id, username, first_name) 
            VALUES (?, ?, ?)
        ''', (telegram_id, username, first_name))
        
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        user_id = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT id FROM measurements 
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        existing = cursor.fetchone()
        
        if existing:
            if mtype == 'steps':
                cursor.execute('''
                    UPDATE measurements SET steps = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (value, existing[0]))
            elif mtype == 'calories':
                cursor.execute('''
                    UPDATE measurements SET calories = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (value, existing[0]))
            elif mtype == 'weight':
                cursor.execute('''
                    UPDATE measurements SET weight = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (value, existing[0]))
        else:
            if mtype == 'steps':
                cursor.execute('''
                    INSERT INTO measurements (user_id, date, steps, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, today, value))
            elif mtype == 'calories':
                cursor.execute('''
                    INSERT INTO measurements (user_id, date, calories, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, today, value))
            elif mtype == 'weight':
                cursor.execute('''
                    INSERT INTO measurements (user_id, date, weight, created_at, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, today, value))
        
        self.conn.commit()
        print(f"✅ Сохранено: {first_name} - {mtype}: {value}")
    
    def save_burned(self, telegram_id, username, first_name, burned_value):
        today = datetime.date.today().isoformat()
        cursor = self.conn.cursor()
        
        print(f"🔄 DEBUG save_burned: {first_name} - burned: {burned_value}")
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id, username, first_name) 
            VALUES (?, ?, ?)
        ''', (telegram_id, username, first_name))
        
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        user_id = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT id FROM measurements 
            WHERE user_id = ? AND date = ?
        ''', (user_id, today))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE measurements SET burned = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (burned_value, existing[0]))
        else:
            cursor.execute('''
                INSERT INTO measurements (user_id, date, burned, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, today, burned_value))
        
        self.conn.commit()
        print(f"✅ Сохранено burned: {first_name} - {burned_value}")
    
    def get_previous_weight(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT weight 
            FROM measurements 
            WHERE user_id = ? AND weight IS NOT NULL
            ORDER BY date DESC, created_at DESC
            LIMIT 1 OFFSET 1
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def get_today_stats(self, mtype):
        today = datetime.date.today().isoformat()
        cursor = self.conn.cursor()
        
        if mtype == 'steps':
            cursor.execute('''
                SELECT u.first_name, m.steps 
                FROM measurements m
                JOIN users u ON m.user_id = u.id
                WHERE m.date = ? AND m.steps IS NOT NULL
                ORDER BY m.steps DESC
            ''', (today,))
        elif mtype == 'calories':
            cursor.execute('''
                SELECT u.first_name, m.calories 
                FROM measurements m
                JOIN users u ON m.user_id = u.id
                WHERE m.date = ? AND m.calories IS NOT NULL
                ORDER BY m.calories DESC
            ''', (today,))
        elif mtype == 'weight':
            cursor.execute('''
                SELECT u.first_name, m.weight 
                FROM measurements m
                JOIN users u ON m.user_id = u.id
                WHERE m.date = ? AND m.weight IS NOT NULL
                ORDER BY m.weight DESC
            ''', (today,))
        
        return cursor.fetchall()
    
    def get_user_today_data(self, telegram_id):
        today = datetime.date.today().isoformat()
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT m.steps, m.calories, m.weight, m.burned
            FROM measurements m
            JOIN users u ON m.user_id = u.id
            WHERE u.telegram_id = ? AND m.date = ?
        ''', (telegram_id, today))
        
        return cursor.fetchone()

db = Database()