from io import BytesIO
from time import sleep
from typing import Optional, List
from telegram import TelegramError, Chat, Message
from telegram import Update, Bot
from telegram.error import BadRequest
from telegram.ext import MessageHandler, Filters, CommandHandler
from telegram.ext.dispatcher import run_async
from tg_bot.modules.helper_funcs.chat_status import is_user_ban_protected, bot_admin

import tg_bot.modules.sql.users_sql as sql
from tg_bot import dispatcher, OWNER_ID, LOGGER
from tg_bot.modules.helper_funcs.filters import CustomFilters

USERS_GROUP = 4


@run_async
def quickscope(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[1])
        to_kick = str(args[0])
    else:
        update.effective_message.reply_text("لا يبدو أنك تشير إلى دردشة / مستخدم")
    try:
        bot.kick_chat_member(chat_id, to_kick)
        update.effective_message.reply_text("محاولة الحظر " + to_kick + " من" + chat_id)
    except BadRequest as excp:
        update.effective_message.reply_text(excp.message + " " + to_kick)


@run_async
def quickunban(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[1])
        to_kick = str(args[0])
    else:
        update.effective_message.reply_text("لا يبدو أنك تشير إلى دردشة / مستخدم")
    try:
        bot.unban_chat_member(chat_id, to_kick)
        update.effective_message.reply_text("محاولة الحظر " + to_kick + " من" + chat_id)
    except BadRequest as excp:
        update.effective_message.reply_text(excp.message + " " + to_kick)


@run_async
def banall(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = str(args[0])
        all_mems = sql.get_chat_members(chat_id)
    else:
        chat_id = str(update.effective_chat.id)
        all_mems = sql.get_chat_members(chat_id)
    for mems in all_mems:
        try:
            bot.kick_chat_member(chat_id, mems.user)
            update.effective_message.reply_text("حاول الحظر " + str(mems.user))
            sleep(0.1)
        except BadRequest as excp:
            update.effective_message.reply_text(excp.message + " " + str(mems.user))
            continue


@run_async
def snipe(bot: Bot, update: Update, args: List[str]):
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError as excp:
        update.effective_message.reply_text("من فضلك أعطني دردشة إلى صدى!")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            bot.sendMessage(int(chat_id), str(to_send))
        except TelegramError:
            LOGGER.warning("Couldn't send to group %s", str(chat_id))
            update.effective_message.reply_text("لا يمكن إرسال الرسالة. ربما أنا لست جزءا من هذه المجموعة؟")


@run_async
@bot_admin
def getlink(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = int(args[0])
    else:
        update.effective_message.reply_text("لا يبدو أنك تشير إلى دردشة")
    chat = bot.getChat(chat_id)
    bot_member = chat.get_member(bot.id)
    if bot_member.can_invite_users:
        invitelink = bot.get_chat(chat_id).invite_link
        update.effective_message.reply_text(invitelink)
    else:
        update.effective_message.reply_text("ليس لدي حق الوصول إلى رابط الدعوة!")


@bot_admin
def leavechat(bot: Bot, update: Update, args: List[int]):
    if args:
        chat_id = int(args[0])
        bot.leaveChat(chat_id)
    else:
        update.effective_message.reply_text("لا يبدو أنك تشير إلى دردشة")

__help__ = """
**للمالك فقط:**
- /getlink **ايدي المجموعة**: احصل على رابط الدعوة للحصول على دردشة محددة.
- /banall: حظر جميع الأعضاء من الدردشة
- /leavechat **ايدي المجموعة ** : اترك الدردشة
**للمشرف او المالك فقط :**
- /quickscope ** Userid ** ** Chatid **: حظر المستخدم من الدردشة.
- /quickunban **userid** **chatid**: الغاء حظر المستخدم من الدردشة
- /snipe **chatid** **string**: اجعلني أرسل رسالة إلى دردشة محددة.
- /rban **userid** **chatid** حظر المستخدم عن بعد من الدردشة
- /runban **userid** **chatid** الغاء حظر المستخدم عن بعد في الدردشة
- /Stats: تحقق من حالة البوت
- /chatlist: الحصول على قائمة الدردشة
- /gbanlist: الحصول على قائمة المستخدمين gbinned
- /gmutelist: احصل على قائمة مستخدمي GMUTED
- حظر الدردشة عبر / تقييد الأوامر chat_id و / undrestict chat_id
**دعم المستخدم :**
- /Gban : حظر عام للمستخدم
- /Ungban : الغاء حظر عام للمستخدم
- /Gmute : جي كليم المستخدم
- /Ungmute : الغاء جي كليم المستخدم
المشرف / المالك يمكن استخدام هذه الأوامر أيضا.
**للمستخدم:**
- /listsudo لارسال قائمة المشرفين الموجودين في المجموعة
- /listsupport يعطي قائمة مستخدمي الدعم
"""
__mod_name__ = "Special"

SNIPE_HANDLER = CommandHandler("snipe", snipe, pass_args=True, filters=CustomFilters.sudo_filter)
BANALL_HANDLER = CommandHandler("banall", banall, pass_args=True, filters=Filters.user(OWNER_ID))
QUICKSCOPE_HANDLER = CommandHandler("quickscope", quickscope, pass_args=True, filters=CustomFilters.sudo_filter)
QUICKUNBAN_HANDLER = CommandHandler("quickunban", quickunban, pass_args=True, filters=CustomFilters.sudo_filter)
GETLINK_HANDLER = CommandHandler("getlink", getlink, pass_args=True, filters=Filters.user(OWNER_ID))
LEAVECHAT_HANDLER = CommandHandler("leavechat", leavechat, pass_args=True, filters=Filters.user(OWNER_ID))

dispatcher.add_handler(SNIPE_HANDLER)
dispatcher.add_handler(BANALL_HANDLER)
dispatcher.add_handler(QUICKSCOPE_HANDLER)
dispatcher.add_handler(QUICKUNBAN_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
