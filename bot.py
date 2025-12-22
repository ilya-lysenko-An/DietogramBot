import logging
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import database

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "8384396628:AAHcRT21YqN3QLesRVAUk__lDZ972pQTlQw"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для похудения\n\n"
        "📝 ВВОД ДАННЫХ (можно вводить по одной или несколько):\n"
        "/steps [число] - шаги\n"
        "/calories [число] - калории\n"
        "/weight [число] - вес\n"
        "/burned [число] - сожжённые калории\n\n"
        "📊 ПРОСМОТР:\n"
        "/allSteps - все шаги сегодня\n"
        "/allCalories - все калории сегодня\n"
        "/allWeight - весь вес пользователей\n"
        "/allBurned - все сожжённые калории\n"
        "/stats - мои данные сегодня"
    )

async def handle_combined(update: Update, context: ContextTypes.DEFAULT_TYPE):
 
    text = update.message.text.strip()
    
    # Если сообщение начинается с '/' и содержит пробелы после команд
    if text.startswith('/') and ' ' in text:
        print(f"🔍 Обрабатываем комбинированную команду: {text}")
        
        # Словарь для хранения результатов обработки
        results = {
            'steps': None,
            'weight': None, 
            'calories': None,
            'burned': None
        }
        
        # Разбиваем на пары команда-значение
        parts = text.split()
        i = 0
        
        while i < len(parts):
            cmd = parts[i]
            
            # Если это команда и есть следующее значение
            if cmd in ['/steps', '/weight', '/calories', '/burned'] and i + 1 < len(parts):
                value = parts[i + 1]
                
                try:
                    # Обрабатываем каждую команду
                    if cmd == '/steps':
                        steps_count = int(value)
                        if steps_count > 150000:
                            results['steps'] = "дохуя прошел сегодня, топай нахуй"
                        else:
                            user = update.effective_user
                            database.db.save_measurement(
                                user.id, user.username, user.first_name,
                                'steps', steps_count
                            )
                            results['steps'] = "saved"
                    
                    elif cmd == '/calories':
                        calories_count = int(value)
                        if calories_count < 500:
                            results['calories'] = "кушай больше"
                        else:
                            user = update.effective_user
                            database.db.save_measurement(
                                user.id, user.username, user.first_name,
                                'calories', calories_count
                            )
                            results['calories'] = "saved"
                    
                    elif cmd == '/weight':
                        weight_value = float(value)
                        if weight_value > 200:
                            results['weight'] = "слышь пидор, ты точку не забыл?"
                        else:
                            user = update.effective_user
                            
                            cursor = database.db.conn.cursor()
                            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (user.id,))
                            result = cursor.fetchone()
                            
                            if not result:
                                database.db.save_measurement(
                                    user.id, user.username, user.first_name,
                                    'weight', weight_value
                                )
                            else:
                                database.db.save_measurement(
                                    user.id, user.username, user.first_name,
                                    'weight', weight_value
                                )
                            
                            results['weight'] = "saved"
                    
                    elif cmd == '/burned':
                        burned_value = int(value)
                        if burned_value <= 0:
                            results['burned'] = "Ну хоть что то введи А"
                        elif burned_value > 10000:
                            results['burned'] = "Не, люди стока не жгут, переделывай"
                        else:
                            user = update.effective_user
                            database.db.save_burned(
                                user.id, user.username, user.first_name,
                                burned_value
                            )
                            results['burned'] = "saved"
                
                except ValueError:
                    if cmd == '/steps':
                        results['steps'] = "❌ Введите число: /steps 10000"
                    elif cmd == '/weight':
                        results['weight'] = "❌ Введите число: /weight 85.5"
                    elif cmd == '/calories':
                        results['calories'] = "❌ Введите число: /calories 1800"
                    elif cmd == '/burned':
                        results['burned'] = "Введите число: /burned 650"
                except Exception as e:
                    results[cmd[1:]] = f"❌ Ошибка: {e}"
                
                i += 2  # Пропускаем команду и значение
            else:
                i += 1
        
        # Проверяем были ли успешные сохранения
        saved_successfully = False
        for result in results.values():
            if result == "saved":
                saved_successfully = True
                break
        
        # Ставим реакцию если что-то сохранилось успешно
        if saved_successfully:
            try:
                await update.message.set_reaction(["👍"])
            except:
                pass
        
        # Проверяем есть ли ошибки для показа
        error_messages = []
        for result in results.values():
            if result and result != "saved":
                error_messages.append(result)
        
        # Показываем только ошибки (если есть)
        if error_messages:
            await update.message.reply_text("\n".join(error_messages))
    
    else:
        # Если не комбинированная команда, показываем справку как раньше
        cmd = text.split()[0] if text else ""
        if cmd == '/steps':
            await update.message.reply_text("Используйте: /steps [число]")
        elif cmd == '/weight':
            await update.message.reply_text("Используйте: /weight [число]")
        elif cmd == '/calories':
            await update.message.reply_text("Используйте: /calories [число]")
        elif cmd == '/burned':
            await update.message.reply_text("Используйте: /burned [число]")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        data = database.db.get_user_today_data(user.id)
        
        if not data:
            await update.message.reply_text("📭 Нет данных за сегодня")
        else:
            steps, calories, weight, burned = data
            response = f"📊 {user.first_name} сегодня:\n\n"
            
            if steps:
                response += f"👣 Шаги: {int(steps):,}\n".replace(",", " ")
            if calories:
                response += f"🍎 Калории: {int(calories)}\n"
            if weight:
                response += f"⚖️ Вес: {weight} кг\n"
            if burned:
                response += f"🔥 Сожжено: {int(burned)} ккал\n"
            
            await update.message.reply_text(response)
        
    except Exception as e:
        print(f"❌ Ошибка в stats: {e}")
        await update.message.reply_text("❌ Ошибка")

