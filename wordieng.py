import logging
import time
from datetime import datetime
from random import choices

import cherrypy
import telebot
from mysql.connector import connect, Error
from telebot import types

from config import API_TOKEN, DBUSER, DBPASS, LOGTOFILE, cherrypy_conf

bot = telebot.TeleBot(token=API_TOKEN)

charline_default = 'abcdefghijklmnopqrstuvwxyz'

logger = logging.getLogger('wordiebot')
formatter = logging.Formatter('[%(asctime)s] %(levelname)-7s %(message)s', '%m-%d %H:%M:%S')
handler = logging.FileHandler('wordiengbot.log') if LOGTOFILE else logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.info('=' * 24)
logger.info("==== START LOGGING  ====")


def get_kb(chline):
    kb = types.InlineKeyboardMarkup(row_width=7)
    button = types.InlineKeyboardButton
    charlines = (chline[:7], chline[7:13], chline[13:19], chline[19:26])
    j = -1
    for chline in charlines:
        button_list = []
        for i in range(0, len(chline)):
            j += 1
            if chline[i] in charline_default + '_':
                btnchar = chline[i]
            else:
                btnchar = '•' + chline[i]
            button_list.append(button(text=btnchar, callback_data='press_' + charline_default[j]))
        if j == 12:
            button_list.append(button(text='Del', callback_data='press_DEL'))
        elif j == 18:
            button_list.append(button(text='Clr', callback_data='press_CLR'))
        kb.add(*button_list)
    return kb


def get_vote_kb(word):
    keyboard_markup = types.InlineKeyboardMarkup(row_width=2)
    button = types.InlineKeyboardButton
    button1 = button(text="Vote PRO 💚", callback_data=f"vote_{word}_pro")
    button2 = button(text="Contra 💩", callback_data=f"vote_{word}_contra")
    keyboard_markup.add(button1, button2)
    return keyboard_markup


ONE, ALL = (1, 0)


def try_commit(query, data):
    try:
        with connect(host="localhost", user=DBUSER,
                     password=DBPASS, database="wordieng"
                     ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, data)
            connection.commit()
    except Error as err:
        logger.error(f'ERROR COMMIT {err}, {query}, {data}')


def try_fetch(query, data, is_single):
    try:
        with connect(host="localhost", user=DBUSER,
                     password=DBPASS, database="wordieng"
                     ) as connection:
            with connection.cursor() as cursor:
                if is_single:
                    cursor.execute(query, data)
                    data = cursor.fetchone()
                else:
                    cursor.execute(query, data)
                    data = cursor.fetchall()
                return data
    except Error as err:
        logger.error(f'ERROR FETCH {err}, {query}, {data}')


