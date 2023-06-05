"""
This is the main file of the bot.
"""

import os
import logging
import settings
from telegram.ext import MessageHandler, CallbackQueryHandler
from bot.utils import load_langs


settings.langs = load_langs(os.getenv('LANGS_PATH'))
logger = logging.getLogger()
logger.info('Starting application')


from settings import bot, tg_logger
from bot.buttons import *
from bot.buttons import handlers as button_handlers, register_button
from bot.commands import *
from bot.commands import handlers as command_handlers
from bot.notifier import scheduler
from bot.data import ContextManager, ChatData
from bot import errorhandler, pages


async def set_chat_accessible(upd, ctx):
    chat_data = ChatData(upd.effective_chat.id)

    if not chat_data.get('_accessible'):
        chat_data.set('_accessible', True)


async def button_logger(upd, ctx):
    logger.info('[chat/%s user/%s msg/%s] callback query: %s',
        upd.callback_query.message.chat.id,
        upd.callback_query.from_user.id,
        upd.callback_query.message.id,
        upd.callback_query.data
    )


async def message_logger(upd, ctx):
    logger.info('[chat/%s user/%s msg/%s] message: %s',
        upd.message.chat.id,
        upd.message.from_user.id,
        upd.message.id,
        upd.message.text
    )
    

async def button_post_logger(upd, ctx):
    manager = ContextManager(upd, ctx)
    await tg_logger.callback_query_handler(manager)


async def message_post_logger(upd, ctx):
    manager = ContextManager(upd, ctx)
    await tg_logger.message_handler(manager)


@register_button()
async def unsupported_btn_handler(ctx):
    await ctx.update.callback_query.answer(ctx.lang.get('alert.callback_query_unsupported'), show_alert=True)
    msg = await ctx.update.callback_query.message.edit_text(**pages.menu(ctx))
    ctx.chat_data.save_message('menu', msg)


bot.add_handlers([CallbackQueryHandler(button_logger), MessageHandler(None, message_logger)], 0)
bot.add_handlers([CallbackQueryHandler(set_chat_accessible), MessageHandler(None, set_chat_accessible)], 5)
bot.add_handlers(button_handlers + command_handlers, 10)
bot.add_handlers([CallbackQueryHandler(button_post_logger), MessageHandler(None, message_post_logger)], 20)
bot.add_error_handler(errorhandler.handler)


# Run notifications scheduler
scheduler.start()
# Run bot
bot.run_polling()
