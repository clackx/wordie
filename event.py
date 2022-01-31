from random import choices

from utils import try_send_message, try_edit_message_text, try_delete_message, \
    get_vote_kb, get_kb, dope_send_message, logger
from wordb import set_user, check_user, create_user, set_blank_user, \
    get_crux, check_word, get_word, set_word, get_word_info, set_word_info, up_word_usages, \
    get_games, add_game, get_moves, set_moves, get_stats, set_stats, set_inputs, get_inputs, \
    get_comm_word, add_comm_word, upd_comm_word


async def incoming(userid, userword):
    userword = userword.lower().replace('ё', 'е')
    if len(userword) < 5:
        num = 0
        try:
            num = int(userword)
        except Exception as err:
            logger.debug(err)
        if 0 < num < 1262:
            userword = await choose_word(userid, num)
            if userword:
                shared, entered, votepro, votecontra = await get_word_info(userword)
                entered += 1
                await set_word_info(userword, shared, entered, votepro, votecontra)
            return
        elif num > 1234:
            await try_send_message(userid, "Доступно 1234 слова. 7 последних специально подобраны сложными.")
            return
        else:
            await try_send_message(userid, "Маловато! Введите слово из 5 букв.")
            return

    if userword == 'сдаюсь':
        cruxword, cruxid, _, prevmess, _ = await get_crux(userid)
        if cruxword:
            moves = await add_moves(userid, cruxword, userword, '🟧' * 5)
            await go_loose(userid, cruxword, cruxid, prevmess, moves)
        else:
            await try_send_message(userid, "Игра не начата. Для начала нажмите /start")
        return

    if len(userword) > 5:
        await try_send_message(userid, "Так не пойдёт! Введите слово из 5 букв.")
        return

    dictword = await check_word(userword)
    if not dictword:
        commword = await get_comm_word(userword)
        if commword:
            logger.debug(f"{userid} ?!?! userword {userword} :: {commword[0]} repeats")
            await try_send_message(userid, "Я уже записал это слово, возможно, добавлю его в словарь :*")
            await upd_comm_word(userword, commword[0] + 1)
        else:
            logger.debug(f"{userid} ?!?! unknown userword :: {userword}")
            answers = ("Такое слово существует?", "Это точно не имя собственное?",
                       "Не знаю этого слова", "Извини, друг, не понимаю")
            await try_send_message(userid, choices(answers)[0])
            await add_comm_word(userword)
        return
    else:
        word, usages = dictword
        usages += 1
        logger.debug(f"{'.' * 26} {word} {'|' * usages} repeats {usages} times")
        await up_word_usages(word, usages)

    cruxword, cruxid, chline, prevmess, state = await get_crux(userid)

    if not cruxword:
        await try_send_message(userid, "Игра не начата. Для начала нажмите /start")
        return

    if userword == cruxword:
        moves = await add_moves(userid, cruxword, userword, '🟩' * 5)
        await go_win(userid, state, cruxword, cruxid, prevmess, moves)
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

    moves = await add_moves(userid, cruxword, userword, answer)
    await try_send_message(userid, answer)
    if state > 6:
        await go_loose(userid, cruxword, cruxid, prevmess, moves)
        return
    await try_delete_message(userid, prevmess)
    statetext = state if state < 6 else '6 (последний!)'
    messid = await try_send_message(userid, f'Ход {statetext}: ', markup=get_kb(chline))
    await set_user(userid, chline, messid, state)


async def start(userid, message):
    cruxid = 0
    is_shared = False
    if len(message.text) > 6:
        try:
            cruxid = int(message.text[7:])
            logger.debug(f'{userid} start with shared {cruxid}')
            is_shared = True
            await try_send_message(userid, f'Вам передали номер {cruxid}!')
        except Exception as err:
            logger.debug(f"{userid} PARSE ERROR {cruxid} {message.text} {err}")

    result = await touch_user(userid, message.from_user)
    if result:
        await try_send_message(userid, 'Привет!')
        await show_help(userid)
    word = await choose_word(userid, cruxid)
    if word and is_shared:
        logger.debug(f'start with word {word}')
        shared, entered, votepro, votecontra = await get_word_info(word)
        shared += 1
        await set_word_info(word, shared, entered, votepro, votecontra)


async def touch_user(userid, from_user):
    is_user_exist = await check_user(userid)
    if is_user_exist:
        return 0
    uname = from_user.username if from_user.username else ''
    # locale = from_user.language_code if from_user.language_code else 'ru'
    fname = from_user.first_name if from_user.first_name else ''
    lname = from_user.last_name if from_user.last_name else ''
    flname = f'{fname} {lname}'.lstrip().rstrip()[:42]
    nickname = '@' + uname
    await create_user(userid, flname, nickname)
    return 1


