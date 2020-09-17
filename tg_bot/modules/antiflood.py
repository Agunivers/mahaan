import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import Filters, MessageHandler, CommandHandler, run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.chat_status import is_user_admin, user_admin, can_restrict
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.sql import antiflood_sql as sql

FLOOD_GROUP = 3


@run_async
@loggable
def check_flood(bot: Bot, update: Update) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]

    if not user:  # ignore channels
        return ""

    # ignore admins
    if is_user_admin(chat, user.id):
        sql.update_flood(chat.id, None)
        return ""

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        chat.kick_member(user.id)
        msg.reply_text("لا تزعج الآخرين أنك لا حاجة لهذه المجموعة بعد الآن ...")

        return "<b>{}:</b>" \
               "\n#حظر" \
               "\n<b>للمستخدم:</b> {}" \
               "\nغمرت المجموعة.".format(html.escape(chat.title),
                                             mention_html(user.id, user.first_name))

    except BadRequest:
        msg.reply_text("لا يمكنك استخدام هذه الخدمة طالما أنك لا تعطيني أذونات.")
        sql.set_flood(chat.id, 0)
        return "<b>{}:</b>" \
               "\n#معلومات" \
               "\nليس لديك أذونات ركلة، لذلك تعطيلها تلقائيا Antiflood.".format(chat.title)


@run_async
@user_admin
@can_restrict
@loggable
def set_flood(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    if len(args) >= 1:
        val = args[0].lower()
        if val == "off" or val == "no" or val == "0":
            sql.set_flood(chat.id, 0)
            message.reply_text("لن أتراجع أولئك الذين يضحكون.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                message.reply_text("لن أتراجع أولئك الذين يضحكون.")
                return "<b>{}:</b>" \
                       "\n#مجموعة_الفيضان" \
                       "\n<b>بواسطة المشرف:</b> {}" \
                       "\nالمعوقين أنفئون.".format(html.escape(chat.title), mention_html(user.id, user.first_name))

            elif amount < 3:
                message.reply_text("يجب أن يكون Antiflood إما 0 (معطل)، أو رقم أكبر من 3!")
                return ""

            else:
                sql.set_flood(chat.id, amount)
                message.reply_text("مراقبة الرسائل {} تمت إضافته لحساب ".format(amount))
                return "<b>{}:</b>" \
                       "\n#مجموعة_الفيضان" \
                       "\n<b>بواسطة المشرف:</b> {}" \
                       "\nSet مضاد ل <code>{}</code>.".format(html.escape(chat.title),
                                                                    mention_html(user.id, user.first_name), amount)

        else:
            message.reply_text("أنا لا أفهم ما تقوله .... إما استخدام الرقم أو استخدام نعم لا")

    return ""


@run_async
def flood(bot: Bot, update: Update):
    chat = update.effective_chat  # type: Optional[Chat]

    limit = sql.get_flood_limit(chat.id)
    if limit == 0:
        update.effective_message.reply_text("I am not doing message control right now!")
    else:
        update.effective_message.reply_text(
            " {} سأترك الكعكة للشخص الذي يرسل الرسالة أكثر في نفس الوقت.".format(limit))


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "* لا * حاليا فرض السيطرة على الفيضانات."
    else:
        return " تم ضبط عنصر تحكم الرسائل على `{}`.".format(limit)


__help__ = """
 - /flood: لمعرفة تحكم الرسائل الحالية ..

*للمشرف فقط*
 - /setflood <int/'no'/'off'>: تمكين أو تعطيل مراقبة الفيضانات
"""

__mod_name__ = "AntiFlood"

FLOOD_BAN_HANDLER = MessageHandler(Filters.all & ~Filters.status_update & Filters.group, check_flood)
SET_FLOOD_HANDLER = CommandHandler("setflood", set_flood, pass_args=True, filters=Filters.group)
FLOOD_HANDLER = CommandHandler("flood", flood, filters=Filters.group)

dispatcher.add_handler(FLOOD_BAN_HANDLER, FLOOD_GROUP)
dispatcher.add_handler(SET_FLOOD_HANDLER)
dispatcher.add_handler(FLOOD_HANDLER)
