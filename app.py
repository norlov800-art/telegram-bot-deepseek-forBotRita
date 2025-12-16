import os
import telebot
import requests
import logging
from flask import Flask, request
import time

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8504373078:AAEINBhCSq7yBC42A5Ucf14Z-UmK95WEqXI')
DEEPSEEK_API_KEY = os.environ.get('sk-69fe68d2a539461694c7367b5b6d7c45')

# ========== ДИАГНОСТИКА ПРИ ЗАПУСКЕ ==========
logger.info("=" * 60)
logger.info("🚀 ЗАПУСК TELEGRAM БОТА")
logger.info("=" * 60)

# Проверка наличия токенов
if not TELEGRAM_TOKEN:
    logger.error("❌ TELEGRAM_TOKEN не найден!")
else:
    logger.info(f"✅ TELEGRAM_TOKEN: {TELEGRAM_TOKEN[:15]}...")

if not DEEPSEEK_API_KEY:
    logger.warning("⚠️ DEEPSEEK_API_KEY не найден. Бот будет в эхо-режиме")
else:
    logger.info(f"✅ DEEPSEEK_API_KEY: {DEEPSEEK_API_KEY[:10]}... (длина: {len(DEEPSEEK_API_KEY)})")
    if not DEEPSEEK_API_KEY.startswith('sk-'):
        logger.error("❌ DEEPSEEK_API_KEY имеет неверный формат! Должен начинаться с 'sk-'")

