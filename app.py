import os
import telebot
import requests
import json
import logging
from flask import Flask, request
from datetime import datetime

# ========== КОНФИГУРАЦИЯ ==========
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
YANDEX_API_KEY = os.environ.get('YANDEX_API_KEY')
YANDEX_FOLDER_ID = os.environ.get('YANDEX_FOLDER_ID')
YANDEX_MODEL = "yandexgpt-lite"  # Можно изменить на "yandexgpt"

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== ИНИЦИАЛИЗАЦИЯ ==========
bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

# ========== YANDEXGPT ФУНКЦИЯ ==========
def ask_yandex_gpt(user_message, system_prompt="Ты полезный и вежливый ассистент."):
    """
    Отправляет запрос к YandexGPT API и возвращает текстовый ответ.
    """
    # URL API Яндекс GPT
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    # Заголовки запроса
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }
    
    # Тело запроса согласно документации Яндекс
    data = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 1500
        },
        "messages": [
            {
                "role": "system",
                "text": system_prompt
            },
            {
                "role": "user", 
                "text": user_message
            }
        ]
    }
    
    # ========== ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ЗАПРОСА ==========
    logger.info("=" * 60)
    logger.info("🔍 ОТПРАВКА ЗАПРОСА К YANDEXGPT")
    logger.info("=" * 60)
    
    # Логируем основные параметры (скрываем полный ключ)
    logger.info(f"📡 URL: {url}")
    logger.info(f"📦 Модель: {YANDEX_MODEL}")
    logger.info(f"📁 Folder ID: {YANDEX_FOLDER_ID}")
    
    if YANDEX_API_KEY:
        logger.info(f"🔑 API Key (первые 15 символов): {YANDEX_API_KEY[:15]}...")
    else:
        logger.error("❌ API Key не указан!")
    
    # Логируем полное тело запроса
    logger.info("📝 Тело запроса (JSON):")
    try:
        request_json_pretty = json.dumps(data, ensure_ascii=False, indent=2)
        logger.info(f"\n{request_json_pretty}")
    except Exception as e:
        logger.error(f"❌ Не удалось сериализовать JSON запроса: {e}")
        logger.info(f"📝 Сырые данные: {data}")
    
    # ========== ОТПРАВКА ЗАПРОСА ==========
    try:
        start_time = datetime.now()
        logger.info(f"⏱ Время начала запроса: {start_time}")
        
        # Отправляем POST-запрос
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=30
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # ========== ЛОГИРОВАНИЕ ОТВЕТА ==========
        logger.info("=" * 60)
        logger.info("📡 ПОЛУЧЕН ОТВЕТ ОТ YANDEXGPT")
        logger.info("=" * 60)
        
        logger.info(f"⏱ Время выполнения: {duration:.2f} сек")
        logger.info(f"📊 HTTP статус: {response.status_code}")
        logger.info(f"📊 Размер ответа: {len(response.text)} байт")
        
        # Логируем заголовки ответа
        logger.info("📋 Заголовки ответа:")
        for header, value in response.headers.items():
            logger.info(f"   {header}: {value}")
        
        # Логируем полный текст ответа (особенно важно при ошибках)
        logger.info("📦 Полный текст ответа:")
        logger.info(f"\n{response.text}")
        
        # Проверяем HTTP статус
        if response.status_code != 200:
            logger.error(f"❌ ОШИБКА HTTP: {response.status_code}")
            
            # Пытаемся распарсить JSON с ошибкой
            try:
                error_data = response.json()
                logger.error("📊 JSON ошибки:")
                logger.error(json.dumps(error_data, ensure_ascii=False, indent=2))
                
                # Извлекаем понятное сообщение об ошибке
                error_message = error_data.get('message', 'Неизвестная ошибка')
                error_code = error_data.get('code', 'UNKNOWN')
                
                logger.error(f"🚨 Код ошибки: {error_code}")
                logger.error(f"🚨 Сообщение: {error_message}")
                
                # Возвращаем понятное сообщение пользователю
                if response.status_code == 400:
                    return f"❌ Ошибка в запросе (400): {error_message}"
                elif response.status_code == 401:
                    return "❌ Ошибка авторизации (401). Проверьте API-ключ."
                elif response.status_code == 403:
                    return f"❌ Доступ запрещен (403): {error_message}"
                elif response.status_code == 404:
                    return "❌ Ресурс не найден (404). Проверьте Folder ID и имя модели."
                elif response.status_code == 429:
                    return "⏳ Слишком много запросов (429). Попробуйте через минуту."
                else:
                    return f"⚠️ Ошибка сервера ({response.status_code}): {error_message}"
                    
            except json.JSONDecodeError:
                logger.error("❌ Ответ не в формате JSON")
                return f"⚠️ Ошибка сервера ({response.status_code}): {response.text[:200]}"
        
        # ========== ОБРАБОТКА УСПЕШНОГО ОТВЕТА ==========
        logger.info("✅ Успешный ответ получен, парсим JSON...")
        
        # Парсим JSON ответ
        try:
            result = response.json()
            
            # Логируем структуру ответа для отладки
            logger.info("📊 Структура JSON ответа:")
            logger.info(json.dumps(result, ensure_ascii=False, indent=2))
            
            # Проверяем наличие ожидаемых полей
            if 'result' not in result:
                logger.error("❌ В ответе нет поля 'result'")
                logger.error(f"Полная структура: {result}")
                return "⚠️ Неожиданный формат ответа от AI"
            
            if 'alternatives' not in result['result']:
                logger.error("❌ В ответе нет поля 'result.alternatives'")
                return "⚠️ Неожиданный формат ответа от AI"
            
            if not result['result']['alternatives']:
                logger.error("❌ Список alternatives пуст")
                return "⚠️ AI не смог сгенерировать ответ"
            
            # Извлекаем текст ответа
            answer_text = result['result']['alternatives'][0]['message']['text']
            logger.info(f"✅ Ответ AI получен ({len(answer_text)} символов)")
            
            return answer_text.strip()
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON: {e}")
            logger.error(f"📦 Сырой ответ: {response.text[:500]}...")
            return "⚠️ Ошибка обработки ответа от AI"
        except KeyError as e:
            logger.error(f"❌ Отсутствует ожидаемое поле в JSON: {e}")
            logger.error(f"📦 Полный ответ: {result}")
            return "⚠️ Неожиданный формат ответа от AI"
    
    except requests.exceptions.Timeout:
        logger.error("⏱ Таймаут запроса (30 секунд)")
        return "⏱ AI-сервис не ответил вовремя. Попробуйте позже."
    except requests.exceptions.ConnectionError as e:
        logger.error(f"🔌 Ошибка соединения: {e}")
        return "🔌 Ошибка соединения с AI-сервисом."
    except requests.exceptions.RequestException as e:
        logger.error(f"🚨 Ошибка запроса: {type(e).__name__}: {e}")
        return "⚠️ Ошибка при обращении к AI-сервису."
    except Exception as e:
        logger.error(f"💥 Неожиданная ошибка: {type(e).__name__}: {e}")
        return "⚠️ Произошла непредвиденная ошибка."

