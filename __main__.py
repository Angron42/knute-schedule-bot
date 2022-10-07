import telebot
import os
import sys
import time
import logging

from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault('MODE', 'prod')
os.chdir(sys.path[0])

import src.messages as create_message
from src.chat_configs import chat_configs
from src.tg_logger import TelegramLogger
from src.modify_message import modify_message



if not os.path.exists('logs'):
    os.mkdir('logs')

if not os.path.exists('logs/debug'):
    os.mkdir('logs/debug')

logging.basicConfig(
    level=os.getenv('LOGGING_LEVEL'),
    filename=os.path.join(os.getcwd(), 'logs/debug/%s.log' % datetime.now().strftime('%Y-%m-%d %H-%M-%S')),
    filemode='a',
    format='%(asctime)s [%(levelname)s] - %(message)s'
)

logger = logging.getLogger()
logger.info('Starting application')

tg_logger = TelegramLogger(Path('logs/telegram').absolute())
bot_token = os.getenv('BOT_TOKEN')
telebot.apihelper.ENABLE_MIDDLEWARE = True
bot = telebot.TeleBot(bot_token)



@bot.middleware_handler(update_types=['message'])
def message_middleware(bot_instance, message: telebot.types.Message):
    logger.debug('Called main message middleware')
    modify_message(message=message)

@bot.middleware_handler(update_types=['callback_query'])
def callback_query_middleware(bot_instance, call: telebot.types.CallbackQuery):
    logger.debug('Called main callback query middleware')
    modify_message(call=call)

bot.middleware_handler(update_types=['message'])(tg_logger.message_middleware)
bot.middleware_handler(update_types=['callback_query'])(tg_logger.callback_query_middleware)



@bot.callback_query_handler(func=lambda call: call.data.startswith('open.'))
def handle_open(call):
    logger.debug('Handling callback query %s' % call.data)

    data = call.data[call.data.index('.') + 1:]

    if data == 'menu':
        msg = create_message.create_menu_message(call.message)
        bot.edit_message_text(**msg, message_id=call.message.message_id)

    elif data == 'select_group':
        bot.edit_message_text(**create_message.create_select_structure_message(call.message), message_id=call.message.message_id)
    
    elif data == 'select_lang':
        bot.edit_message_text(**create_message.create_lang_select_message(call.message), message_id=call.message.message_id)

    elif data == 'settings':
        bot.edit_message_text(**create_message.create_settings_message(call.message), message_id=call.message.message_id)

    elif data == 'more':
        bot.edit_message_text(**create_message.create_more_message(call.message), message_id=call.message.message_id)

    elif data == 'info':
        bot.edit_message_text(**create_message.create_info_message(call.message), message_id=call.message.message_id)

    elif data.startswith('schedule'):
        data = data[data.index('.') + 1:]
        today = datetime.today()

        if data == 'today':
            date = today.strftime('%Y-%m-%d')

        elif data == 'tomorrow':
            date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        elif data.startswith('day='):
            date = data.split('=')[1]

        else:
            return

        bot.edit_message_text(**create_message.create_schedule_message(call.message, date), message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('select.'))
def handle_select(call):
    logger.debug('Handling callback query %s' % call.data)

    dot_index = call.data.index('.')
    data = call.data[dot_index + 1:]

    if data.startswith('schedule'):
        dot_index = data.index('.')
        data = data[dot_index + 1:]

        delimeter_index = data.index('=')
        
        action = data[:delimeter_index]
        action_value = data[delimeter_index + 1:]

        call.message.config['schedule'][action] = action_value
        chat_configs.set_chat_config_field(call.message.chat.id, 'schedule', call.message.config['schedule'])

        if action == 'structure_id':
            message = create_message.create_select_faculty_message(call.message)
        elif action == 'faculty_id':
            message = create_message.create_select_course_message(call.message)
        elif action == 'course':
            message = create_message.create_select_group_message(call.message)
        elif action == 'group_id':
            message = create_message.create_menu_message(call.message)
        else:
            return

        bot.edit_message_text(
            **message,
            message_id=call.message.message_id
        )

    elif data.startswith('lang'):
        delimeter_index = data.index('=')
        lang = data[delimeter_index + 1:]
        
        chat_configs.set_chat_config_field(call.message.chat.id, 'lang', lang)
        call.message.update_config()

        bot.edit_message_text(
            **create_message.create_menu_message(call.message),
            message_id=call.message.message_id
        )



@bot.message_handler(commands=['start'])
def start_command(message):
    logger.info('Handling /start command from chat %s' % message.chat.id)
    bot.send_message(**create_message.create_select_structure_message(message))

@bot.message_handler(commands=['select'])
def select_command(message):
    logger.info('Handling /select command from chat %s' % message.chat.id)
    bot.send_message(**create_message.create_select_structure_message(message))

@bot.message_handler(commands=['menu'])
def menu_command(message):
    logger.info('Handling /menu command from chat %s' % message.chat.id)
    msg = create_message.create_menu_message(message)
    bot.send_message(**msg)

@bot.message_handler(commands=['settings'])
def settings_command(message):
    logger.info('Handling /settings command from chat %s' % message.chat.id)
    msg = create_message.create_settings_message(message)
    bot.send_message(**msg)

@bot.message_handler(commands=['lang'])
def lang_command(message):
    logger.info('Handling /lang command from chat %s' % message.chat.id)
    msg = create_message.create_lang_select_message(message)
    bot.send_message(**msg)

@bot.message_handler(commands=['today'])
def schedule_today_command(message):
    logger.info('Handling /today command from chat %s' % message.chat.id)
    date = datetime.today()
    bot.send_message(**create_message.create_schedule_message(message, date.strftime('%Y-%m-%d')))

@bot.message_handler(commands=['tomorrow'])
def schedule_tomorrow_command(message):
    logger.info('Handling /tomorrow command from chat %s' % message.chat.id)
    date = datetime.today() + timedelta(days=1)
    bot.send_message(**create_message.create_schedule_message(message, date.strftime('%Y-%m-%d')))

@bot.message_handler(content_types=['text'], func=lambda msg: msg.text.startswith('/empty_'))
def empty_command(message):
    logger.info('Handling /empty_* command from chat %s' % message.chat.id)
    bot.send_message(**create_message.create_statistic_message(message))



if os.getenv('MODE') == 'prod':
    logger.info('Running in production mode')

    while True:
        logger.debug('Start polling')

        try:
            bot.polling(none_stop=True)

        except Exception as e:
            logger.error('Bot polling error: %s' % e)
            time.sleep(2)

elif os.getenv('MODE') == 'dev':
    logger.info('Running in dev mode')

    while True:
        logger.debug('Start polling')
        bot.polling(none_stop=True)
