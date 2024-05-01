from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ContentType
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import requests
import json

# Инициализация бота и диспетчера
API_TOKEN = 'TOKEN'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    # Создаем кнопку для отправки контакта
    contact_button = KeyboardButton('Отправить контакт', request_contact=True)
    contact_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(contact_button)
    await message.reply("Привет! Отправь мне свой контакт, и я найду тебя в базе данных.",
                        reply_markup=contact_keyboard)


@dp.message_handler(content_types=ContentType.CONTACT)
async def handle_contact(message: types.Message):
    contact = message.contact
    phone_number = contact.phone_number
    url = "http://127.0.0.1:5000"

    response = requests.get(f"{url}/users/{phone_number}")
    decoded_data = json.loads(response.text)

    # Форматирование данных для вывода
    formatted_text = "\n".join([f"{key}: {value}" for key, value in decoded_data.items()])

    await bot.send_message(message.chat.id, formatted_text)
    contact_button = KeyboardButton('Отправить контакт', request_contact=True)
    contact_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(contact_button)
    await bot.send_message(message.chat.id, "Отправь мне свой контакт, и я найду тебя в базе данных.", reply_markup=contact_keyboard)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

