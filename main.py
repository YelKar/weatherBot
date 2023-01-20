from time import sleep

from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton

from weather import Weather
from loguru import logger

import os
import sys


bot = TeleBot(os.environ.get("Weather_bot_TOKEN"), parse_mode="HTML")
w = Weather(os.environ.get(os.environ.get("Weather_bot_LINK") or "Weather_bot_Home"))


def out(context):
    time = context["time"].strftime("%d.%m.%Y__%H:%M:%S.%f")
    level = context["level"]
    message = context["message"].replace("\n", "\n\t")
    return f"{time} | {level} | {message}\n"


logger.remove()
logger.add(sys.stdout, format=out)


def create_keyboard():
    global keyboard
    global days
    days = {
        f"{day['day_number']} {day['month'].title()}": day for day in w.get_all()
    }
    keyboard = [
        ["Обновить клавиатуру"],
        ["Сегодня", "Завтра"],
        list(days.keys())[2:6],
        list(days.keys())[6:],
        [f"{d} дня" for d in range(2, 5)] + ["5 дней"],
        [f"{d} дней" for d in range(6, 11)]
    ]


days = {}
keyboard = []
create_keyboard()


@bot.message_handler(commands=["start", "help", "старт", "помощь"])
def start(message: Message):
    k = ReplyKeyboardMarkup(True)
    for row in keyboard:
        k.row(*[KeyboardButton(b) for b in row])
    hello = "Здравствуйте! Я расскажу вам о погоде\n" \
            "Я отправил вам клавиатуру\n" \
            "При нажатии на клавиатуру вам будет приходить погода на выбранный день\n\n" \
            "/start и /help покажут справку"
    bot.reply_to(message, hello)
    bot.send_message(
        message.chat.id,
        "Нажмите на кнопку на клавиатуре ↓",
        reply_markup=k
    )
    logger.info(f"Отправлена справка пользователю {message.from_user.id}")

@bot.message_handler(commands=["id"])
def get_id(message: Message):
    bot.reply_to(message, message.from_user.id)

@bot.message_handler(regexp=keyboard[0][0])
def update_keyboard(message: Message):
    create_keyboard()
    k = ReplyKeyboardMarkup(True)
    for row in keyboard:
        k.row(*[KeyboardButton(b) for b in row])
    send_message = bot.send_message(message.chat.id, "Клавиатура обновлена", reply_markup=k)


@bot.message_handler(func=lambda m: in_keyboard(m.text, keyboard))
def get(message: Message):
    text = message.text
    place = w.soup.select_one('h1.title').text.split(" — ")[-1]
    if text in ["Сегодня", "Завтра"]:
        answer = text_from_day(w.get_day(message.text))
    elif "дн" in text:
        num = int(text.split()[0])
        answer = f"{'_' * 50}\n\n".join([text_from_day(day) for day in list(days.values())[:num]])
    elif text in days:
        answer = text_from_day(days[text])
    else:
        logger.info(f"Пользователь {message.from_user.id} сделал неверное обращение")
        return
    bot.reply_to(message, f"<b><u>{f'Погода на {message.text}'.upper()}</u></b>\n{place}\n\n{answer}")
    logger.info(f"Пользователь {message.from_user.id} получил погоду на {text.lower()}")


def in_keyboard(text: str, keyboard: list):
    for row in keyboard:
        if text in row:
            return True
    return False


def text_from_day(day: dict):
    weather_icon = {
        "Ясно": "☀🌙",
        "Малооблачно": ("🌤", "🌙☁"),
        "Облачно с прояснениями": "⛅⛅",
        "Небольшой дождь": "🌧🌧",
        "Пасмурно": "☁☁",
        "Дождь": ("🌧🌧",) * 2,
        "Ливни": ("🌧🌧🌧🌧",) * 2,
        "Ливень": ("🌧🌧🌧🌧",) * 2,
        "Снег": ("🌨️🌨️",) * 2,
        "Дождь со снегом": ("🌧🌨️",) * 2,
        "Небольшой снег": ("🌨️",) * 2,
    }
    ans = f"<b><u>{day['day_number']} {day['month'].title()}, {day['day_name'].title()}</u></b>\n"
    try:
        ans += "".join(
            f'<b>{day_part.title():7} {weather_icon[weather["weather"]][day_part == "ночью"]}</b> \n'
            f'от {weather["min_temp"]:3} до {weather["max_temp"]:3} -> '
            f'{weather["weather"]}\n'
            for day_part, weather in day["day"].items()
        )
    except KeyError as err:
        logger.error(f'Нет эмоджи для погоды "{err.args[0]}"')
    return ans
