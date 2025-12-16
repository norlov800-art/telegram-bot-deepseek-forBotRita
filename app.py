import os
from flask import Flask, request
import telebot
import requests
import time

# ========== КОНФИГУРАЦИЯ ==========
TELEGRAM_TOKEN = os.environ.get("8504373078:AAEINBhCSq7yBC42A5Ucf14Z-UmK95WEqXI")
DEEPSEEK_API_KEY = os.environ.get("sk-3baac25d30784da9acb6d5c9a067bc8b")

# Проверка конфигурации
if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN не найден!")
if not DEEPSEEK_API_KEY:
    print("⚠️ DEEPSEEK_API_KEY не найден. Бот будет работать в эхо-режиме.")

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = telebot.TeleBot("8504373078:AAEINBhCSq7yBC42A5Ucf14Z-UmK95WEqXI")
app = Flask(__name__)

# ========== FLASK РОУТЫ ==========
@app.route('/')
def home():
    status = "✅ Работает с DeepSeek" if DEEPSEEK_API_KEY else "⚠️ Эхо-режим (нет API ключа)"
    return f"Бот работает! {status}"

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
    if DEEPSEEK_API_KEY:
        bot.reply_to(message, "👋 Привет! Я бот с DeepSeek AI.\nЗадавайте вопросы, и я постараюсь помочь!")
    else:
        bot.reply_to(message, "👋 Привет! Я бот в эхо-режиме.\nДобавьте API ключ DeepSeek для умных ответов.")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
📚 Доступные команды:
/start - Начать диалог
/help - Показать это сообщение
/about - О боте

💡 Просто напишите вопрос, и я отвечу!
    """
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['about'])
def send_about(message):
    about_text = f"""
🤖 О боте:
• Платформа: DeepSeek AI
• Режим: {'🤖 Умный режим' if DEEPSEEK_API_KEY else '🔁 Эхо-режим'}
• Хостинг: Render.com
• Для умных ответов нужен API ключ DeepSeek
    """
    bot.reply_to(message, about_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        # Проверяем, есть ли API ключ
        if not DEEPSEEK_API_KEY:
            bot.reply_to(message, f"🔁 Эхо: {message.text}\n\nℹ️ Добавьте DEEPSEEK_API_KEY для умных ответов.")
            return
        
        # Показываем индикатор "печатает"
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Подготавливаем запрос
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Ты полезный ассистент. Отвечай на русском языке."},
                {"role": "user", "content": message.text}
            ],
            "stream": False,
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        # Отправляем запрос с таймаутом
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            json=data,
            headers=headers,
            timeout=45
        )
        
        # Обрабатываем ответ
        if response.status_code == 200:
            response_data = response.json()
            if "choices" in response_data and len(response_data["choices"]) > 0:
                answer = response_data["choices"][0]["message"]["content"]
                
                # Разбиваем длинные ответы
                max_length = 4000  # Лимит Telegram
                if len(answer) <= max_length:
                    bot.reply_to(message, answer)
                else:
                    parts = [answer[i:i+max_length] for i in range(0, len(answer), max_length)]
                    for i, part in enumerate(parts):
                        if i == 0:
                            bot.reply_to(message, part)
                        else:
                            bot.send_message(message.chat.id, part)
            else:
                bot.reply_to(message, "❌ Неверный ответ от API")
                
        elif response.status_code == 401:
            bot.reply_to(message, "❌ Неверный API ключ. Проверьте DEEPSEEK_API_KEY.")
        elif response.status_code == 429:
            bot.reply_to(message, "⚠️ Слишком много запросов. Попробуйте позже.")
        else:
            bot.reply_to(message, f"❌ Ошибка {response.status_code}: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        bot.reply_to(message, "⏰ Запрос превысил время ожидания. Попробуйте еще раз.")
    except Exception as e:
        error_msg = str(e)
        print(f"Ошибка обработки: {error_msg}")
        bot.reply_to(message, f"❌ Ошибка: {error_msg[:200]}")

# ========== ЗАПУСК ==========
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Запуск Telegram бота с DeepSeek")
    print(f"🤖 Режим: {'DeepSeek AI' if DEEPSEEK_API_KEY else 'Эхо'}")
    print(f"🌐 Порт: {os.environ.get('PORT', 10000)}")
    print("=" * 50)
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
