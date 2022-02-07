import asyncio
from datetime import datetime

import aiomysql

from confy import DBUSER, DBPASS
from utils import logger, charline_default

ONE, ALL = (1, 0)


async def create_my_pool():
    loop = asyncio.get_event_loop()
    pool = await aiomysql.create_pool(
        host="localhost", user=DBUSER, password=DBPASS,
        db="wordie", loop=loop, autocommit=True, pool_recycle=120)
    return pool


async def try_commit(query, data):
    async with aiomysql.connect(host="localhost", user=DBUSER, password=DBPASS,
                                db="wordie") as connection:
        try:
            async with connection.cursor() as cursor:
                await cursor.execute(query, data)
            await connection.commit()
        except aiomysql.Error as err:
            logger.error(f'ERROR COMMIT {err}, {query}, {data}')


async def try_fetch(query, data, is_single):
    pl = await create_my_pool()
    async with pl.acquire() as connection:
        try:
            async with connection.cursor() as cursor:
                if is_single:
                    await cursor.execute(query, data)
                    data = await cursor.fetchone()
                else:
                    await cursor.execute(query, data)
                    data = await cursor.fetchall()
                return data
        except aiomysql.Error as err:
            logger.error(f'ERROR FETCH {err}, {query}, {data}')


async def create_user(userid, name, nick):
    await try_commit(
        "INSERT INTO users (userid, username, usernick, charline, state, games, wins, "
        "streaks, maxstreak, points, maxpoints) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (userid, name, nick, charline_default, 0, 0, 0, 0, 0, 0, 0))


async def check_user(userid):
    data = await try_fetch("SELECT userid FROM users WHERE userid=%s", (userid,), ONE)
    return data


async def get_word(_id):
    data = await try_fetch("SELECT word FROM crux5 WHERE id=%s", (_id,), ONE)
    word = data[0]
    return word


async def get_word_info(word):
    data = await try_fetch("SELECT shared, entered, votepro, votecontra FROM crux5 WHERE word=%s", (word,), ONE)
    return data


async def get_all_word_info():
    data = await try_fetch("SELECT word, shared, entered, votepro, votecontra FROM crux5"
                           " WHERE shared>0 OR votepro>0 OR votecontra>0 OR entered>0", (), ALL)
    return data


async def set_word_info(word, shared, entered, votepro, votecontra):
    await try_commit("UPDATE crux5 SET shared=%s, entered=%s, votepro=%s, votecontra=%s WHERE word=%s",
                     (shared, entered, votepro, votecontra, word))


async def set_word(userid, word, cruxid):
    await try_commit("UPDATE users SET cruxword=%s, cruxid=%s WHERE userid=%s", (word, cruxid, userid))


async def check_word(word):
    data = await try_fetch("SELECT word, usages FROM dict5 WHERE word=%s", (word,), ONE)
    return data


async def get_word_usages():
    data = await try_fetch("SELECT word, usages FROM dict5 WHERE usages>0", (), ALL)
    return data


async def get_comms():
    data = await try_fetch("SELECT word, usages FROM comm5 WHERE usages>1", (), ALL)
    return data


async def up_word_usages(word, usages):
    await try_commit("UPDATE dict5 set usages=%s WHERE word=%s", (usages, word))


async def get_crux(userid):
    data = await try_fetch("SELECT cruxword, cruxid, charline, prevmess, state FROM users WHERE userid=%s",
                           (userid,), ONE)
    return data


async def set_user(userid, chline, messid, state):
    await try_commit("UPDATE users SET charline=%s, prevmess=%s, state=%s WHERE userid=%s",
                     (chline, messid, state, userid))


async def set_blank_user(userid):
    await try_commit("UPDATE users SET cruxword=%s, cruxid=%s, charline=%s, "
                     "prevmess=%s, state=%s, inputs=%s, lastupd=%s WHERE userid=%s",
                     ('', 0, charline_default, 0, 1, '', datetime.now(), userid))


async def set_inputs(userid, inputs):
    await try_commit("UPDATE users SET inputs=%s WHERE userid=%s", (inputs, userid))


async def get_inputs(userid):
    data = await try_fetch("SELECT inputs FROM users WHERE userid=%s", (userid,), ONE)
    return data[0]


async def set_stats(userid, games, wins, streaks, maxstreak, points, maxpoints):
    await try_commit("UPDATE users SET games=%s, wins=%s, streaks=%s, "
                     "maxstreak=%s, points=%s, maxpoints=%s WHERE userid=%s",
                     (games, wins, streaks, maxstreak, points, maxpoints, userid))


async def get_stats(userid):
    data = await try_fetch("SELECT games, wins, streaks, maxstreak, points, maxpoints "
                           "FROM users WHERE userid=%s", (userid,), ONE)
    return data


async def add_game(userid, cruxid, crux):
    tstamp = datetime.now()
    await try_commit("INSERT into games (userid, cruxid, crux, tstamp) VALUES (%s,%s,%s,%s) ",
                     (userid, cruxid, crux, tstamp))


async def set_moves(userid, crux, moves, words):
    logger.debug(f'{userid} SET MOVES {crux} {moves} {words}')
    await try_commit("UPDATE games SET moves=%s, words=%s WHERE userid=%s AND crux=%s", (moves, words, userid, crux))


async def get_moves(userid, crux):
    data = await try_fetch("SELECT moves, words FROM games WHERE userid=%s AND crux=%s", (userid, crux), ONE)
    return data


async def get_games(userid):
    data = await try_fetch("SELECT cruxid FROM games WHERE userid=%s", (userid,), ALL)
    logger.debug(f'{userid} played  {len(data)} GAMES')
    return data


async def get_players(day_from):
    data = await try_fetch("SELECT userid, username, games, wins, streaks, maxstreak, points "
                           "FROM users WHERE games>4 AND lastupd>%s", (day_from, ), ALL)
    return data


async def get_comm_word(word):
    data = await try_fetch("SELECT usages FROM comm5 WHERE word=%s", (word,), ONE)
    return data


async def add_comm_word(word):
    await try_commit("INSERT INTO comm5 (word, usages) VALUES (%s,%s)", (word, 1))


async def upd_comm_word(word, usages):
    await try_commit("UPDATE comm5 SET usages=%s where word=%s", (usages, word))


async def get_games_from(tstamp):
    data = await try_fetch("select users.username, count(games.crux) FROM games "
                           "LEFT JOIN users ON users.userid=games.userid WHERE tstamp>%s "
                           "GROUP BY username ORDER BY count(games.crux) DESC;", (tstamp,), ALL)
    return data
