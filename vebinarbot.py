import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext
)
from telegram import ReplyKeyboardMarkup
import mysql.connector
import datetime
import pytz

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

config = {
    
}
try:
    connection = mysql.connector.connect(**config)
    print("Подключение успешно установлено!")


except mysql.connector.Error as err:
    print(f"Ошибка при подключении к базе данных: {err}")

CHOOSE_OPTION, FREE_COURSES, VEBINAR_SINGIN, NUMBER_SINGIN, EMAIL_SINGIN = range(1,6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Получить бесплатные курсы","Записаться на вебинар"]]
    await context.bot.send_message(
        chat_id=update.message.chat.id,
        text=f"Здравствуйте {update.effective_user.full_name},добро пожаловать в наш телеграм бот",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder="Пожалуйста выберите опцию",
        ),
    )
    cursor = connection.cursor()
    cursor.execute(f"SELECT id FROM vebinar.table WHERE id={update.effective_user.id}")
    fetchar = cursor.fetchone()
    if fetchar == None:
        sql = "INSERT INTO vebinar.table (id, name) VALUES (%s, %s)"
        val = (update.effective_user.id), (update.effective_user.full_name)
        cursor.execute(sql, val)
        connection.commit()
        return CHOOSE_OPTION
    else:
 
        return CHOOSE_OPTION

async def choose_option(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.text == "Получить бесплатные курсы":
        await context.bot.send_message(
            chat_id= update.effective_chat.id,
            text="Это бесплатный пробный курс (такой то такой то) от Евгении Морозовой"
        )
        return await free_courses(update, context)
    elif update.effective_message.text == "Записаться на вебинар":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Введите пожалуйста свое полное имя и фамилию:"
        )
        return VEBINAR_SINGIN
    elif update.effective_message.text == "Да, конечно хочу":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Введите пожалуйста свое полное имя и фамилию:"
        )
        return VEBINAR_SINGIN
    elif update.effective_message.text == "К сожелению нет":
        return await dont_want(update, context)

async def free_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open('telegbot/courses/fae.pdf','rb') as course:
        await context.bot.send_document(chat_id=update.message.chat.id, document=course)
    return await sendmessage(update, context)

async def sendmessage(update:Update, context: ContextTypes.DEFAULT_TYPE ):
    replay_sendmes = [["Да, конечно хочу", "К сожелению нет"]]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Понравились курсы? Хотите записаться на вебинар и лично познакомиться с Евгенией Морозовой?",
        reply_markup=ReplyKeyboardMarkup(
            replay_sendmes,
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )
    return CHOOSE_OPTION

async def dont_want(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id= update.effective_chat.id,
        text="Всего хорошего, на вебинар можно будет записаться в любое другое время"
    )
    return await sendmessage(update,context)

async def vebinar_singin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        cursor = connection.cursor()
        cursor.execute(f'UPDATE vebinar.table SET real_name = "{update.effective_message.text}" WHERE id = {update.effective_user.id}')
        connection.commit()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Введите номер телефона:")
        return NUMBER_SINGIN
async def number_singin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        cursor = connection.cursor()
        cursor.execute(f'UPDATE vebinar.table SET phone = "{update.effective_message.text}" WHERE id = {update.effective_user.id}')
        connection.commit()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Введите свой email:"
        )
        return EMAIL_SINGIN
async def email_singin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        cursor = connection.cursor()
        cursor.execute(f'UPDATE vebinar.table SET email = "{update.effective_message.text}" WHERE id = {update.effective_user.id}')
        connection.commit()

        if "connection" in locals():
            connection.close()

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы зарегестрированы"
            )
def main():
    application = (
        ApplicationBuilder()
        .token("")
        .build()
    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_OPTION: [
                MessageHandler(filters.TEXT, choose_option),
                            ],
            VEBINAR_SINGIN: [
                MessageHandler(filters.TEXT, vebinar_singin)
                            ],
            NUMBER_SINGIN:  [
                MessageHandler(filters.TEXT, number_singin)
                            ],
            EMAIL_SINGIN:   [
                MessageHandler(filters.TEXT, email_singin) 
            ]

        },
        fallbacks=[],
    )


    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