# Проверка подключения к DeepSeek API
if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith('sk-'):
    logger.info("🧪 Тестирую подключение к DeepSeek API...")
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        test_data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "Тест"}],
            "max_tokens": 5
        }
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            json=test_data,
            headers=headers,
            timeout=10
        )
        logger.info(f"📡 DeepSeek API ответил с кодом: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"❌ Ошибка DeepSeek API: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        logger.error(f"❌ Ошибка теста DeepSeek: {type(e).__name__}: {str(e)}")

logger.info("=" * 60)

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ========== FLASK РОУТЫ ==========
@app.route('/')
def home():
    return "✅ Бот работает! Отправьте /start в Telegram"

@app.route('/debug')
def debug():
    """Страница для отладки"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Bot</title>
        <style>
            body {{ font-family: Arial; margin: 40px; }}
            .success {{ color: green; }}
            .warning {{ color: orange; }}
            .error {{ color: red; }}
            .info {{ background: #f5f5f5; padding: 20px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <h1>🤖 Отладка Telegram Bot</h1>
        <div class="info">
            <h3>Статус:</h3>
            <p>Telegram Token: <span class="{'success' if TELEGRAM_TOKEN else 'error'}">
                {'✅ Рабочий' if TELEGRAM_TOKEN else '❌ Отсутствует'}
            </span></p>
            <p>DeepSeek Key: <span class="{'success' if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith('sk-') else 'warning'}">
                {'✅ Найден' if DEEPSEEK_API_KEY else '⚠️ Отсутствует'}
            </span></p>
            <p>Режим: {'🤖 AI режим' if DEEPSEEK_API_KEY else '🔁 Эхо-режим'}</p>
        </div>
        <p><a href="/">На главную</a></p>
    </body>
    </html>
    """
    return html

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик webhook от Telegram"""
    start_time = time.time()
    
    try:
        logger.info("📥 Получен запрос на /webhook")
        
        # Проверяем наличие данных
        if not request.data:
            logger.error("❌ Пустой запрос от Telegram")
            return 'Bad Request', 400
        
        # Парсим JSON
        json_data = request.get_json()
        if not json_data:
            logger.error("❌ Невалидный JSON от Telegram")
            return 'Bad Request', 400
        
        logger.info(f"📊 Данные от Telegram: update_id={json_data.get('update_id', 'unknown')}")
        
        # Обрабатываем обновление
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        
        processing_time = time.time() - start_time
        logger.info(f"✅ Webhook обработан за {processing_time:.2f} сек")
        
        return 'OK', 200
        
    except Exception as e:
        logger.error(f"💥 Ошибка в webhook: {type(e).__name__}: {str(e)}")
        return 'Internal Server Error', 500

# ========== TELEGRAM ОБРАБОТЧИКИ ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    logger.info(f"👋 Команда /start от {message.from_user.id}")
    
    welcome_text = """
👋 Привет! Я бот с интеграцией DeepSeek AI.

Доступные команды:
/start - Начало работы
/help - Помощь
/status - Статус бота
/test - Тестовая команда

Просто напишите мне вопрос, и я постараюсь помочь!
    """
    
    try:
        bot.reply_to(message, welcome_text)
        logger.info(f"✅ Приветствие отправлено пользователю {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки приветствия: {e}")

@bot.message_handler(commands=['status'])
def send_status(message):
    """Показывает статус бота"""
    logger.info(f"📊 Команда /status от {message.from_user.id}")
    
    status_text = f"""
📊 Статус бота:
• Telegram: {'✅ Подключен' if TELEGRAM_TOKEN else '❌ Ошибка'}
• DeepSeek API: {'✅ Подключен' if DEEPSEEK_API_KEY else '❌ Не подключен'}
• Режим: {'🤖 AI режим' if DEEPSEEK_API_KEY else '🔁 Эхо-режим'}
• Время работы: {time.strftime('%H:%M:%S')}
    """
    
    try:
        bot.reply_to(message, status_text)
        logger.info(f"✅ Статус отправлен пользователю {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки статуса: {e}")

@bot.message_handler(commands=['test'])
def send_test(message):
    """Тестовая команда"""
    logger.info(f"🧪 Команда /test от {message.from_user.id}")
    
    try:
        bot.reply_to(message, "✅ Бот работает! Тестовое сообщение получено.")
        logger.info(f"✅ Тестовое сообщение отправлено пользователю {message.from_user.id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки тестового сообщения: {e}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Основной обработчик сообщений"""
    user_id = message.from_user.id
    message_text = message.text
    
    logger.info("=" * 50)
    logger.info(f"📩 Новое сообщение от {user_id}: {message_text[:50]}...")
    
    # 1. Проверяем наличие ключа DeepSeek
    if not DEEPSEEK_API_KEY:
        logger.warning("⚠️ DEEPSEEK_API_KEY не найден. Включаю эхо-режим.")
        try:
            bot.reply_to(message, f"🔁 Эхо: {message_text}")
            logger.info(f"✅ Эхо-сообщение отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки эхо-сообщения: {e}")
        logger.info("=" * 50)
        return
    
    # 2. Проверяем формат ключа DeepSeek
    if not DEEPSEEK_API_KEY.startswith('sk-'):
        logger.error(f"❌ DEEPSEEK_API_KEY имеет неверный формат: {DEEPSEEK_API_KEY[:20]}...")
        try:
            bot.reply_to(message, "❌ Ошибка: неверный формат API ключа")
            logger.info(f"✅ Сообщение об ошибке формата отправлено пользователю {user_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки сообщения об ошибке: {e}")
        logger.info("=" * 50)
        return
    
    # 3. Пытаемся получить ответ от DeepSeek
    try:
        logger.info("🔄 Отправляю запрос к DeepSeek API...")
        
        # Показываем индикатор "печатает"
        bot.send_chat_action(message.chat.id, 'typing')
        
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты полезный ассистент. Отвечай на русском языке кратко и по делу."
                },
                {
                    "role": "user",
                    "content": message_text
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
            "stream": False
        }
        
        # Отправляем запрос с таймаутом
        logger.info(f"📤 Запрос к DeepSeek с ключом: {DEEPSEEK_API_KEY[:10]}...")
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            json=data,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"📥 Ответ от DeepSeek получен. Статус: {response.status_code}")
        
        # 4. Обрабатываем ответ
        if response.status_code == 200:
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]
                logger.info(f"✅ Получен ответ AI ({len(answer)} символов)")
                
                # Разбиваем длинные ответы
                if len(answer) > 4000:
                    parts = [answer[i:i+4000] for i in range(0, len(answer), 4000)]
                    for i, part in enumerate(parts):
                        if i == 0:
                            bot.reply_to(message, part)
                        else:
                            bot.send_message(message.chat.id, part)
                    logger.info(f"✅ Ответ отправлен частями ({len(parts)} частей)")
                else:
                    bot.reply_to(message, answer)
                    logger.info(f"✅ Ответ отправлен пользователю {user_id}")
                    
            else:
                logger.error(f"❌ Неожиданный формат ответа: {result}")
                bot.reply_to(message, "⚠️ Не удалось обработать ответ от нейросети")
                
        elif response.status_code == 402:
            logger.error("❌ Ошибка 402: недостаточно средств/квот на API ключе")
            bot.reply_to(message, "⚠️ Закончилась квота на API-ключе DeepSeek. Нужно пополнить баланс.")
            
        elif response.status_code == 401:
            logger.error("❌ Ошибка 401: неавторизованный доступ. Ключ неверный.")
            bot.reply_to(message, "❌ Ошибка: неверный API-ключ DeepSeek.")
            
        elif response.status_code == 429:
            logger.warning("⚠️ Ошибка 429: слишком много запросов.")
            bot.reply_to(message, "⏳ Слишком много запросов. Попробуйте через минуту.")
            
        else:
            logger.error(f"❌ Другая ошибка API: {response.status_code}, Тело: {response.text[:200]}")
            bot.reply_to(message, f"🔧 Ошибка сервера AI (код {response.status_code}).")
            
    except requests.exceptions.Timeout:
        logger.error("⏱️ Таймаут запроса к DeepSeek API.")
        bot.reply_to(message, "⏱️ Нейросеть долго не отвечает. Попробуйте еще раз.")
        
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Ошибка подключения к DeepSeek API.")
        bot.reply_to(message, "🔌 Ошибка сети. Проверьте подключение к интернету.")
        
    except Exception as e:
        logger.error(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {type(e).__name__}: {str(e)}")
        try:
            bot.reply_to(message, "😕 При обработке запроса произошла непредвиденная ошибка.")
        except Exception as send_error:
            logger.error(f"💥 Не удалось отправить сообщение об ошибке: {send_error}")
    
    logger.info(f"✅ Обработка сообщения завершена для пользователя {user_id}")
    logger.info("=" * 50)

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 Сервер запускается...")
    
    # Тестируем Telegram бота
    try:
        bot_info = bot.get_me()
        logger.info(f"🤖 Бот инициализирован: @{bot_info.username} ({bot_info.first_name})")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации бота: {e}")
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Веб-сервер запускается на порту {port}")
    logger.info(f"🔗 Основной URL: https://telegram-bot-deepseek-forbotrita.onrender.com")
    logger.info(f"🔧 Отладка: https://telegram-bot-deepseek-forbotrita.onrender.com/debug")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)