async def all_steps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        steps_data = database.db.get_today_stats('steps')
        if not steps_data:
            await update.message.reply_text("📭 Нет шагов за сегодня")
            return
        response = "👣 ШАГИ СЕГОДНЯ:\n\n"
        for name, value in steps_data:
            response += f"{name}: {int(value):,} шагов\n".replace(",", " ")
        await update.message.reply_text(response)
    except Exception:
        await update.message.reply_text("❌ Ошибка")

async def all_calories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        calories_data = database.db.get_today_stats('calories')
        if not calories_data:
            await update.message.reply_text("📭 Нет калорий за сегодня")
            return
        response = "🍎 КАЛОРИИ СЕГОДНЯ:\n\n"
        for name, value in calories_data:
            response += f"{name}: {int(value)} ккал\n"
        await update.message.reply_text(response)
    except Exception:
        await update.message.reply_text("❌ Ошибка")

async def all_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cursor = database.db.conn.cursor()
        cursor.execute('SELECT id, first_name FROM users')
        users = cursor.fetchall()
        
        if not users:
            await update.message.reply_text("📭 Нет пользователей")
            return
        
        today = datetime.date.today().isoformat()
        response = "⚖️ ТЕКУЩИЙ ВЕС:\n\n"
        
        for user_id, name in users:
            cursor.execute('''
                SELECT weight, date FROM measurements 
                WHERE user_id = ? AND weight IS NOT NULL AND date = ?
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id, today))
            
            today_weight = cursor.fetchone()

            cursor.execute('''
                SELECT weight, date FROM measurements 
                WHERE user_id = ? AND weight IS NOT NULL
                ORDER BY date DESC, created_at DESC LIMIT 1
            ''', (user_id,))
            
            last_result = cursor.fetchone()
            
            if not last_result:
                response += f"{name}: ❌ нет данных\n"
                continue
                
            weight, last_date = last_result
            is_today = (last_date == today)

            if is_today:
                status_emoji = "🟢"  # Зеленый кружок - вес обновлен сегодня
            else:
                status_emoji = "🔴"  # Красный кружок - вес не обновлен сегодня

            cursor.execute('''
                SELECT weight FROM measurements 
                WHERE user_id = ? AND weight IS NOT NULL AND date != ?
                ORDER BY date DESC, created_at DESC LIMIT 1
            ''', (user_id, last_date))
            
            prev = cursor.fetchone()
            
            change_text = ""
            if prev:
                change = weight - prev[0]

                if change < -0.1:  # Похудение (>0.1 кг)
                    change_emoji = "🔽"
                    change_text = f" {change_emoji}{abs(change):.1f} кг"
                elif change > 0.1:  # Набор веса (>0.1 кг)
                    change_emoji = "🔼"
                    change_text = f" {change_emoji}{change:.1f} кг"
                else:  # Без изменений (±0.1 кг)
                    change_emoji = "↕️"
                    change_text = f" {change_emoji}без изменений"
                
                if not is_today:
                    last_date_obj = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()
                    days_diff = (datetime.date.today() - last_date_obj).days
                    
                    if days_diff == 1:
                        date_info = " (вчера)"
                    elif days_diff > 1:
                        date_info = f" ({days_diff} дн. назад)"
                    else:
                        date_info = ""
                    
                    response += f"{status_emoji} {name}: {weight} кг{date_info}{change_text} (было {prev[0]})\n"
                else:
                    response += f"{status_emoji} {name}: {weight} кг{change_text} (было {prev[0]})\n"
            else:
                if is_today:
                    response += f"{status_emoji} {name}: {weight} кг 🆕\n"
                else:
                    last_date_obj = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()
                    days_diff = (datetime.date.today() - last_date_obj).days
                    
                    if days_diff == 1:
                        date_info = " (вчера)"
                    elif days_diff > 1:
                        date_info = f" ({days_diff} дн. назад)"
                    else:
                        date_info = ""
                    
                    response += f"{status_emoji} {name}: {weight} кг{date_info} 🆕\n"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        print(f"❌ Ошибка в all_weight: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text("❌ Ошибка при получении данных о весе")

async def all_burned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Все сожженные калории за сегодня"""
    try:
        today = datetime.date.today().isoformat()
        cursor = database.db.conn.cursor()
        
        cursor.execute('''
            SELECT u.first_name, m.burned
            FROM measurements m
            JOIN users u ON m.user_id = u.id
            WHERE m.date = ? AND m.burned IS NOT NULL
            ORDER BY m.burned DESC
        ''', (today,))
        
        burned_data = cursor.fetchall()
        
        if not burned_data:
            await update.message.reply_text("📭 Нет данных о сожженных калориях за сегодня")
            return
            
        response = "🔥 СОЖЖЕННЫЕ КАЛОРИИ СЕГОДНЯ:\n\n"
        total = 0
        
        for name, value in burned_data:
            response += f"{name}: {int(value)} ккал\n"
            total += value
            
        response += f"\n📊 Всего сожжено: {int(total)} ккал"
        await update.message.reply_text(response)
        
    except Exception as e:
        print(f"❌ Ошибка в all_burned: {e}")
        await update.message.reply_text("❌ Ошибка")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("steps", handle_combined))
    app.add_handler(CommandHandler("weight", handle_combined))
    app.add_handler(CommandHandler("calories", handle_combined))
    app.add_handler(CommandHandler("burned", handle_combined))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("allSteps", all_steps))
    app.add_handler(CommandHandler("allCalories", all_calories))
    app.add_handler(CommandHandler("allWeight", all_weight))
    app.add_handler(CommandHandler("allBurned", all_burned))
    
    print("✅ Бот запущен с поддержкой комбинированных команд")
    app.run_polling()

if __name__ == "__main__":
    main()