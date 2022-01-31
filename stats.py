from utils import try_send_message
from wordb import get_stats, get_players, get_word_usages, get_all_word_info, get_comms


async def show_stats(userid):
    games, wins, streaks, maxstreak, points, maxpoints = await get_stats(userid)
    avrgpoints = points * 10 // games / 10 if games else 0
    wins_percents = wins * 1000 // games / 10 if games else 0.0
    result = (f'Завершено игр: {games}\nИз них побед: {wins} \nВ процентах: {wins_percents}%\n\n'
              f'Подряд (streaks): {streaks} \nМакс. подряд: {maxstreak}'
              f' \n\nОчки: {points}\nМакс.: {maxpoints}\nСреднее: {avrgpoints}\n\n'
              f'TOP 10 /top10')
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


async def show_top(userid):
    data = await get_players()
    avrg_dict = {}
    points_dict = {}
    maxstreak_dict = {}
    for player in data:
        username, games, wins, streaks, maxstreak, points = player
        if len(username) > 21:
            username = username[:20] + '...'
        avrgpoints = points * 10 // games / 10 if games else 0
        avrg_dict[username] = avrgpoints
        points_dict[username] = points
        maxstreak_dict[username] = maxstreak

    avrg_winners = sorted(avrg_dict.items(), key=lambda x: x[1], reverse=True)
    points_winners = sorted(points_dict.items(), key=lambda x: x[1], reverse=True)
    maxstreak_winners = sorted(maxstreak_dict.items(), key=lambda x: x[1], reverse=True)

    size = len(data) if len(data) < 15 else 15
    text = 'Среднее за игру:\n'
    for idx, val in zip(range(size), avrg_winners):
        text += f'{idx + 1}. {val[0]} : : {val[1]}\n'
    text += '\nПо очкам:\n'
    for idx, val in zip(range(size - 5), points_winners):
        text += f'{idx + 1}. {val[0]} : : {val[1]}\n'
    text += '\nМакс. подряд:\n'
    for idx, val in zip(range(size - 5), maxstreak_winners):
        text += f'{idx + 1}. {val[0]} : : {val[1]}\n'
    text += '\nЛичная статистка /stats'
    text += '\nРазработка @timeclackx'
    await try_send_message(userid, text)
