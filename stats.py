from datetime import datetime, timedelta

from utils import try_send_message
from wordb import get_stats, get_players, get_word_usages, get_all_word_info, get_comms, get_games_from


async def show_stats(userid):
    games, wins, streaks, maxstreak, points, maxpoints = await get_stats(userid)
    avrgpoints = points * 10 // games / 10 if games else 0
    wins_percents = wins * 1000 // games / 10 if games else 0.0
    result = (f'Завершено игр: {games}\nИз них побед: {wins} \nВ процентах: {wins_percents}%\n\n'
              f'Подряд (streaks): {streaks} \nМакс. подряд: {maxstreak}'
              f' \n\nОчки: {points}\nМакс.: {maxpoints}\nСреднее: {avrgpoints}\n\n'
              f'Топ недели /top7')
    await try_send_message(userid, result)


async def show_words(userid):
    data = await get_word_usages()
    result = {}
    for wordpair in data:
        word, counts = wordpair
        result[word] = counts

    sorted_result = sorted(result.items(), key=lambda x: x[1], reverse=True)
    size = len(result) if len(result) < 25 else 25

    text = 'Частота слов:\n\n'
    for idx, val in enumerate(sorted_result):
        if idx < size + 2:
            text += f'{idx + 1}. {val[0]} x {val[1]}\n'
    text += '\nРейтинг слов /rates'
    await try_send_message(userid, text)


async def show_comms(userid):
    data = await get_comms()
    result = {}
    for wordpair in data:
        word, counts = wordpair
        result[word] = counts

    sorted_result = sorted(result.items(), key=lambda x: x[1], reverse=True)
    size = len(result) if len(result) < 25 else 25

    text = 'Частота слов:\n\n'
    for idx, val in enumerate(sorted_result):
        if idx < size + 2:
            text += f'{idx + 1}. {val[0]} x {val[1]}\n'
    text += '\nРейтинг слов /rates'
    await try_send_message(userid, text)


async def show_games(userid):
    today = datetime.now().strftime("%Y-%m-%d")
    dt = datetime.strptime(today, "%Y-%m-%d")
    week = (dt - timedelta(days=dt.weekday())).strftime("%Y-%m-%d")
    month = (dt - timedelta(days=30)).strftime("%Y-%m-%d")

    text = 'Игр за сегодня:\n'
    data = await get_games_from(today)
    size = len(data) if len(data) < 10 else 10
    total = 0
    for index, (username, count) in enumerate(data):
        if index < size:
            text += f"{index + 1}. {username} : : {count}\n"
        total += count
    text += f"Всего: {total}\n\n"

    text += 'C начала недели:\n'
    data = await get_games_from(week)
    size = len(data) if len(data) < 10 else 10
    total = 0
    for index, (username, count) in enumerate(data):
        if index < size:
            text += f"{index + 1}. {username} : : {count}\n"
        total += count
    text += f"Всего: {total}\n\n"

    text += 'За 30 дней:\n'
    data = await get_games_from(month)
    size = len(data) if len(data) < 10 else 10
    total = 0
    for index, (username, count) in enumerate(data):
        if index < size:
            text += f"{index + 1}. {username} : : {count}\n"
        total += count
    text += f"Всего: {total}\n\n"

    text += 'Рейтинг слов /rates    '
    await try_send_message(userid, text)


async def show_words_rate(userid):
    data = await get_all_word_info()
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
    text = 'Пошарено:\n'
    for idx, val in zip(range(size), shared_top):
        text += f'{idx + 1}. {val[0]} : : {val[1]}\n'
    text += '\nВведено:\n'
    for idx, val in zip(range(size), entered_top):
        text += f'{idx + 1}. {val[0]} : : {val[1]}\n'
    text += '\nГолоса за:\n'
    for idx, val in zip(range(size), votepro_top):
        text += f'{idx + 1}. {val[0]} : : {val[1]}\n'
    text += '\nПротив:\n'
    for idx, val in zip(range(size), votecontra_top):
        text += f'{idx + 1}. {val[0]} : : {val[1]}\n'
    text += '\nЧастота слов /words'
    text += '\nРазработка @timeclackx'
    await try_send_message(userid, text)


async def show_top(userid, is_weektop):
    today = datetime.now().strftime("%Y-%m-%d")
    dt = datetime.strptime(today, "%Y-%m-%d")
    week = (dt - timedelta(days=dt.weekday())).strftime("%Y-%m-%d")

    data = await get_players(week) if is_weektop else await(get_players('2022-01-01'))
    avrg_dict = {}
    points_dict = {}
    maxstreak_dict = {}
    for player in data:
        playerid, username, games, wins, streaks, maxstreak, points = player
        if len(username) > 21:
            username = username[:20] + '...'
        avrgpoints = points * 10 // games / 10 if games else 0
        avrg_dict[playerid] = (avrgpoints, username)
        points_dict[playerid] = (points, username)
        maxstreak_dict[playerid] = (maxstreak, username)

    text = 'Топ активных:\n\n' if is_weektop else 'Лучшие за всё время:\n\n'
    avrg_winners = sorted(avrg_dict.items(), key=lambda x: x[1], reverse=True)
    size = len(data) if len(data) < 15 else 15
    text += 'Среднее за игру:\n'
    for idx, val in zip(range(size), avrg_winners):
        text += f'{idx + 1}. {val[1][1]} : : {val[1][0]}\n'

    if is_weektop:
        text += '\nТоп за всё время /top10'
    else:
        points_winners = sorted(points_dict.items(), key=lambda x: x[1], reverse=True)
        maxstreak_winners = sorted(maxstreak_dict.items(), key=lambda x: x[1], reverse=True)
        text += '\nПо очкам:\n'
        for idx, val in zip(range(size - 5), points_winners):
            text += f'{idx + 1}. {val[1][1]} : : {val[1][0]}\n'
        text += '\nМакс. подряд:\n'
        for idx, val in zip(range(size - 5), maxstreak_winners):
            text += f'{idx + 1}. {val[1][1]} : : {val[1][0]}\n'
        text += '\nЛичная статистка /stats'
        text += '\nРазработка @timeclackx'

    await try_send_message(userid, text)