async def choose_word(userid, cruxid=0):
    cruxword, _, _, _, _ = await get_crux(userid)
    if cruxword:
        await try_send_message(userid, 'Пожалуйста, завершите текущую игру.\n'
                                       'Можете отправить слово "сдаюсь", чтобы узнать ответ.')
        return
    games_ids = await get_games(userid)
    await dope_send_message(f": : {userid} played {len(games_ids)} games, enter {cruxid}")
    knowncruxes = [i[0] for i in games_ids]
    if cruxid in knowncruxes:
        await try_send_message(userid, 'Вы уже отгадывали это слово')
        return

    if not cruxid:
        allowedcruxes = [i for i in range(1, 1234) if i not in knowncruxes]
        if len(allowedcruxes) == 1133:
            await try_send_message(userid, "Ого, вы сыграли 100 слов! Это целых 8% от 1234 :)")
        if len(allowedcruxes) == 926:
            await try_send_message(userid, "Вы сыграли четвертую часть всех слов!")
        if len(allowedcruxes) == 823:
            await try_send_message(userid, "Вы сыграли треть всех слов!!")
        if len(allowedcruxes) == 617:
            await try_send_message(userid, "Вы сыграли половину всех слов!!!")
        if len(allowedcruxes) == 100:
            await try_send_message(userid, "Осталось меньше 100 слов o_0")
        if len(allowedcruxes) == 10:
            await try_send_message(userid, "Осталось меньше 10 слов...")
        if len(allowedcruxes) == 0:
            await try_send_message(userid, "Вы сыграли все слова! Напишите разработчику @timeclackx")
            return
        cruxid = choices(allowedcruxes)[0]

    await try_send_message(userid, f"Я загадал слово №{cruxid}\nХод 1:  Введите слово из пяти букв")
    await set_blank_user(userid)
    word = await get_word(cruxid)
    await set_word(userid, word, cruxid)
    await add_game(userid, cruxid, word)
    return word


async def add_moves(userid, cruxword, word, move):
    data = await get_moves(userid, cruxword)
    moves, words = data if data else ('', '')
    moves = moves + ' ' + move if moves else move
    words = words + ' ' + word if words else word
    await set_moves(userid, cruxword, moves, words)
    return moves


async def go_inputs(userid, chosen):
    inputs = await get_inputs(userid)
    if not inputs:
        inputs = ''
    _, _, charline, prevmess, state = await get_crux(userid)
    inputs += chosen
    letters = inputs.upper() if len(inputs) < 5 else ''
    await try_edit_message_text(f'Ход {state}: {letters}', userid, prevmess, markup=get_kb(charline))

    if len(inputs) > 4:
        await set_inputs(userid, '')
        await try_send_message(userid, f'Ход {state}: {inputs.capitalize()}')
        await incoming(userid, inputs)
    else:
        await set_inputs(userid, inputs)


async def go_loose(userid, cruxword, cruxid, prevmess, moves):
    await try_send_message(userid, f'Верное слово: {cruxword}')
    await try_delete_message(userid, prevmess)
    text = f'@WordieRobot №{cruxid} X/6 \n\n' + '\n'.join(moves.split())
    await try_send_message(userid, text, markup=get_vote_kb(cruxword))
    games, wins, streaks, maxstreak, points, maxpoints = await get_stats(userid)
    games += 1
    avrgpoints = points * 10 // games / 10
    await try_send_message(userid, f'Вы проиграли.\nВаши очки: {points}\nСреднее: {avrgpoints}'
                                   '\nСтатистика /stats\n\nНовая игра /start')
    await set_blank_user(userid)
    await set_stats(userid, games, wins, 0, maxstreak, points, maxpoints)
    await try_send_message(userid, f"Поделитесь словом с другом: t.me/WordieRobot?start={cruxid}")


async def go_win(userid, state, cruxword, cruxid, prevmess, moves):
    await try_delete_message(userid, prevmess)
    text = f'@WordieRobot №{cruxid} {state}/6 \n\n' + '\n'.join(moves.split())
    await try_send_message(userid, text, markup=get_vote_kb(cruxword))
    games, wins, streaks, maxstreak, points, maxpoints = await get_stats(userid)
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
    await try_send_message(userid, f'Победа!\n+ {winpoints} очков\nВаши очки: {points}\nСредний балл: {avrgpoints}'
                                   '\nСтатистика /stats\n\nНовая игра /start')
    await set_blank_user(userid)
    await set_stats(userid, games, wins, streaks, maxstreak, points, maxpoints)
    await try_send_message(userid, f"Поделитесь словом с другом: t.me/WordieRobot?start={cruxid}")


async def go_vote(userid, word, vote, text, message_id):
    shared, entered, votepro, votecontra = await get_word_info(word)
    if vote == 'pro':
        votepro += 1
    else:
        votecontra += 1
    await set_word_info(word, shared, entered, votepro, votecontra)
    await try_edit_message_text(text, userid, message_id)


async def show_help(userid):
    text = 'Правила простые: я загадываю слово из пяти букв, а вы стараетесь отгадать его за 6 шагов.\n' \
           'В моём словаре около 4х тысяч пятибуквенных слов, но загадывать я буду только самые известные.\n\n' \
           'Итак, вы отправляете мне слова, а я даю вам ответ в виде цветных плиток:\n' \
           '<i>серая</i> ⬜, если такой буквы нет,\n' \
           '<i>жёлтая</i> 🟨️, если буква в слове существует, но стоит не на своём месте,\n' \
           'и <i>зелёная</i> 🟩, если буква в вашем слове стоит на том же месте, что и буква в загаданном. \n\n' \
           'Например, если вы напишете слово "<i>комар</i>", а я вам отвечу ⬜️🟩🟨️⬜️🟨️, то это будет означать, ' \
           'что буква "<b>о</b>" в загаданном слове будет второй, буквы "<b>м</b>" и "<b>р</b>" где-то встречаются, ' \
           'а буквы "<b>к</b>" и "<b>а</b>" в загаданном слове отсутствуют.\n\n' \
           'Если вам понравилось загаданное слово, ва можете отправить номер своему другу, ' \
           'чтобы он тоже поломал над ним голову :) Вы и сами можете ввести любой номер до 1234го.\n\n' \
           'Если возникнут пожелания или неполадки в работе, не стесняйтесь, пишите @timeclackx\n\nПриятной игры!'
    await try_send_message(userid, text)
