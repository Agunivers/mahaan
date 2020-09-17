import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, User, CallbackQuery

from tg_bot import dispatcher, BAN_STICKER, LOGGER
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_bot_admin
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.filters import CustomFilters

RBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}

RUNBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat"
}



@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("لا يبدو أنك تشير إلى مستخدم.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("لا أستطيع أن أجد هذا المستخدم")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("أتمنى حقا أن أتمكن من حظر المسؤولين ...")
        return ""

    if user_id == bot.id:
        message.reply_text("مابالك تريد أن أحظر نفسي، هل أنت مجنون؟")
        return ""

    log = "<b>{}:</b>" \
          "\n#حظر" \
          "\n<b>بواسطة المشرف:</b> {}" \
          "\n<b>للمستخدم:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>وذالك بسبب:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        keyboard = []
        reply = "{} حظر بنجاح!".format(mention_html(member.user.id, member.user.first_name))
        message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('حظر!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("حسنا لعنة، لا أستطيع حظر هذا المستخدم.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("لا يبدو أنك تشير إلى مستخدم.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("لا أستطيع أن أجد هذا المستخدم")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("أتمنى حقا أن أتمكن من حظر المسؤولين ...")
        return ""

    if user_id == bot.id:
        message.reply_text("أنا لا سأحظر نفسي، هل أنت مجنون؟")
        return ""

    if not reason:
        message.reply_text("لم تقم بتحديد وقت لحظر هذا المستخدم!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#تم حظر TEMP" \
          "\n<b>بواسطة المشرف:</b> {}" \
          "\n<b>للمستخدم:</b> {}" \
          "\n<b>لمدة:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>بسبب:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("حظر! سيتم حظر المستخدم ل {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("حظر! سيتم حظر المستخدم ل {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("حسنا لعنة، لا أستطيع حظر هذا المستخدم.")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("لا أستطيع أن أجد هذا المستخدم")
            return ""
        else:
            raise

    if is_user_ban_protected(chat, user_id):
        message.reply_text("أتمنى حقا أن أركل مدراء ...")
        return ""

    if user_id == bot.id:
        message.reply_text("نعم أنا لن أفعل ذلك")
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("ركل!")
        log = "<b>{}:</b>" \
              "\n#طرد-ركل-" \
              "\n<b>بواسطة المشرف:</b> {}" \
              "\n<b>للمستخدم:</b> {}".format(html.escape(chat.title),
                                         mention_html(user.id, user.first_name),
                                         mention_html(member.user.id, member.user.first_name))
        if reason:
            log += "\n<b>بسبب:</b> {}".format(reason)

        return log

    else:
        message.reply_text("حسنا لعنة، لا أستطيع ركلة هذا المستخدم.")

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(bot: Bot, update: Update):
    user_id = update.effective_message.from_user.id
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text("أتمنى أن أتمكن منك لاكنك مسؤول")
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text("لا مشكلة.")
    else:
        update.effective_message.reply_text("هوة؟ لا أستطيع :/")


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(bot: Bot, update: Update, args: List[str]) -> str:
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("لا أستطيع أن أجد هذا المستخدم")
            return ""
        else:
            raise

    if user_id == bot.id:
        message.reply_text("كيف يمكنني أن أبني أنا إذا لم أكن هنا ...؟")
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text("لماذا تحاول الغاء حظر شخص ما بالفعل في الدردشة؟")
        return ""

    chat.unban_member(user_id)
    message.reply_text("نعم، يمكن لهذا المستخدم الانضمام!")

    log = "<b>{}:</b>" \
          "\n#الغي_الحظر" \
          "\n<b>بواسطة المشرف:</b> {}" \
          "\n<b>للمستخدم:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name))
    if reason:
        log += "\n<b>بسبب:</b> {}".format(reason)

    return log


@run_async
@bot_admin
def rban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("لا يبدو أنك تشير إلى دردشة / مستخدم.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("لا يبدو أنك تشير إلى مستخدم.")
        return
    elif not chat_id:
        message.reply_text("لا يبدو أنك تشير إلى دردشة.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("لم يتم العثور على الدردشة! تأكد من إدخال معرف دردشة صالح وأنا جزء من الدردشة.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("أنا آسف، لكن هذا دردشة خاصة!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("لا أستطيع تقييد الناس هناك! تأكد من أنني مشرف ويمكنه حظر المستخدمين.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("لا أستطيع أن أجد هذا المستخدم")
            return
        else:
            raise

    if is_user_ban_protected(chat, user_id, member):
        message.reply_text("أتمنى حقا أن أتمكن من حظر المسؤولين ...")
        return

    if user_id == bot.id:
        message.reply_text("مابالك تريد أن أحظر نفسي، هل أنت مجنون؟")
        return

    try:
        chat.kick_member(user_id)
        message.reply_text("حظر!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('حظر!', quote=False)
        elif excp.message in RBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("حسنا لعنة، لا أستطيع حظر هذا المستخدم.")

@run_async
@bot_admin
def runban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message

    if not args:
        message.reply_text("لا يبدو أنك تشير إلى دردشة / مستخدم.")
        return

    user_id, chat_id = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("لا يبدو أنك تشير إلى مستخدم.")
        return
    elif not chat_id:
        message.reply_text("لا يبدو أنك تشير إلى دردشة.")
        return

    try:
        chat = bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message == "Chat not found":
            message.reply_text("لم يتم العثور على الدردشة! تأكد من إدخال معرف دردشة صالح وأنا جزء من الدردشة.")
            return
        else:
            raise

    if chat.type == 'private':
        message.reply_text("أنا آسف، لكن هذا دردشة خاصة!")
        return

    if not is_bot_admin(chat, bot.id) or not chat.get_member(bot.id).can_restrict_members:
        message.reply_text("لا أستطيع أن أجد الناس هناك! تأكد من أنني مشرف ويمكن لمستخدمي شبان.")
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("لا أستطيع أن أجد هذا المستخدم هناك")
            return
        else:
            raise
            
    if is_user_in_chat(chat, user_id):
        message.reply_text("لماذا تحاول إلغاء حظر شخص ما في تلك الدردشة؟")
        return

    if user_id == bot.id:
        message.reply_text("أنا لن أحظر نفسي، أنا مشرف هناك!")
        return

    try:
        chat.unban_member(user_id)
        message.reply_text("نعم، يمكن لهذا المستخدم الانضمام إلى الدردشة!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('الغي حظرة!', quote=False)
        elif excp.message in RUNBAN_ERRORS:
            message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR unbanning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("حسنا لعنة، لا أستطيع إلغاء الحظر هذا المستخدم.")


__help__ = """
 - /kickme: ركل المستخدم الذي أصدر الأمر

*Admin only:*
 - /ban <userhandle>: تحظر المستخدم. (عبر مقبض، أو الرد)
 - /tban <userhandle> x(m/h/d): لتحظر المستخدم x الوقت. (عبر اليوزر، أو الرد). m = دقائق، h = ساعات، d = أيام.
 - /unban <userhandle>: لا يقوم على المستخدم. (عبر مقبض، أو الرد)
 - /kick <userhandle>: ركل المستخدم، (عبر مقبض، أو الرد)
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)
RBAN_HANDLER = CommandHandler("rban", rban, pass_args=True, filters=CustomFilters.sudo_filter)
RUNBAN_HANDLER = CommandHandler("runban", runban, pass_args=True, filters=CustomFilters.sudo_filter)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
dispatcher.add_handler(RBAN_HANDLER)
dispatcher.add_handler(RUNBAN_HANDLER)
