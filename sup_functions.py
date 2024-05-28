import aiosqlite
import aiohttp
import asyncio

import re



db_path="db_avito.sqlite3"

# Этапы воронки
sales_funnel_stages = {
    0: {'text': 'Здравствуйте', 'answers_crm':[], 'answers_next_q':[]},
    1: {'text': 'Ваше первое сообщение', 'answers_crm':['1','2','3','4'], 'answers_next_q':['5']},
    2: {'text': 'Ваше второе сообщение', 'answers_crm':['1','2','3','4','5','6'], 'answers_next_q':['7']},
    3: {'text': 'Поздравляем', 'answers_crm':[], 'answers_next_q':[]},
    4: {'text': 'Квота', 'answers_crm':[], 'answers_next_q':[] },
}
final_status_kval = 3
final_status_nekval = 4
got_phone = 5

messages_dict = {
    0: "Здравствуйте",
    1: "Ваше первое сообщение",
    2: "Ваше второе сообщение",
    3: "Ваше третье сообщение",
    4: "Ваше четвертое сообщение",
}


# async def is_new_chat(message_data):
#     if message_data.get('payload') and message_data.get('payload').get('type') == 'message':
#         message_information = message_data.get('payload')
#         chat_id = message_information['value'].get('chat_id')
#         # async with 

# db_path = "db_avito.sqlite3"
async def check_chat_and_get_status(chat_id, author_id, api_token, user_id, text):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)):
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("SELECT status FROM dialogs WHERE chat_id = ? AND author_id = ?", (chat_id, author_id))
            row = await cursor.fetchone()
            await cursor.close()
            if row:
                return await process_message(chat_id, author_id, row[0], text, api_token, user_id)
            else:
                return await add_new_chat(chat_id, author_id, api_token, user_id)

async def add_new_chat(chat_id, author_id, api_token, user_id):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("INSERT INTO dialogs (chat_id, author_id, status) VALUES (?, ?, ?)", (chat_id, author_id, 1))
        await db.commit()
    await send_message(chat_id, sales_funnel_stages.get(0).get('text'), api_token, user_id)
    await asyncio.sleep(3)
    return await send_message(chat_id, sales_funnel_stages.get(1).get('text'), api_token, user_id)

async def send_message(chat_id, message, api_token, user_id):
    api_url = f"https://api.avito.ru/messenger/v1/accounts/{user_id}/chats/{chat_id}/messages"

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "message": {
            "text": f"{message}"
        },
        "type": "text"
    }
    
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.post(api_url, headers=headers, json=data) as response:
            if response.status == 200:
                print("Сообщение отправлено")
            else:
                print("Ошибка при отправке сообщения")


def validate_phone_number(phone_number):
    # Удаление пробелов, скобок и дефисов из строки
    cleaned_number = re.sub(r"[ \-\(\)]", "", phone_number)
    
    # Проверка соответствия номера формату +79997537474
    if re.match(r"^\+7\d{10}$", cleaned_number):
        return cleaned_number
    else:
        return False

async def process_message(chat_id, author_id, status, text, api_token, user_id):
    is_to_kval = False
    is_to_nekval = False

    if status not in sales_funnel_stages.keys():
        return

    if status == final_status_kval:
        res_func = validate_phone_number(text)
        if res_func:
            print(f'Номер телефона бедолаги: {res_func}')
            new_message_text = 'Ожидайте, я с вами свяжусь в ближайшее время'
            await send_message(chat_id, new_message_text, api_token, user_id)

            async with aiosqlite.connect(db_path) as db:
                await db.execute("UPDATE dialogs SET phone_number =? WHERE chat_id =? AND author_id =?", (res_func, chat_id, author_id))
                await db.commit()
            return
        else:
            new_message_text = 'Ожидайте, я с вами свяжусь в ближайшее время'
            await send_message(chat_id, new_message_text, api_token, user_id)
            return
    
    if status == final_status_nekval:
        # Здесь надо оправить сообщение про ожидайте, с вами свяжется человек
        new_message_text = 'Ожидайте, я с вами свяжусь в ближайшее время'
        await send_message(chat_id, new_message_text, api_token, user_id)
        return
    
    answers_crm = sales_funnel_stages[status].get('answers_crm')
    answers_next_q = sales_funnel_stages[status].get('answers_next_q')

    if text in answers_crm:
        status = final_status_kval
        is_to_kval = True
        
    elif text in answers_next_q:
        status += 1
        if status == final_status_kval:
            status = final_status_nekval
            is_to_nekval = False
    
    else: # он написал фигню
        await send_message(chat_id, 'Пожалуйста, напишите 1 цифру из предложенных', api_token, user_id)
        return

    async with aiosqlite.connect(db_path) as db:
        await db.execute("UPDATE dialogs SET status =? WHERE chat_id =? AND author_id =?", (status, chat_id, author_id))
        await db.commit()

    new_message_text = sales_funnel_stages[status].get('text')
    await send_message(chat_id, new_message_text, api_token, user_id)

    if is_to_kval:
        await move_to_kval()

    if is_to_nekval:
        await move_to_nekval()
    

async def move_to_kval():
    print("квал")
    


async def move_to_nekval():
    print("не квал")
    
    



#