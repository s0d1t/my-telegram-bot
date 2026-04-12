import asyncio
import logging
import time
import json
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# --- НАСТРОЙКИ ---
BOT_TOKEN = "8602984326:AAFZPFcZ5gZG3rfoQVmvnwqKVMKT6QYWl2c" 
ADMIN_CHAT_IDS = [8707137629, 8723515276] 

# Кулдаун: 20 минут = 1200 секунд
COOLDOWN_SECONDS = 1200 

# Файл для хранения истории сообщений
DATA_FILE = "cooldowns.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛОМ ---

def load_cooldowns():
    """Загружает данные из файла при запуске"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cooldowns(data):
    """Сохраняет данные в файл после каждого сообщения"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Загружаем историю при старте бота
user_last_message_time = load_cooldowns()

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Здравствуйте, напишите нам сообщением, и мы вышлем его в ближайшее время, "
        "ваше сообщение полностью анонимно."
    )

@dp.message()
async def handle_message(message: Message):
    user_id = str(message.from_user.id) # Используем строку для ID
    current_time = time.time()

    # 1. ПРОВЕРКА КУЛДАУНА
    last_time = user_last_message_time.get(user_id, 0)
    
    if current_time - last_time < COOLDOWN_SECONDS:
        # Вычисляем сколько осталось ждать
        remaining = int(COOLDOWN_SECONDS - (current_time - last_time))
        minutes = remaining // 60
        seconds = remaining % 60
        
        # Отвечаем пользователю и НЕ отправляем сообщение админам
        await message.answer(
            f"⏳ Пожалуйста, подождите. Следующее сообщение можно отправить через {minutes} мин. {seconds} сек."
        )
        print(f"БЛОК: Пользователь {user_id} превысил лимит. Осталось: {minutes}м {seconds}с")
        return # Выходим из функции, код ниже не выполнится

    # 2. ЕСЛИ КУЛДАУН ПРОШЕЛ:
    # Обновляем время последнего сообщения
    user_last_message_time[user_id] = current_time
    save_cooldowns(user_last_message_time)
    
    print(f"ОК: Сообщение от пользователя {user_id} принято.")

    try:
        user = message.from_user
        
        admin_info = (
            f"🕵️ <b>Источник сообщения:</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"Имя: {user.full_name}\n"
            f"Юзернейм: @{user.username if user.username else 'Нет'}\n"
            f"------------------\n"
        )
        
        # Отправляем каждому админу (тебе и кенту)
        for admin_id in ADMIN_CHAT_IDS:
            try:
                await bot.send_message(chat_id=admin_id, text=admin_info, parse_mode="HTML")
                await message.copy_to(chat_id=admin_id)
            except Exception as e:
                logging.error(f"Ошибка отправки админу {admin_id}: {e}")
        
        await message.answer("✅ Сообщение принято в обработку.")
        
    except Exception as e:
        logging.error(f"Ошибка обработки: {e}")
        await message.answer("❌ Произошла техническая ошибка.")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())