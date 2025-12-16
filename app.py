import os
import telebot
import requests
from flask import Flask, request

# ========== КОНФИГУРАЦИЯ ==========
# 🔥 ЗАМЕНИТЕ ЭТИ КЛЮЧИ НА СВОИ! 🔥
TELEGRAM_TOKEN = "8564273978:AAEINBhCSq7yBC42A5Ucf14Z-UmK95WEqXI"  # Ваш Telegram токен
DEEPSEEK_API_KEY = "sk-69fe68d2a539461694c7367b5b6d7c45"  # Ваш новый DeepSeek ключ

# ========== ПРОВЕРКА КЛЮЧЕЙ ==========
print("=" * 60)
print("🤖 ЗАПУСК TELEGRAM БОТА С DEEPSEEK")
print("=" * 60)

# Проверяем Telegram токен
if not TELEGRAM_TOKEN or len(TELEGRAM_TOKEN) < 20:
    print("❌ ОШИБКА: TELEGRAM_TOKEN невалидный!")
    print(f"   Текущий токен: {TELEGRAM_TOKEN[:20]}...")
else:
    print(f"✅ TELEGRAM_TOKEN: {TELEGRAM_TOKEN[:15]}...")

# Проверяем DeepSeek ключ
if not DEEPSEEK_API_KEY or not DEEPSEEK_API_KEY.startswith('sk-'):
    print("❌ ОШИБКА: DEEPSEEK_API_KEY невалидный!")
    print(f"   Ключ должен начинаться с 'sk-'")
    if DEEPSEEK_API_KEY:
        print(f"   Текущий ключ: {DEEPSEEK_API_KEY[:20]}...")
else:
    print(f"✅ DEEPSEEK_API_KEY: {DEEPSEEK_API_KEY[:10]}...")
    print(f"   Длина ключа: {len(DEEPSEEK_API_KEY)} символов")

print("=" * 60)

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ========== FLASK РОУТЫ ==========
@app.route('/')
def home():
    return "✅ Бот работает с DeepSeek AI! Отправьте /start в Telegram"

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
            .success {{ color: green; font-weight: bold; }}
            .error {{ color: red; font-weight: bold; }}
            .info {{ background: #f0f0f0; padding: 20px; border-radius: 10px; }}
        </style>
    </head>
    <body>
        <h1>🤖 Отладка Telegram Bot</h1>
        
        <div class="info">
            <h3>Статус ключей:</h3>
            <p>Telegram Token: <span class="{'success' if TELEGRAM_TOKEN else 'error'}">
                {'✅ Установлен' if TELEGRAM_TOKEN else '❌ Отсутствует'}
            </span></p>
            
            <p>DeepSeek API Key: <span class="{'success' if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith('sk-') else 'error'}">
                {'✅ Установлен' if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith('sk-') else '❌ Отсутствует/Невалидный'}
            </span></p>
            
            <p>Режим бота: <strong>{'🤖 DeepSeek AI' if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith('sk-') else '🔁 Эхо-режим'}</strong></p>
        </div>
        
        <h3>Тестирование:</h3>
        <ul>
            <li><a href="/">Главная страница</a></li>
            <li><a href="https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe" target="_blank">Проверить Telegram бота</a></li>
            <li><a href="https://platform.deepseek.com" target="_blank">DeepSeek Dashboard</a></li>
        </ul>
    </body>
    </html>
    """
    return html

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json()
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return 'OK', 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'Error', 500

# ========== TELEGRAM ОБРАБОТЧИКИ ==========
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith('sk-'):
        bot.reply_to(message, "👋 Привет! Я бот с DeepSeek AI.\nЗадавайте вопросы, и я помогу вам!")
    else:
        bot.reply_to(message, "👋 Привет! Я бот в эхо-режиме.\n(Нет валидного DeepSeek API ключа)")

@bot.message_handler(commands=['status'])
def send_status(message):
    status_text = f"""
📊 Статус бота:
• Telegram: {'✅ Подключен' if TELEGRAM_TOKEN else '❌ Ошибка'}
• DeepSeek API: {'✅ Подключен' if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith('sk-') else '❌ Не подключен'}
• Режим: {'🤖 DeepSeek AI' if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith('sk-') else '🔁 Эхо'}
"""
    bot.reply_to(message, status_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Основной обработчик сообщений"""
    
    # Если нет валидного DeepSeek ключа - эхо-режим
    if not DEEPSEEK_API_KEY or not DEEPSEEK_API_KEY.startswith('sk-'):
        bot.reply_to(message, f"🔁 Эхо: {message.text}")
        return
    
    try:
        # Показываем, что бот печатает
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Подготавливаем запрос к DeepSeek
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты полезный ассистент. Отвечай на русском языке."
                },
                {
                    "role": "user",
                    "content": message.text
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.7,
            "stream": False
        }
        
        # Отправляем запрос
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            json=data,
            headers=headers,
            timeout=30
        )
        
        # Обрабатываем ответ
        if response.status_code == 200:
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]
                
                # Разбиваем длинные ответы для Telegram
                if len(answer) > 4000:
                    parts = [answer[i:i+4000] for i in range(0, len(answer), 4000)]
                    for i, part in enumerate(parts):
                        if i == 0:
                            bot.reply_to(message, part)
                        else:
                            bot.send_message(message.chat.id, part)
                else:
                    bot.reply_to(message, answer)
                    
            else:
                bot.reply_to(message, "❌ Не удалось получить ответ от AI")
                
        elif response.status_code == 401:
            bot.reply_to(message, "❌ Ошибка авторизации DeepSeek. Проверьте API ключ.")
        elif response.status_code == 429:
            bot.reply_to(message, "⚠️ Слишком много запросов. Попробуйте позже.")
        else:
            bot.reply_to(message, f"❌ Ошибка API: {response.status_code}")
            
    except requests.exceptions.Timeout:
        bot.reply_to(message, "⏱️ Таймаут запроса. Попробуйте еще раз.")
    except Exception as e:
        error_msg = str(e)
        print(f"Ошибка: {error_msg}")
        bot.reply_to(message, f"❌ Ошибка: {error_msg[:150]}")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    # Тестовый запрос к DeepSeek для проверки ключа
    if DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.startswith('sk-'):
        print("🧪 Тестирую подключение к DeepSeek API...")
        try:
            headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}"}
            test_data = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Привет"}],
                "max_tokens": 10
            }
            test_response = requests.post(
                "https://api.deepseek.com/chat/completions",
                json=test_data,
                headers=headers,
                timeout=10
            )
            print(f"✅ DeepSeek API отвечает: {test_response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка теста DeepSeek: {e}")
    
    # Запускаем сервер
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Сервер запущен на порту {port}")
    print(f"🌐 Откройте: http://localhost:{port}")
    print(f"🔧 Отладка: http://localhost:{port}/debug")
    app.run(host='0.0.0.0', port=port, debug=False)