# ========== TELEGRAM ОБРАБОТЧИКИ ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команд /start и /help"""
    logger.info(f"👋 Команда /start от {message.from_user.id}")
    
    welcome_text = """
👋 Привет, чем могу помочь?.

📋 **Доступные команды:**
/start или /help - это сообщение
/status - статус бота и подключения
/test - тестовая команда
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
    
    # Проверяем конфигурацию
    config_status = []
    
    if TELEGRAM_TOKEN:
        config_status.append("✅ Telegram Token")
    else:
        config_status.append("❌ Telegram Token")
    
    if YANDEX_API_KEY:
        config_status.append("✅ Yandex API Key")
    else:
        config_status.append("❌ Yandex API Key")
    
    if YANDEX_FOLDER_ID:
        config_status.append("✅ Yandex Folder ID")
    else:
        config_status.append("❌ Yandex Folder ID")
    
    status_text = f"""
📊 **Статус бота:**

• **Telegram API:** {'✅ Подключен' if TELEGRAM_TOKEN else '❌ Ошибка'}
• **YandexGPT API:** {'✅ Настроен' if YANDEX_API_KEY and YANDEX_FOLDER_ID else '❌ Не настроен'}
• **Модель:** {YANDEX_MODEL}
• **Сервер:** Render.com
• **Время:** {datetime.now().strftime('%H:%M:%S')}

