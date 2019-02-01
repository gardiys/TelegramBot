import telebot
from telebot import types
from collections import defaultdict
from storage import Store
from settings import TOKEN
token = TOKEN

START, ADDRESS, PHOTO, LOCATION = range(4)
bot = telebot.TeleBot(token)
commands = ['add', 'list', 'reset', 'help']
USER_STATE = defaultdict(lambda: START)
PLACES = defaultdict(lambda: {})
STORAGE = Store()


def update_place(user_id, key, value):
    PLACES[user_id][key] = value


def get_place(user_id):
    return PLACES[user_id]


def save_to_database(key, items):
    number = 1
    while STORAGE.already_exist(f"{key}:{number}"):
        number += 1
    STORAGE.set_items(key, items, number)


def get_from_database(key):
    return STORAGE.get_item(key)


def reset_all_data():
    STORAGE.reset_data()


def get_state(message):
    return USER_STATE[message.chat.id]


def update_state(message, state):
    USER_STATE[message.chat.id] = state


def create_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=4)
    buttons = [types.InlineKeyboardButton(text=c, callback_data=c)
               for c in commands]
    keyboard.add(*buttons)
    return keyboard


@bot.callback_query_handler(func=lambda x: True)
def callback_handler(callback_query):
    message = callback_query.message
    text = callback_query.data
    if text == 'add':
        handle_add(message)
    elif text == 'list':
        handle_list(message)
    elif text == 'reset':
        handle_reset(message)
    elif text == 'help':
        handle_help(message)


@bot.message_handler(commands=['start'])
def handle_start(message):
    response_text = "Привет! Я умею сохранять интересные места!\n" \
                    "Для вывода списка команд вызови /help"
    bot.send_message(chat_id=message.chat.id, text=response_text)


@bot.message_handler(commands=['help'])
def handle_help(message):
    response_text = "Вот список команд, которые мне знакомы:\n" \
                    "/add - Добавить новое интересное местечко;\n" \
                    "/list - Отобразить 10 последних сохраненных ранее мест;\n" \
                    "/reset - Удалить все сохраненные ранее места;\n" \
                    "/help - Вывести список комманд;\n" \
                    "Так же ты можешь отправить мне свою геолокацию, а я покажу тебе " \
                    "ближайшие места, которые ты попросил сохранить:)"
    keyboard = create_keyboard()
    bot.send_message(chat_id=message.chat.id, text=response_text, reply_markup=keyboard)


@bot.message_handler(commands=['add'], func=lambda message: get_state(message) == START)
def handle_add(message):
    bot.send_message(message.chat.id, text='Окей, хочешь добавить новое место? Хорошо:)\n'
                                           'Введи его адрес:')
    update_state(message, ADDRESS)


@bot.message_handler(func=lambda message: get_state(message) == ADDRESS)
def handle_step_address(message):
    #adress
    update_place(message.chat.id, 'adress', message.text)
    bot.send_message(message.chat.id, text='Супер! А теперь пришли мне фото места:')
    update_state(message, PHOTO)


@bot.message_handler(content_types=['photo'], func=lambda message: get_state(message) == PHOTO)
def handle_step_photo(message):
    #photo
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.reply_to(message, e)

    update_place(message.chat.id, 'photo', downloaded_file)
    bot.send_message(message.chat.id, text='Отлично, осталось отправить геолокацию:')
    update_state(message, LOCATION)


@bot.message_handler(content_types=['location'], func=lambda message: get_state(message) == LOCATION)
def handle_step_location(message):
    #location
    update_place(message.chat.id, 'location', message.location)
    try:
        save_to_database(message.chat.id, get_place(message.chat.id))
    except Exception as e:
        bot.reply_to(message, e)
    bot.send_message(message.chat.id, text='Отлично, я всё сохранил!')
    update_state(message, START)


@bot.message_handler(commands=['list'])
def handle_list(message):
    for i in range(1, 11):
        if not STORAGE.already_exist(f"{message.chat.id}:{i}"):
            break
        info = get_from_database(f"{message.chat.id}:{i}")
        bot.send_message(message.chat.id, text=f"Адрес: {info['adress']}")
        bot.send_photo(message.chat.id, info['photo'])
        bot.send_location(message.chat.id, info['location'].latitude,
                          info['location'].longitude)


@bot.message_handler(commands=['reset'])
def handle_reset(message):
    bot.send_message(message.chat.id, "Хорошо, сейчас всё удалю)")
    reset_all_data()
    bot.send_message(message.chat.id, "Удалил!")


@bot.message_handler(content_types=['location'])
def handle_location(message):
    bot.send_message(message.chat.id, text="Простите, но платные API гугла это уже слишком:(")


bot.polling()