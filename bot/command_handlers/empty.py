from telegram import Update
from telegram.ext import ContextTypes
from . import register_command_handler
from ..pages import statistic
from ..data import Message

@register_command_handler(['empty_0', 'empty_1'])
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.chat.send_message(**statistic.create_message(update, context))
    context._chat_data.add_message(Message(msg.message_id, msg.date, 'statistic', context._chat_data.get('lang_code')))
