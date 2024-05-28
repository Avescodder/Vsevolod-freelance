
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from telegram import ReplyKeyboardMarkup
import aiosqlite
import sqlite3

# Подключение к базе данных (или создание, если она не существует)
conn = sqlite3.connect('db.sqlite3')

# Создание курсора
cursor = conn.cursor()

# Создание таблицы clients
cursor.execute('''
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    status INTEGER NOT NULL,
    day INTEGER
)
''')

# Сохранение изменений
conn.commit()

# Закрытие соединения с базой данных
conn.close()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


CHOOSE_OPTION = range(1,2)

questions = {
    1: {"question": "What is urbanization?", "answer": [
        "A) The movement of people from rural areas to cities", "B) The development of rural areas", "C) The construction of highways", "D) The preservation of natural habitats"],
        "correct_answer": "A) The movement of people from rural areas to cities"},
    2: {"question": "Which of the following is a common environmental impact of urbanization?", "answer": [
        "A) Decrease in air pollution", "B) Increase in green spaces", "C) Loss of natural habitats", "D) Increase in biodiversity"],
        "correct_answer": "C) Loss of natural habitats"},
    3: {"question": "How does urbanization contribute to water pollution?", "answer": [
        "A) By increasing the number of rivers", "B) Through industrial discharge and sewage", "C) By cleaning up contaminated water sources", "D) By reducing the amount of waste produced"],
        "correct_answer": "B) Through industrial discharge and sewage"},
    4: {"question": "What is one way urbanization affects the local climate?", "answer": [
        "A) It makes the area cooler", "B) It has no impact on the local climate", "C) It can create urban heat islands", "D) It decreases precipitation levels"],
        "correct_answer": "C) It can create urban heat islands"},
    5: {"question": "How does urbanization impact wildlife?", "answer": [
        "A) It increases natural habitats", "B) It provides more food for wildlife", "C) It leads to habitat fragmentation and loss", "D) It has no effect on wildlife"],
        "correct_answer": "C) It leads to habitat fragmentation and loss"},
    6: {"question": "Which of the following is a sustainable practice to reduce the environmental impact of urbanization?", "answer": [
        "A) Deforestation", "B) Increasing the number of cars on the road", "C) Implementing green building practices", "D) Expanding urban sprawl"],
        "correct_answer": "C) Implementing green building practices"},
    7: {"question": "What is an urban heat island?", "answer": [
        "A) An area in a city that is significantly cooler than its surroundings", "B) An area in a city that is significantly warmer than its surroundings", "C) A natural park in the middle of a city", "D) A rural area that remains undeveloped"],
        "correct_answer": "B) An area in a city that is significantly warmer than its surroundings"}
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    status = 1
    async with aiosqlite.connect("db.sqlite3") as db:
        await db.execute("DELETE FROM clients")
        await db.commit()
    async with aiosqlite.connect("db.sqlite3") as db:
        await db.execute("INSERT INTO clients (id, status) VALUES (?, ?)", (user_id, status))
        await db.commit()
    replay_keyboard = [["Let's get started👆"]]
    async with aiosqlite.connect("db.sqlite3") as db:
        await db.execute("UPDATE clients SET day =? WHERE id =?", (1, user_id))
        await db.commit()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi guys, this is our quiz to learn what we've told you, hope you've been listening🧐",
        reply_markup=ReplyKeyboardMarkup(
            replay_keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
            
        ),
    )
    return CHOOSE_OPTION





async def choose_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with aiosqlite.connect("db.sqlite3") as db:
        cursor = await db.execute("SELECT status FROM clients WHERE id = ?", (user_id,))
        status_row = await cursor.fetchone()
        if status_row:
            user_status = status_row[0]
            print(f"это статус{user_status}")
            if user_status == 7:
                cursor = await db.execute("SELECT day FROM clients WHERE id =?", (user_id, ))
                day = await cursor.fetchone()
                day = day[0]
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"You answered {day} out of 7 questions correctly, thank you for taking our quiz🤙",
                )
                return ConversationHandler.END
            else:
                if update.effective_message.text == "Let's get started👆":
                    return await send_question(update, context, user_status)
                elif update.effective_message.text in questions[user_status]["correct_answer"]:
                    user_status += 1
                    await db.execute("UPDATE clients SET status =? WHERE id =?", (user_status, user_id))
                    await db.commit()
                    cursor = await db.execute("SELECT day FROM clients WHERE id =?", (user_id,))
                    day_row = await cursor.fetchone()
                    day = day_row[0] 
                    print(f"это день{day_row}")
                    day += 1
                    await db.execute("UPDATE clients SET day =? WHERE id =?", (day, user_id))
                    await db.commit()
                    return await send_question(update, context, user_status)
                elif update.effective_message.text not in questions[user_status]["correct_answer"]:
                    user_status += 1
                    await db.execute("UPDATE clients SET status =? WHERE id =?", (user_status, user_id))
                    await db.commit()
                    return await send_question(update, context, user_status)
        else:
            print("Error")

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_status):
    reeply_keyboard = [list(questions[user_status]["answer"])]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=questions[user_status]["question"],  # Убедитесь, что вы также отправляете текст вопроса
        reply_markup=ReplyKeyboardMarkup(
            reeply_keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return CHOOSE_OPTION
def main():
    application = (
        ApplicationBuilder().token("7152149587:AAEC5xvOqZe3oxxep44UHaiL4QQtXhmbmlU").build()
    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_OPTION:[
                MessageHandler(filters.TEXT, choose_option)
            ]
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
