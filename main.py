import logging
import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Message

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account

CHANNEL_ID = os.getenv('CHANNEL_ID')

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

async def delete_pinned_message():
    try:
        # Получаем информацию о чате (включая последнее закрепленное сообщение)
        chat = await bot.get_chat(CHANNEL_ID)
        
        await bot.unpin_all_chat_messages(CHANNEL_ID)
        logging.info("✅ Все закрепленные сообщения удалены.")
        
        if chat.pinned_message:
            pinned_message_id = chat.pinned_message.message_id

            # Удаляем само сообщение
            await bot.delete_message(CHANNEL_ID, pinned_message_id)
            logging.info(f"🗑 Сообщение {pinned_message_id} удалено из канала.")
                                    
    except Exception as e:
        logging.error(f"❌ Ошибка удаления закрепленных сообщений: {e}")
        
# Храним ID последнего сообщения
last_message_id = None

def get_value():    

    # Путь к JSON-файлу Service Account
    SERVICE_ACCOUNT_FILE = "service_account.json"

    SHEET_ID = "1WyCLramjiN1sm7oq1rTVXrUBVPnpHQJgKnGRzrOPG-U"
    SHEET_NAME = "resuming"
    RANGE = "D3:D8"

    # URL API для чтения данных из Google Sheets
    URL = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{SHEET_NAME}!{RANGE}"

    # Аутентификация через Service Account
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )

    # Создаем авторизованный запрос
    authed_session = AuthorizedSession(credentials)
    response = authed_session.get(URL)

    # Проверяем успешность запроса
    if response.status_code == 200:
        data = response.json()
        if "values" in data:
            all_winrate = data["values"][5][0]
            football_winrate = data["values"][2][0]
            hockey_winrate = data["values"][3][0]
            basketball_winrate = data["values"][0][0]
            tennis_winrate = data["values"][1][0]
            express_winrate = data["values"][4][0]
            return all_winrate, football_winrate, hockey_winrate, basketball_winrate, tennis_winrate, express_winrate
        else:
            print("Ячейка пуста или отсутствует.")
            return None
    else:
        print(f"Ошибка: {response.status_code}, {response.text}")
        return None

async def post_to_channel():
    global last_message_id
                        
    all_winrate, football_winrate, hockey_winrate, basketball_winrate, tennis_winrate, express_winrate = get_value()
    
    if all_winrate or football_winrate or hockey_winrate or basketball_winrate or tennis_winrate or express_winrate:
        text = f"""
WINRATE 📈

общий - {all_winrate}

🔽🔽🔽

⚽️ футбол - {football_winrate}

🏒 хоккей - {hockey_winrate}

🏀 баскетбол - {basketball_winrate}

🎾 теннис - {tennis_winrate}

🎲 экспресс - {express_winrate}
        """

        try:
            # Отправляем сообщение в канал
            msg = await bot.send_message(CHANNEL_ID, text)
    
            # Закрепляем сообщение
            await bot.pin_chat_message(CHANNEL_ID, msg.message_id)
            
            # Удаляем предыдущее сообщение, если оно было
            if last_message_id:
                try:
                    await bot.delete_message(CHANNEL_ID, last_message_id)
                except Exception as e:
                    logging.warning(f"Не удалось удалить сообщение: {e}")

            # Обновляем ID последнего сообщения
            last_message_id = msg.message_id
            logging.info(f"Сообщение отправлено: {text}")
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения: {e}")

@dp.channel_post()
async def delete_pin_notifications(message: Message):
    global last_pinned_by_bot
    if message.pinned_message:
        try:            
            if 'WINRATE' in message.pinned_message.text:
                await bot.delete_message(CHANNEL_ID, message.message_id)
                logging.info(f"🗑 Удалено системное уведомление о закрепе: {message.message_id}")
        except Exception as e:
            logging.error(f"❌ Ошибка удаления уведомления: {e}")
            
async def scheduler():
    while True:
        await post_to_channel()
        await asyncio.sleep(int(os.getenv('INTERVAL')))

# Запуск бота
async def main():
    await delete_pinned_message()
    logging.basicConfig(level=logging.INFO)
    asyncio.create_task(scheduler())  # Запускаем задачу по расписанию
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
