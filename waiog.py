import sys
import asyncio
from time import time
from aiohttp import web

from aiogram import F, Router
from aiogram.filters.command import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from confy import WEBHOOK_URL, WEBHOOK_URL_PATH, WEBHOOK_HOST, WEBHOOK_PORT
from event import start, show_help, incoming, go_vote, go_inputs
from stats import show_stats, show_top, show_words, show_words_rate, show_comms, show_games
from utils import dp, bot, try_answer_callback_query, dope_send_message
from utils import logger

router = Router()

def get_prefix(from_user):
    userid = from_user.id
    uname = from_user.username
    fname = from_user.first_name
    return f"{userid} {fname} @{uname}"


@router.message(Command("start"))
@dp.message(Command("start"))
async def docall(message):
    start_time = time()
    userid = message.from_user.id
    pref = get_prefix(message.from_user)
    logger.debug(f"{pref} select START ...")
    await dope_send_message(f": : {pref} select START")
    await start(userid, message)
    logger.info(f"{pref} select START :: {time() - start_time}")


@router.message(Command("stats"))
@dp.message(Command("stats"))
async def docall(message):
    start_time = time()
    pref = get_prefix(message.from_user)
    logger.debug(f"{pref} select STATS ...")
    await show_stats(message.from_user.id)
    logger.info(f"{pref} select STATS :: {time() - start_time}")


@router.message(Command("help"))
@dp.message(Command("help"))
async def docall(message):
    start_time = time()
    userid = message.from_user.id
    pref = get_prefix(message.from_user)
    logger.debug(f"{pref} select HELP ...")
    await show_help(userid)
    logger.info(f"{pref} select HELP :: {time() - start_time}")


@router.message(Command("top10"))
@dp.message(Command("top10"))
async def docall(message):
    start_time = time()
    userid = message.from_user.id
    pref = get_prefix(message.from_user)
    logger.debug(f"{pref} select TOP10 ...")
    await show_top(userid, False)
    logger.info(f"{pref} select TOP10 :: {time() - start_time}")


@router.message(Command("top7"))
@dp.message(Command("top7"))
async def docall(message):
    start_time = time()
    userid = message.from_user.id
    pref = get_prefix(message.from_user)
    logger.debug(f"{pref} select TOP7 ...")
    await show_top(userid, True)
    logger.info(f"{pref} select TOP7 :: {time() - start_time}")


@router.message(Command("words"))
@dp.message(Command("words"))
async def docall(message):
    start_time = time()
    userid = message.from_user.id
    pref = get_prefix(message.from_user)
    logger.debug(f"{pref} select WORDS ...")
    await show_words(userid)
    logger.info(f"{pref} select WORDS :: {time() - start_time}")


@router.message(Command("games"))
@dp.message(Command("games"))
async def docall(message):
    start_time = time()
    userid = message.from_user.id
    pref = get_prefix(message.from_user)
    logger.debug(f"{pref} select GAMES ...")
    await show_games(userid)
    logger.info(f"{pref} select GAMES :: {time() - start_time}")


@router.message(Command("comms"))
@dp.message(Command("comms"))
async def docall(message):
    start_time = time()
    userid = message.from_user.id
    pref = get_prefix(message.from_user)
    logger.debug(f"{pref} select UTILS ...")
    await show_comms(userid)
    logger.info(f"{pref} select UTILS :: {time() - start_time}")


@router.message(Command("rates"))
@dp.message(Command("rates"))
async def docall(message):
    start_time = time()
    userid = message.from_user.id
    pref = get_prefix(message.from_user)
    logger.debug(f"{pref} select RATES ...")
    await show_words_rate(userid)
    logger.info(f"{pref} select RATES :: {time() - start_time}")


@router.message(F.text)
@dp.message(F.text)
async def docall(message):
    start_time = time()
    pref = get_prefix(message.from_user)
    logger.debug(f"{pref} input {message.text} ...")
    await incoming(message.chat.id, message.text)
    logger.info(f"{pref} input {message.text} :: {time() - start_time}")


@router.callback_query()
@dp.callback_query()
async def docall(query):
    start_time = time()
    userid = query.message.chat.id
    messid = query.message.message_id
    button = query.data
    pref = get_prefix(query.message.chat)
    logger.debug(f"{pref} button {button} ...")

    strips = button.split('_')
    if len(strips) > 1:
        button = strips[0]
        chosen = strips[1]
        if button == "press":
            await go_inputs(userid, chosen)
            await try_answer_callback_query(query.id)
        if button == "vote":
            await go_vote(userid, chosen, strips[2], query.message.text, messid)
            await try_answer_callback_query(query.id, 'Голос принят, спасибо')
    logger.info(f"{pref} button {query.data} :: {time() - start_time}")


async def start_longpolling():
    await dp.start_polling(bot, skip_updates=False)


async def on_startup(bot):
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_URL_PATH)


def start_webhook():
    dp.include_router(router)
    dp.startup.register(on_startup)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_URL_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host=WEBHOOK_HOST, port=WEBHOOK_PORT)


if __name__ == '__main__':
    if len(sys.argv) > 1 and (sys.argv[1] == '--polling'):
        print('wordie <><> polling <><> mode started')
        asyncio.run(start_longpolling())
    else:
        print('wordie aiobot V^V^ webhook V^V^ mode started')
        start_webhook()