def create_user(userid, name, nick):
    try_commit(
        "INSERT INTO users (userid, username, usernick, charline, state, games, wins, "
        "streaks, maxstreak, points, maxpoints) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (userid, name, nick, charline_default, 0, 0, 0, 0, 0, 0, 0))


def check_user(userid):
    data = try_fetch("SELECT userid FROM users WHERE userid=%s", (userid,), ONE)
    return data


def get_word(_id):
    data = try_fetch("SELECT word FROM crux5 WHERE id=%s", (_id,), ONE)
    word = data[0]
    return word


def get_word_info(word):
    data = try_fetch("SELECT shared, entered, votepro, votecontra FROM crux5 WHERE word=%s", (word,), ONE)
    return data


def get_all_word_info():
    data = try_fetch(
        "SELECT word, shared, entered, votepro, votecontra FROM crux5 WHERE shared>0 OR votepro>0 OR votecontra>0 OR entered>0",
        (), ALL)
    return data


def set_word_info(word, shared, entered, votepro, votecontra):
    try_commit("UPDATE crux5 SET shared=%s, entered=%s, votepro=%s, votecontra=%s WHERE word=%s",
               (shared, entered, votepro, votecontra, word))


def set_word(userid, word, cruxid):
    try_commit("UPDATE users SET cruxword=%s, cruxid=%s WHERE userid=%s", (word, cruxid, userid))


def check_word(word):
    data = try_fetch("SELECT word, usages FROM dict5 WHERE word=%s", (word,), ONE)
    return data


def get_word_usages():
    data = try_fetch("SELECT word, usages FROM dict5 WHERE usages>0", (), ALL)
    return data


def up_word_usages(pair):
    word, usages = pair
    data = try_fetch("UPDATE dict5 set usages=%s WHERE word=%s", (usages + 1, word), ONE)
    return data


def get_crux(userid):
    data = try_fetch("SELECT cruxword, cruxid, charline, prevmess, state FROM users WHERE userid=%s",
                     (userid,), ONE)
    return data


def set_user(userid, chline, messid, state):
    try_commit("UPDATE users SET charline=%s, prevmess=%s, state=%s WHERE userid=%s", (chline, messid, state, userid))


def set_blank_user(userid):
    try_commit("UPDATE users SET cruxword=%s, cruxid=%s, charline=%s, prevmess=%s, state=%s, inputs=%s WHERE userid=%s",
               ('', 0, charline_default, 0, 1, '', userid))


def set_inputs(userid, inputs):
    try_commit("UPDATE users SET inputs=%s WHERE userid=%s", (inputs, userid))


def get_inputs(userid):
    data = try_fetch("SELECT inputs FROM users WHERE userid=%s", (userid,), ONE)
    return data[0]


def set_stats(userid, games, wins, streaks, maxstreak, points, maxpoints):
    try_commit("UPDATE users SET games=%s, wins=%s, streaks=%s, maxstreak=%s, points=%s, maxpoints=%s WHERE userid=%s",
               (games, wins, streaks, maxstreak, points, maxpoints, userid))


def get_stats(userid):
    data = try_fetch("SELECT games, wins, streaks, maxstreak, points, maxpoints FROM users WHERE userid=%s",
                     (userid,), ONE)
    return data


def add_game(userid, cruxid, crux):
    tstamp = datetime.now()
    try_commit("INSERT into games (userid, cruxid, crux, tstamp) VALUES (%s,%s,%s,%s) ", (userid, cruxid, crux, tstamp))


def set_moves(userid, crux, moves, words):
    logger.debug(f'{userid} SET MOVES {crux} {moves} {words}')
    try_commit("UPDATE games SET moves=%s, words=%s WHERE userid=%s AND crux=%s", (moves, words, userid, crux))


def get_moves(userid, crux):
    data = try_fetch("SELECT moves, words FROM games WHERE userid=%s AND crux=%s", (userid, crux), ONE)
    return data


def get_games(userid):
    data = try_fetch("SELECT cruxid FROM games WHERE userid=%s", (userid,), ALL)
    return data


def get_players():
    data = try_fetch("SELECT username, games, wins, streaks, maxstreak, points FROM users", (), ALL)
    return data


def get_comm_word(word):
    data = try_fetch("SELECT usages FROM comm5 WHERE word=%s", (word,), ONE)
    return data


def add_comm_word(word):
    try_commit("INSERT INTO comm5 (word, usages) VALUES (%s,%s)", (word, 1))


def upd_comm_word(word, usages):
    try_commit("UPDATE comm5 SET usages=%s where word=%s", (usages, word))


def start(userid, message):
    cruxid = 0
    is_shared = False
    if len(message.text) > 6:
        try:
            cruxid = int(message.text[7:])
            is_shared = True
            try_send_message(userid, f'Given number #{cruxid}')
        except Exception as err:
            logger.debug(f'PARSE START ERR {(userid, cruxid, message.text, err)}')

    result = touch_user(userid, message.from_user)
    if result:
        try_send_message(userid, 'Hello!')
        show_help(userid)
    word = choose_word(userid, cruxid)
    if word and is_shared:
        shared, entered, votepro, votecontra = get_word_info(word)
        shared += 1
        set_word_info(word, shared, entered, votepro, votecontra)


def touch_user(userid, from_user):
    uname = from_user.username if from_user.username else ''
    # locale = from_user.language_code if from_user.language_code else 'ru'
    fname = from_user.first_name if from_user.first_name else ''
    lname = from_user.last_name if from_user.last_name else ''
    flname = f'{fname} {lname}'.lstrip().rstrip()
    nickname = '@' + uname
    if check_user(userid):
        return 0

    create_user(userid, flname, nickname)
    return 1


def choose_word(userid, cruxid=0):
    _, currcruxid, _, _, _ = get_crux(userid)
    if currcruxid:
        try_send_message(userid, 'Please finish the current game\n'
                                 'You can send the word "giveup" to get the answer.')
        return

    knowncruxes = [i[0] for i in get_games(userid)]
    if cruxid in knowncruxes:
        try_send_message(userid, 'You already guessed that word')
        return

    if not cruxid:
        allowedcruxes = [i for i in range(1, 2315) if i not in knowncruxes]
        if len(allowedcruxes) == 2214:
            try_send_message(userid, "Wow, you played 100 words! This is as much as 4% of 2315 :)")
        if len(allowedcruxes) == 100:
            try_send_message(userid, "Less than 100 words left o_0")
        if len(allowedcruxes) == 10:
            try_send_message(userid, "Less than 10 words left...")
        if len(allowedcruxes) == 0:
            try_send_message(userid, "You have played all the words! Write to developer @timeclackx")
            return
        cruxid = choices(allowedcruxes)[0]

    try_send_message(userid, f"I guess a word #{cruxid}\nMove 1: Enter a five-letter word")
    set_blank_user(userid)
    word = get_word(cruxid)
    set_word(userid, word, cruxid)
    add_game(userid, cruxid, word)
    return word


def incoming(userid, userword):
    userword = userword.lower()
    if len(userword) < 5:
        num = 0
        try:
            num = int(userword)
        except Exception as err:
            logger.debug(f'PARSE INT ERR {userid} {userword} {err}')
        if 0 < num <= 2315:
            userword = choose_word(userid, num)
            if userword:
                shared, entered, votepro, votecontra = get_word_info(userword)
                entered += 1
                set_word_info(userword, shared, entered, votepro, votecontra)
            return
        elif num > 2315:
            try_send_message(userid, "2315 words available. The last 7 are specially chosen to be difficult.")
            return
        else:
            try_send_message(userid, "Not enough! Enter a 5 letter word.")
            return

    if userword == 'giveup':
        cruxword, cruxid, chline, prevmess, state = get_crux(userid)
        if cruxword:
            add_moves(userid, cruxword, userword, '🟧' * 5)
            go_loose(userid, cruxword, cruxid, prevmess)

        else:
            try_send_message(userid, "The game has not started. To start press /start")
        return

    if len(userword) > 5:
        try_send_message(userid, "Will not work! Enter a 5 letter word.")
        return

    result = check_word(userword)
    if not result:
        worddata = get_comm_word(userword)
        if worddata:
            try_send_message(userid, "I already wrote down this word, maybe I will add it to the dictionary :*")
            upd_comm_word(userword, worddata[0] + 1)
        else:
            logger.debug(f"{userid} ?? unknown userword :: {userword}")
            answers = ("Does such a word exist?", "It's definitely not a proper name, is it?",
                       "I don't know this word", "Sorry friend, I don't understand")
            try_send_message(userid, choices(answers)[0])
            add_comm_word(userword)
        return

    up_word_usages(result)
    cruxword, cruxid, chline, prevmess, state = get_crux(userid)

    if not cruxword:
        try_send_message(userid, "The game has not started. To start press /start")
        return

    if userword == cruxword or userword == 'ok':
        add_moves(userid, cruxword, userword, '🟩' * 5)
        go_win(userid, state, cruxword, cruxid, prevmess)
        return

    b, g, y = ('⬜', '🟩', '🟨️')
    answer = ''
    state += 1

    for i in range(0, 5):

        if userword[i] == cruxword[i]:
            answer += g
            chline = chline.replace(userword[i], userword[i].capitalize())
        else:
            if userword[i] in cruxword:
                answer += y
                chline = chline.replace(userword[i], userword[i].capitalize())
            else:
                answer += b
                chline = chline.replace(userword[i], '_')

    add_moves(userid, cruxword, userword, answer)
    try_send_message(userid, answer)

    if state > 6:
        go_loose(userid, cruxword, cruxid, prevmess)
        return

    try_delete_message(userid, prevmess)
    statetext = state if state < 6 else '6 (last one!)'
    messid = try_send_message(userid, f'Move {statetext}: ', reply_markup=get_kb(chline))
    set_user(userid, chline, messid, state)


def add_moves(userid, cruxword, word, move):
    data = get_moves(userid, cruxword)
    moves, words = data if data else ('', '')
    moves = moves + ' ' + move if moves else move
    words = words + ' ' + word if words else word
    set_moves(userid, cruxword, moves, words)


def go_inputs(userid, chosen):
    inputs = get_inputs(userid)
    if not inputs:
        inputs = ''
    _, _, charline, prevmess, state = get_crux(userid)
    if chosen == 'CLR':
        inputs = ''
    elif chosen == 'DEL':
        inputs = inputs[:len(inputs) - 1] if len(inputs) > 0 else ''
    else:
        inputs += chosen
    try_edit_message_text(f'Move {state}: {inputs.upper()}', userid, prevmess, reply_markup=get_kb(charline))

    if len(inputs) > 4:
        set_inputs(userid, '')
        try_send_message(userid, f'Move {state}: {inputs.capitalize()}')
        try_edit_message_text(f'Move {state}:', userid, prevmess, reply_markup=get_kb(charline))
        incoming(userid, inputs)
    else:
        set_inputs(userid, inputs)


def go_loose(userid, cruxword, cruxid, prevmess):
    try_send_message(userid, f'Correct word: {cruxword}')
    try_delete_message(userid, prevmess)

    moves, words = get_moves(userid, cruxword)
    text = f'@Wordiengbot #{cruxid} X/6 \n\n' + '\n'.join(moves.split())
    try_send_message(userid, text, reply_markup=get_vote_kb(cruxword))

    games, wins, streaks, maxstreak, points, maxpoints = get_stats(userid)
    games += 1
    avrgpoints = points * 10 // games / 10
    try_send_message(userid, f'You lost.\nYour points: {points}\nAverage: {avrgpoints}'
                             '\nStatistics /stats\n\nNew game /start')
    set_blank_user(userid)
    set_stats(userid, games, wins, 0, maxstreak, points, maxpoints)
    try_send_message(userid, f"Share a word with a friend: t.me/Wordiengbot?start={cruxid}")


def go_win(userid, state, cruxword, cruxid, prevmess):
    try_delete_message(userid, prevmess)
    moves, words = get_moves(userid, cruxword)

    text = f'@Wordiengbot #{cruxid} {state}/6 \n\n' + '\n'.join(moves.split())
    try_send_message(userid, text, reply_markup=get_vote_kb(cruxword))

    games, wins, streaks, maxstreak, points, maxpoints = get_stats(userid)
    bonus = streaks if streaks < 10 else 10
    winpoints = 70 - (10 * state) + bonus
    points += winpoints
    wins += 1
    games += 1
    streaks += 1
    if maxstreak < streaks:
        maxstreak = streaks
    if maxpoints < winpoints:
        maxpoints = winpoints
    avrgpoints = points * 10 // games / 10
    try_send_message(userid, f'You won!\n+ {winpoints} points\nYour points: {points}\nAverage: {avrgpoints}'
                             '\nStatistics /stats\n\nNew game /start')
    set_blank_user(userid)
    set_stats(userid, games, wins, streaks, maxstreak, points, maxpoints)
    try_send_message(userid, f"Share a word with a friend: t.me/Wordiengbot?start={cruxid}")


def show_stats(userid):
    games, wins, streaks, maxstreak, points, maxpoints = get_stats(userid)
    avrgpoints = points * 10 // games / 10 if games else 0
    wins_percents = wins * 1000 // games / 10
    result = (f'Games completed: {games}\nOf which wins: {wins} \nPercentage: {wins_percents}%\n\n'
              f'Streaks: {streaks} \nMax. in a row: {maxstreak}'
              f' \n\nPoints: {points}\nMax: {maxpoints}\nAverage: {avrgpoints}\n\n'
              f'Top 10 /top10')
    try_send_message(userid, result)


def show_help(userid):
    text = 'The rules are simple: I guess a five-letter word, and you try to guess it in 6 steps.\n' \
           'I have about 13,000 five-letter words in my dictionary, but I''ll only guess of the most popular ones.\n\n' \
           'So you send me the words, and I give you the answer in the form of colored tiles:\n' \
           '<i>gray</i> ⬜ if there is no such letter,\n' \
           '<i>yellow</i> 🟨️ if the letter in the word exists but is not in its place,\n' \
           'and <i>green</i> 🟩 if the letter in your word is in the same place as the letter in the hidden one. \n\n' \
           'For example,\nif you write the word "<i>raven</i>",\nand I answer you ⬜️🟩🟨️⬜️🟨️,\nit will mean ' \
           'that the letter "<b>a</b>" in the hidden word will be the second, ' \
           'the letters "<b>v</b>" and "<b>n</b>" meet somewhere, ' \
           'and the letters "<b>r</b>" and "<b>e</b>" are absent in the hidden word.\n\n' \
           'If you like the hidden word, you can send the number to your friend, ' \
           'so that he also breaks his head over it :) You can enter any number up to 2315 yourself.\n\nHave a nice game!'
    try_send_message(userid, text)


def show_words(userid):
    data = get_word_usages()
    result = {}
    for wordpair in data:
        word, counts = wordpair
        result[word] = counts

    sorted_result = sorted(result.items(), key=lambda x: x[1], reverse=True)
    size = len(result) if len(result) < 25 else 25

    text = 'Word frequency:\n\n'
    for idx, val in enumerate(sorted_result):
        if idx < size + 2:
            text += f'{idx + 1}. {val[0]} x {val[1]}\n'
    text += '\nWord rating /rates'
    try_send_message(userid, text)


def show_words_rate(userid):
    data = get_all_word_info()
    shared_dict = {}
    entered_dict = {}
    votepro_dict = {}
    votecontra_dict = {}
    for worddata in data:
        word, shared, entered, votepro, votecontra = worddata
        shared_dict[word] = shared
        entered_dict[word] = entered
        votepro_dict[word] = votepro
        votecontra_dict[word] = votecontra

    shared_top = sorted(shared_dict.items(), key=lambda x: x[1], reverse=True)
    entered_top = sorted(entered_dict.items(), key=lambda x: x[1], reverse=True)
    votepro_top = sorted(votepro_dict.items(), key=lambda x: x[1], reverse=True)
    votecontra_top = sorted(votecontra_dict.items(), key=lambda x: x[1], reverse=True)

    size = len(data) if len(data) < 7 else 7

    text = 'Shared:\n'
    for idx, val in enumerate(shared_top):
        if idx < size:
            text += f'{idx + 1}. {val[0]} : : {val[1]}\n'

    text += '\nEntered:\n'
    for idx, val in enumerate(entered_top):
        if idx < size:
            text += f'{idx + 1}. {val[0]} : : {val[1]}\n'

    text += '\nVote pro:\n'
    for idx, val in enumerate(votepro_top):
        if idx < size:
            text += f'{idx + 1}. {val[0]} : : {val[1]}\n'

    text += '\nContra:\n'
    for idx, val in enumerate(votecontra_top):
        if idx < size:
            text += f'{idx + 1}. {val[0]} : : {val[1]}\n'

    text += '\nWord frequency /words'
    text += '\nDevelopment @timeclackx'

    try_send_message(userid, text)


def show_top(userid):
    data = get_players()
    avrg_dict = {}
    points_dict = {}
    maxstreak_dict = {}
    for player in data:
        username, games, wins, streaks, maxstreak, points = player
        avrgpoints = points * 10 // games / 10 if games else 0
        avrg_dict[username] = avrgpoints
        points_dict[username] = points
        maxstreak_dict[username] = maxstreak

    avrg_winners = sorted(avrg_dict.items(), key=lambda x: x[1], reverse=True)
    points_winners = sorted(points_dict.items(), key=lambda x: x[1], reverse=True)
    maxstreak_winners = sorted(maxstreak_dict.items(), key=lambda x: x[1], reverse=True)

    size = len(data) if len(data) < 10 else 10

    text = 'Average per game:\n'
    for idx, val in enumerate(avrg_winners):
        if idx < size + 2:
            text += f'{idx + 1}. {val[0]} : : {val[1]}\n'

    text += '\nBy points:\n'
    for idx, val in enumerate(points_winners):
        if idx < size + 2:
            text += f'{idx + 1}. {val[0]} : : {val[1]}\n'

    text += '\nMax streak:\n'
    for idx, val in enumerate(maxstreak_winners):
        if idx < size + 2:
            text += f'{idx + 1}. {val[0]} : : {val[1]}\n'

    text += '\nPersonal stats /stats'
    text += '\nDevelopment @timeclackx'

    try_send_message(userid, text)


def go_vote(userid, word, vote, text, message_id):
    shared, entered, votepro, votecontra = get_word_info(word)
    if vote == 'pro':
        votepro += 1
    else:
        votecontra += 1
    set_word_info(word, shared, entered, votepro, votecontra)
    try_edit_message_text(text, userid, message_id)


@bot.message_handler(commands=["start"])
def docall(message):
    start_time = time.time()
    userid = message.from_user.id
    uname = message.from_user.username
    fname = message.from_user.first_name
    logger.debug(f"{userid} {fname} @{uname} select START")
    start(userid, message)
    logger.debug(f"{userid} {fname} @{uname} select START :: {time.time() - start_time}")


@bot.message_handler(commands=["stats"])
def docall(message):
    start_time = time.time()
    userid = message.from_user.id
    uname = message.from_user.username
    fname = message.from_user.first_name
    logger.debug(f"{userid} {fname} @{uname} select STATS")
    show_stats(userid)
    logger.debug(f"{userid} {fname} @{uname} select STATS :: {time.time() - start_time}")


@bot.message_handler(commands=["help"])
def docall(message):
    start_time = time.time()
    userid = message.from_user.id
    uname = message.from_user.username
    fname = message.from_user.first_name
    logger.debug(f"{userid} {fname} @{uname} select HELP")
    show_help(userid)
    logger.debug(f"{userid} {fname} @{uname} select HELP :: {time.time() - start_time}")


@bot.message_handler(commands=["top10"])
def docall(message):
    start_time = time.time()
    userid = message.from_user.id
    uname = message.from_user.username
    fname = message.from_user.first_name
    logger.debug(f"{userid} {fname} @{uname} select WORDS")
    show_top(userid)
    logger.debug(f"{userid} {fname} @{uname} select WORDS :: {time.time() - start_time}")


@bot.message_handler(commands=["words"])
def docall(message):
    start_time = time.time()
    userid = message.from_user.id
    uname = message.from_user.username
    fname = message.from_user.first_name
    logger.debug(f"{userid} {fname} @{uname} select TOP10")
    show_words(userid)
    logger.debug(f"{userid} {fname} @{uname} select TOP10 :: {time.time() - start_time}")


@bot.message_handler(commands=["rates"])
def docall(message):
    start_time = time.time()
    userid = message.from_user.id
    uname = message.from_user.username
    fname = message.from_user.first_name
    logger.debug(f"{userid} {fname} @{uname} select TOP10")
    show_words_rate(userid)
    logger.debug(f"{userid} {fname} @{uname} select TOP10 :: {time.time() - start_time}")


@bot.message_handler(content_types=['text'])
def docall(message):
    start_time = time.time()
    userid = message.from_user.id
    uname = message.from_user.username
    fname = message.from_user.first_name
    logger.debug(f"{userid} {fname} @{uname} input {message.text}")
    incoming(message.chat.id, message.text)
    logger.debug(f"{userid} {fname} @{uname} input {message.text} :: {time.time() - start_time}")


@bot.callback_query_handler(func=lambda call: True)
def docall(query):
    start_time = time.time()
    userid = query.message.chat.id
    messid = query.message.message_id
    uname = query.message.chat.username
    fname = query.message.chat.first_name
    button = query.data
    logger.debug(f"{userid} {fname} @{uname} button {button}")

    strips = button.split('_')
    if len(strips) > 1:
        button = strips[0]
        chosen = strips[1]

        if button == "press":
            go_inputs(userid, chosen)
            try_answer_callback_query(query.id)

        if button == "vote":
            go_vote(userid, chosen, strips[2], query.message.text, messid)
            try_answer_callback_query(query.id, 'Vote accepted, thanks')

    logger.debug(f"{userid} {fname} @{uname} button {button} :: {time.time() - start_time}")


def try_edit_message_text(text, userid, messid, reply_markup=None, parse_mode="html"):
    if messid:
        try:
            bot.edit_message_text(text, userid, messid, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as err:
            logger.debug(f'EDIT MESS ERR: {err}')
            if 'are exactly the same' not in str(err):
                try_send_message(userid, text, reply_markup=reply_markup, parse_mode="html")
    else:
        try_send_message(userid, text, reply_markup=reply_markup, parse_mode="html")


def try_send_message(userid, text, reply_markup=None, parse_mode="html"):
    try:
        messid = bot.send_message(userid, text, reply_markup=reply_markup,
                                  parse_mode=parse_mode, disable_notification=True).message_id
        return messid
    except ConnectionResetError as err:
        logger.debug(f'SEND MESS ERR: {err}')
        try_send_message(userid, text, reply_markup=None, parse_mode="html")
    except Exception as err:
        logger.debug(f'SEND MESS ERR: {err}')
        return 0


def try_delete_message(userid, messid):
    if messid:
        try:
            bot.delete_message(userid, messid)
        except Exception as err:
            logger.debug(f'{messid} DEL MESS ERR: {err}')


def try_answer_callback_query(callback_query_id="", text=""):
    try:
        bot.answer_callback_query(callback_query_id, text=text)
    except Exception as err:
        logger.debug(f'ACbQ Err: {err}')


class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                'content-type' in cherrypy.request.headers and \
                cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''


if __name__ == "__main__":
    cherrypy.config.update(cherrypy_conf)
    cherrypy.quickstart(WebhookServer(), '/', {'/': {}})
