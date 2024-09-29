import os
import requests
import json
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
from aiogram import F

# Загружаем переменные окружения
load_dotenv()

# Токен вашего бота
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


# Функция для парсинга страницы Gismeteo и извлечения температуры из JavaScript
def get_weather_from_gismeteo(city: str) -> str:
    # Формируем URL для поиска по названию города на Gismeteo
    search_url = f"https://www.gismeteo.ru/search/{city}/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Выполняем GET-запрос к странице поиска
        search_response = requests.get(search_url, headers=headers)
        search_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Ошибка при получении данных о погоде: {str(e)}"

    # Парсим HTML-ответ
    soup = BeautifulSoup(search_response.text, 'html.parser')

    # Ищем ссылку на страницу города с прогнозом погоды
    city_link = soup.find('a', {'class': 'catalog-group-link'})

    if city_link:
        # Формируем URL для страницы погоды города
        city_weather_url = f"https://www.gismeteo.ru{city_link['href']}"

        try:
            # Делаем запрос на страницу прогноза погоды для города
            city_response = requests.get(city_weather_url, headers=headers)
            city_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f"Ошибка при получении данных о погоде: {str(e)}"

        # Парсим страницу прогноза погоды
        soup = BeautifulSoup(city_response.text, 'html.parser')

        # Ищем строку с JavaScript-объектом с помощью string
        script_tag = soup.find('script', string=lambda s: s and "M.state.weather.cw" in s)

        if script_tag:
            # Находим начало и конец объекта в строке JavaScript
            script_content = script_tag.string
            start = script_content.find('M.state.weather.cw = ') + len('M.state.weather.cw = ')
            end = script_content.find('};', start) + 1
            weather_data_str = script_content[start:end]

            # Парсим JSON-строку
            try:
                weather_data = json.loads(weather_data_str)
                temp = weather_data['temperatureAir'][0]  # Берем текущую температуру
                return f"Текущая температура в {city}: {temp}°C"
            except (json.JSONDecodeError, KeyError) as e:
                return "Ошибка при разборе данных о погоде."
        else:
            return "Не удалось найти данные о погоде на странице."
    else:
        return "Не удалось найти город. Попробуйте ввести корректное название."


# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Отправь мне название города, чтобы узнать текущую температуру.")


# Обработчик текста (названия города)
@dp.message(F.text)
async def send_weather(message: Message):
    city = message.text.strip()

    # Получаем данные о погоде с Gismeteo
    weather_info = get_weather_from_gismeteo(city)
    await message.answer(weather_info)


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
