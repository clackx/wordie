
# Wordie

Telegram bot for playing Wordle in Russian

Based on aiogram and mysql

(Except english wordieng.py based on telebot)


# Ворди

Телеграм-бот для игры Wordle на русском

Боты работают на адресах:

Основной [@WordieRobot](https://t.me/WordieRobot)

Ворди4-7 [@Wordiegamebot](https://t.me/Wordiegamebot)

English [@Wordiengbot](https://t.me/Wordiengbot)


## Setup

Install dependencies

```bash
pip install -r requirements.txt
```

Create and modify confy.py

```bash
cp confy.py.sample confy.py
```

Create database and grant privileges

Then import data e.g.

```bash
mariadb-import wordie dumps/wordie.sql
```


## Run

Wordie with tg-webhook

```bash
python waiog.py
```

Wordie on long polling

```bash
python waiog.py --polling
```

Wordie english (uses wordieng db)

```bash
python wordieng.py
```

To run Wordie7 (4-7 letters, wordie7 db) first do the patch

```bash
patch -p1 < wordie7.patch
```

then run waiog.py or waiog.py --polling

### Enjoy!
