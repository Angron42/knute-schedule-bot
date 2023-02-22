import telebot.types
import logging
from ..settings import bot, chat_configs
from ..pages import select_course

logger = logging.getLogger(__name__)

@bot.callback_query_handler(func=lambda call: call.query == 'select.schedule.faculty')
def handler(call: telebot.types.CallbackQuery):
    logger.debug('Handling callback query')
    faculty_id = int(call.args['facultyId'])
    struct_id = int(call.args['structureId'])
    bot.edit_message_text(**select_course.create_message(call.message, struct_id, faculty_id), message_id=call.message.id)