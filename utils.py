import logging
from time import sleep

from aiogram import Bot, Dispatcher, exceptions, types

from confy import API_TOKEN, DOPE_TOKEN, LOGTOFILE, LOGLEVEL

charline_default = 'абвгдежзийклмнопрстуфхцчшщъыьэюя'

logger = logging.getLogger('wordiebot')
formatter = logging.Formatter('[%(asctime)s] %(levelname)-7s %(message)s', '%m-%d %H:%M:%S')
handler = logging.FileHandler('wordiebot.log') if LOGTOFILE else logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(LOGLEVEL)
logger.info('=' * 24)
logger.info("==== START LOGGING  ====")


bot = Bot(token=API_TOKEN)
dopebot = Bot(token=DOPE_TOKEN)
dp = Dispatcher()


def get_kb(chline):
    row_width=8
    button = types.InlineKeyboardButton
    button_list = []
    button_row = []
    for i in range(0, len(chline)):
        if chline[i] in charline_default + '_':
            btnchar = chline[i]
        else:
            btnchar = '•' + chline[i]
        button_row.append(button(text=btnchar, callback_data='press_' + charline_default[i]))

        if i>0 and (i+1)%row_width == 0:
            button_list.append(button_row)
            button_row = []

    return types.InlineKeyboardMarkup(inline_keyboard=button_list)


def get_vote_kb(word):
    button = types.InlineKeyboardButton
    button1 = button(text="Интересное! 💚", callback_data=f"vote_{word}_pro")
    button2 = button(text="Не понравилось 💩", callback_data=f"vote_{word}_contra")
    return types.InlineKeyboardMarkup(inline_keyboard=[[button1, button2]])


async def dope_send_message(message):
    try:
        await dopebot.send_message(chat_id=1146011385, text=message,
                                   parse_mode='html', disable_notification=True)
    except Exception as err:
        print('DOPE ERR', err)


async def try_send_message(userid, message, markup=None):
    message_id = 0
    try:
        message_obj = await bot.send_message(chat_id=userid, text=message, reply_markup=markup,
                                             parse_mode='html', disable_notification=True)
        message_id = message_obj.message_id
    except exceptions.TelegramNotFound as err:
        logger.warning(f'{userid} ! send_message ChatNotFound exception :: {err}')
    except exceptions.TelegramForbiddenError as err:
        logger.warning(f'{userid} ! send_message ForbiddenError exception :: {err}')
    except exceptions.TelegramRetryAfter as err:
        logger.warning(f'{userid} ! send_message RetryAfter exception :: {err}')
        retry_after = err.timeout
        sleep(retry_after)
        await try_send_message(userid, "Извините, я перегружен сообщениями. Пожалуйста, перейдите, в моего дублёра"
                                       " @wordiegamebot или зайдите позже. Благодарю за понимание!")
        await try_send_message(userid, message, markup)
    except exceptions.TelegramBadRequest as err:
        logger.warning(f'{userid} ! send_message BadRequest exception :: {err}')
    except exceptions.TelegramNetworkError as err:
        logger.warning(f'{userid} ! send_message NetworkError exception :: {err}')
    return message_id


async def try_edit_message_text(text, userid, message_id, markup=None):
    try:
        await bot.edit_message_text(text=text, chat_id=userid, message_id=message_id,
                                    parse_mode="html", reply_markup=markup)
    except exceptions.TelegramBadRequest as err:
        logger.warning(f'{userid} ! edit_message BadRequest exception :: {err} {text} {message_id}')
    except exceptions.TelegramNetworkError as err:
        logger.warning(f'{userid} ! edit_message NetworkError exception :: {err}')
    return False


async def try_delete_message(userid, message_id):
    if message_id:
        try:
            await bot.delete_message(chat_id=userid, message_id=message_id)
        except exceptions.TelegramBadRequest as err:
            logger.warning(f'{userid} ! delete_message BadRequest exception :: {err}')


async def try_answer_callback_query(query_id, text=""):
    if query_id:
        try:
            await bot.answer_callback_query(query_id, text=text)
        except exceptions.TelegramBadRequest as err:
            logger.warning(f'{query_id} ! answer_callback_query BadRequest exception :: {err}')
