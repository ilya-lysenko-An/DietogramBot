import sqlite3
from datetime import datetime

conn = sqlite3.connect('fitness.db')
cursor = conn.cursor()
today = datetime.now().strftime("%Y-%m-%d")

print("="*50)
print("🔍 ПРОВЕРКА КОРРЕКТНОСТИ СОХРАНЕНИЯ ДАННЫХ")
print("="*50)

# 1. Проверяем структуру таблицы
print("\n📋 СТРУКТУРА ТАБЛИЦЫ measurements:")
print("-"*40)

cursor.execute("PRAGMA table_info(measurements)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 2. Проверяем последние 5 записей ВСЕХ типов
print("\n📝 ПОСЛЕДНИЕ 5 ЗАПИСЕЙ (все типы):")
print("-"*40)

cursor.execute('''
    SELECT m.id, u.first_name, m.type, m.value, m.burned, m.date, m.created_at
    FROM measurements m
    JOIN users u ON m.user_id = u.id
    ORDER BY m.created_at DESC
    LIMIT 5
''')

for row in cursor.fetchall():
    id_num, name, mtype, value, burned, date, created = row
    burned_str = f", burned: {burned}" if burned is not None else ""
    type_str = f"type: {mtype}" if mtype else "type: NULL"
    value_str = f", value: {value}" if value is not None else ""
    print(f"  ID:{id_num} | {name} | {type_str}{value_str}{burned_str} | {date}")

# 3. Проверяем, есть ли проблемы с burned
print("\n🔍 ПРОВЕРКА burned:")
print("-"*40)

# Все записи с burned
cursor.execute("SELECT COUNT(*) FROM measurements WHERE burned IS NOT NULL")
total_burned = cursor.fetchone()[0]
print(f"✅ Записей с burned: {total_burned}")

# burned сегодня
cursor.execute("SELECT COUNT(*) FROM measurements WHERE date = ? AND burned IS NOT NULL", (today,))
burned_today = cursor.fetchone()[0]
print(f"✅ burned сегодня: {burned_today}")

# Примеры burned записей
if total_burned > 0:
    cursor.execute('''
        SELECT u.first_name, m.burned, m.date, m.created_at
        FROM measurements m
        JOIN users u ON m.user_id = u.id
        WHERE m.burned IS NOT NULL
        ORDER BY m.created_at DESC
        LIMIT 3
    ''')
    
    print("📊 Примеры burned записей:")
    for name, burned, date, created in cursor.fetchall():
        print(f"  {name}: {burned} ккал | {date} | {created}")

# 4. Проверяем корректность типов данных
print("\n✅ КОРРЕКТНОСТЬ ТИПОВ ДАННЫХ:")
print("-"*40)

types_check = [
    ('steps', 'int'),
    ('calories', 'int'), 
    ('weight', 'float'),
    ('burned', 'int')
]

for mtype, expected_type in types_check:
    if mtype == 'burned':
        cursor.execute(f"SELECT burned FROM measurements WHERE burned IS NOT NULL LIMIT 1")
    else:
        cursor.execute(f"SELECT value FROM measurements WHERE type = ? LIMIT 1", (mtype,))
    
    result = cursor.fetchone()
    if result:
        value = result[0]
        actual_type = 'int' if isinstance(value, int) else 'float' if isinstance(value, float) else 'other'
        print(f"  {mtype}: {actual_type} (ожидалось: {expected_type}) - {'✅ OK' if expected_type in actual_type else '⚠️ Проверь'}")
    else:
        print(f"  {mtype}: нет данных")

# 5. Проверяем данные за сегодня
print(f"\n📅 ДАННЫЕ ЗА СЕГОДНЯ ({today}):")
print("-"*40)

# Шаги сегодня
cursor.execute('''
    SELECT u.first_name, m.value
    FROM measurements m
    JOIN users u ON m.user_id = u.id
    WHERE m.date = ? AND m.type = 'steps'
    ORDER BY m.created_at DESC
''', (today,))

steps_today = cursor.fetchall()
if steps_today:
    print(f"👣 Шаги ({len(steps_today)} записей):")
    for name, steps in steps_today:
        print(f"  {name}: {steps:,} шагов".replace(",", " "))
else:
    print("👣 Шаги: нет данных")

# Калории сегодня
cursor.execute('''
    SELECT u.first_name, m.value
    FROM measurements m
    JOIN users u ON m.user_id = u.id
    WHERE m.date = ? AND m.type = 'calories'
    ORDER BY m.created_at DESC
''', (today,))

calories_today = cursor.fetchall()
if calories_today:
    print(f"🍎 Калории ({len(calories_today)} записей):")
    for name, cals in calories_today:
        print(f"  {name}: {cals} ккал")
else:
    print("🍎 Калории: нет данных")

# Вес сегодня
cursor.execute('''
    SELECT u.first_name, m.value
    FROM measurements m
    JOIN users u ON m.user_id = u.id
    WHERE m.date = ? AND m.type = 'weight'
    ORDER BY m.created_at DESC
''', (today,))

weight_today = cursor.fetchall()
if weight_today:
    print(f"⚖️ Вес ({len(weight_today)} записей):")
    for name, weight in weight_today:
        print(f"  {name}: {weight} кг")
else:
    print("⚖️ Вес: нет данных")

# Сожжено сегодня
cursor.execute('''
    SELECT u.first_name, m.burned
    FROM measurements m
    JOIN users u ON m.user_id = u.id
    WHERE m.date = ? AND m.burned IS NOT NULL
    ORDER BY m.created_at DESC
''', (today,))

burned_today_list = cursor.fetchall()
if burned_today_list:
    print(f"🔥 Сожжено ({len(burned_today_list)} записей):")
    for name, burned in burned_today_list:
        print(f"  {name}: {burned} ккал")
else:
    print("🔥 Сожжено: нет данных")

# 6. Итоговая проверка
print("\n" + "="*50)
print("📊 ИТОГОВАЯ СТАТИСТИКА:")
print("-"*40)

cursor.execute("SELECT COUNT(*) FROM measurements WHERE type = 'steps'")
total_steps = cursor.fetchone()[0]
print(f"👣 Всего записей steps: {total_steps}")

cursor.execute("SELECT COUNT(*) FROM measurements WHERE type = 'calories'")
total_calories = cursor.fetchone()[0]
print(f"🍎 Всего записей calories: {total_calories}")

cursor.execute("SELECT COUNT(*) FROM measurements WHERE type = 'weight'")
total_weight = cursor.fetchone()[0]
print(f"⚖️ Всего записей weight: {total_weight}")

cursor.execute("SELECT COUNT(*) FROM measurements WHERE burned IS NOT NULL")
total_burned_final = cursor.fetchone()[0]
print(f"🔥 Всего записей burned: {total_burned_final}")

# Проверка целостности
total_expected = total_steps + total_calories + total_weight + total_burned_final
cursor.execute("SELECT COUNT(*) FROM measurements")
total_actual = cursor.fetchone()[0]

# Записи без типа и без burned (потенциальные проблемы)
cursor.execute("SELECT COUNT(*) FROM measurements WHERE type IS NULL AND burned IS NULL")
null_records = cursor.fetchone()[0]

print(f"\n🔍 ЦЕЛОСТНОСТЬ ДАННЫХ:")
print(f"  Всего записей: {total_actual}")
print(f"  Записей с данными: {total_expected}")
print(f"  Пустых записей: {null_records}")
print(f"  {'✅ Все данные корректны' if null_records == 0 else '⚠️ Есть пустые записи'}")

conn.close()

print("\n" + "="*50)
print("✅ Проверка завершена")
print("="*50)
