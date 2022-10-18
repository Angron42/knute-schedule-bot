from telebot import types
from ..settings import tg_logger

def create_message(message: types.Message) -> dict:

    chat_dir = tg_logger.get_chat_log_dir(message.chat.id)

    file = open(str(chat_dir) + '/messages.txt', 'r')
    for messages, line in enumerate(file):
        if messages == 0:
            first_msg_date = line[1:line.index(']')]
    file.close()

    file = open(str(chat_dir) + '/cb_queries.txt', 'r')
    for clicks, line in enumerate(file):
        pass
    file.close()

    markup = types.InlineKeyboardMarkup()
    message_text = '*Statistic*\n\nThis chat ID: {chat_id}\nYour ID: {user_id}\nMessages: {messages}\nButtons clicks: {clicks}\nFirst message: {first}'.format(
        chat_id=message.chat.id,
        user_id=message.from_user.id,
        messages=messages,
        clicks=clicks,
        first=first_msg_date
    )

    markup.add(
        types.InlineKeyboardButton(text=message.lang['text']['button_menu'], callback_data='open.menu'),
        types.InlineKeyboardButton(text='How Did We Get Here?', url='https://github.com/Angron42/knute-schedule-bot')
    )

    msg = {
        'chat_id': message.chat.id,
        'text': message_text,
        'reply_markup': markup,
        'parse_mode': 'Markdown'
    }

    return msg