🔧 **Конфигурация:**
{chr(10).join(config_status)}
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
    
    test_text = "✅ Бот работает! Тестовое сообщение получено."
    
    if YANDEX_API_KEY and YANDEX_FOLDER_ID:
        test_text += "\n🤖 YandexGPT подключен и готов к работе!"
    else:
        test_text += "\n⚠️ YandexGPT не настроен. Проверьте переменные окружения."
    
    try:
        bot.reply_to(message, test_text)
        logger.info(f"✅ Тестовое сообщение отправлено")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки тестового сообщения: {e}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """Основной обработчик сообщений"""
    user_id = message.from_user.id
    message_text = message.text
    
    logger.info("=" * 60)
    logger.info(f"📩 Новое сообщение от {user_id}: {message_text}")
    logger.info("=" * 60)
    
    # Проверяем наличие ключа YandexGPT
    if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
        logger.warning("⚠️ Ключ YandexGPT не настроен. Включаю эхо-режим.")
        try:
            response_text = f"🔁 Эхо: {message_text}\n\nℹ️ Для работы с AI настройте YANDEX_API_KEY и YANDEX_FOLDER_ID в Render."
            bot.reply_to(message, response_text)
            logger.info(f"✅ Эхо-сообщение отправлено")
        except Exception as e:
            logger.error(f"❌ Ошибка отправки эхо: {e}")
        return
    
    try:
        # Показываем индикатор "печатает"
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Получаем ответ от YandexGPT
        answer = ask_yandex_gpt(message_text)
        
        # Отправляем ответ пользователю
        if len(answer) > 4000:  # Ограничение Telegram
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
            
    except Exception as e:
        logger.error(f"💥 Ошибка обработки сообщения: {type(e).__name__}: {e}")
        bot.reply_to(message, "😕 Произошла ошибка при обработке запроса.")

# ========== FLASK РОУТЫ ==========
@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🤖 Telegram Bot с YandexGPT</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; text-align: center; }
            .status { background: #f0f8ff; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 600px; }
        </style>
    </head>
    <body>
        <h1>🤖 Telegram Bot с YandexGPT</h1>
        <div class="status">
            <h3>Статус: ✅ Активен</h3>
            <p>Бот работает с YandexGPT AI</p>
            <p>Для использования напишите боту в Telegram</p>
        </div>
        <p>Подробные логи доступны в панели Render</p>
    </body>
    </html>
    """

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик webhook от Telegram"""
    start_time = datetime.now()
    
    try:
        json_data = request.get_json()
        
        if not json_data:
            logger.error("❌ Пустой запрос от Telegram")
            return 'Bad Request', 400
        
        update_id = json_data.get('update_id', 'unknown')
        logger.info(f"📥 Webhook получен (ID: {update_id})")
        
        # Обрабатываем обновление
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
        
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Webhook обработан за {processing_time:.2f} сек")
        
        return 'OK', 200
        
    except Exception as e:
        logger.error(f"💥 Ошибка в webhook: {type(e).__name__}: {str(e)}")
        return 'Internal Server Error', 500

# ========== ЗАПУСК СЕРВЕРА ==========
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("🚀 ЗАПУСК TELEGRAM БОТА С YANDEXGPT")
    logger.info("=" * 60)
    
    # Проверяем конфигурацию при запуске
    config_ok = True
    
    if not TELEGRAM_TOKEN:
        logger.error("❌ TELEGRAM_TOKEN не найден!")
        config_ok = False
    else:
        logger.info(f"✅ TELEGRAM_TOKEN: {TELEGRAM_TOKEN[:15]}...")
    
    if not YANDEX_API_KEY:
        logger.error("❌ YANDEX_API_KEY не найден!")
        config_ok = False
    else:
        logger.info(f"✅ YANDEX_API_KEY: {YANDEX_API_KEY[:10]}...")
        logger.info(f"   Длина ключа: {len(YANDEX_API_KEY)} символов")
    
    if not YANDEX_FOLDER_ID:
        logger.error("❌ YANDEX_FOLDER_ID не найден!")
        config_ok = False
    else:
        logger.info(f"✅ YANDEX_FOLDER_ID: {YANDEX_FOLDER_ID}")
        logger.info(f"   Длина: {len(YANDEX_FOLDER_ID)} символов")
    
    logger.info(f"🤖 Модель: {YANDEX_MODEL}")
    logger.info("=" * 60)
    
    if not config_ok:
        logger.warning("⚠️ Бот запущен с неполной конфигурацией!")
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Веб-сервер запускается на порту {port}")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=False)

