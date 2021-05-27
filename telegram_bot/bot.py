import logging

import requests

from aiogram import Bot, Dispatcher, executor, types
from sqliter import SQLighter
from multiprocessing import Process
import config
import asyncio
from task import Stream

logging.basicConfig(level=logging.INFO)


bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot)
db = SQLighter()


@dp.message_handler(commands=["subscribe"])
async def subscribe(message: types.Message):
    if db.check_user(message.from_user.id):
        await message.answer("You already subscribed")
    else:
        db.add_user(message.from_user.id)
        await message.answer("You subscribed")


@dp.message_handler(commands=["unsubscribe"])
async def unsubscribe(message: types.Message):
    if db.check_user(message.from_user.id):
        db.delete_user(message.from_user.id)
        await message.answer("You unsubscribed")
    else:
        await message.answer("You have not been subscribed")


@dp.message_handler(commands=["accounts"])
async def get_acc(message: types.Message):
    if db.check_user(message.from_user.id):
        users = db.get_twiiter_acc(message.from_user.id)
        users = "\n".join(users)
        if users.strip() == "":
            await message.answer("You have not users")
        else:
            await message.answer(users)
    else:
        await message.answer("You unsubscribed")


async def send_to_telegram_bot(username,twitter_acc, text, date, link_to_tweet):
    users_ids = db.find_users_with_this_acc(username)
    text = (
        twitter_acc
        + " on Twitter\n"
        + "Text: \n"
        + text
        + "\n"
        + "Date: \n"
        + date
        + "\n"
        + "Link to tweet: \n"
        + link_to_tweet
    )
    for user_id in users_ids:
        chats = db.find_user_chats(user_id)
        for chat_id in chats:
            await bot.send_message(chat_id, text, parse_mode="html")


@dp.message_handler()
async def add_acc_to_acc_list(message: types.Message):
    stream = Stream(config.BEARER_TOKEN)
    text = "Error"
    if message.text.startswith("/add_twitter_acc_"):
        username = message.text[17:].strip()
        if stream.check_user_exists(username):
            if not db.user_acc_exists(message.from_user.id, username):
                db.add_usertwitteracc(message.from_user.id, username)
                text = "User Added " + username
                stream.add_rule(username)
            else:
                text = "User exists in your list"
        else:
            text = "No  such user(%s) in Twitter" % (username)

        await message.answer(text)
    elif message.text.startswith("/add_channel_"):
        chat_name = message.text[13:]
        chat_id_link = (
            "https://api.telegram.org/bot%s/sendMessage?chat_id=@%s&text=Test"
            % (config.API_TOKEN, chat_name)
        )
        r = requests.get(chat_id_link)
        data = r.json()

        try:
            chat_id = data["result"]["chat"]["id"]
            if not db.check_chat_id_exists_in_user_list(message.from_user.id, chat_id):
                db.add_chat_id_to_user(message.from_user.id, chat_id)
                text = "Chat id added"
            else:
                text = "Chat id also in list"
            await message.answer(text)
        except:
            await message.answer("This chat name is invalid" + chat_name)
    elif message.text.startswith("/del_acc_"):
        acc = message.text[9:]
        if db.user_acc_exists(message.from_user.id, acc):
            db.delete_usertwitter_acc(message.from_user.id, acc)
            rules = stream.get_rules()
            stream.delete_all_rules(rules)
            stream.set_rules()

    else:
        await message.answer("I do not understand your command")


def scheduled():
    from task import main

    main()


if __name__ == "__main__":
    p = Process(target=scheduled)
    p.start()
    executor.start_polling(dp, skip_updates=True)
