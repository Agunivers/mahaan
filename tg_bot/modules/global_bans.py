import html
from io import BytesIO
from typing import Optional, List

from telegram import Message, Update, Bot, User, Chat, ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_html

import tg_bot.modules.sql.global_bans_sql as sql
from tg_bot import dispatcher, OWNER_ID, SUDO_USERS, SUPPORT_USERS, STRICT_GBAN
from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.filters import CustomFilters
from tg_bot.modules.helper_funcs.misc import send_to_list
from tg_bot.modules.sql.users_sql import get_all_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
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

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
}


@run_async
def gban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("لا يبدو أنك تشير إلى مستخدم.")
        return

    if int(user_id) in SUDO_USERS:
        message.reply_text("أنا جاسوس، مع عيني الصغيرة ... حرب مستخدم SUDO! لماذا أنت تحول يا رفاق بعضهم البعض؟")
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text("OOOH يحاول شخص ما GBAN مستخدم الدعم! * الاستيلاء على الفشار *")
        return

    if user_id == bot.id:
        message.reply_text("- - - مضحك جدا، يتيح GBAN بنفسي لماذا لا؟ محاولة لطيفة.")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text("هذا ليس المستخدم!")
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            message.reply_text("هذا المستخدم غلق بالفعل؛ سأغير السبب، لكنك لم تمنحني واحدا ...")
            return

        old_reason = sql.update_gban_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if old_reason:
            message.reply_text("هذا المستخدم غالبت بالفعل، والسبب التالي:\n"
                               "<code>{}</code>\n"
                               "لقد ذهبت وتحديثها مع السبب الجديد الخاص بك!".format(html.escape(old_reason)),
                               parse_mode=ParseMode.HTML)
        else:
            message.reply_text("هذا المستخدم غلق بالفعل، ولكن ليس لديه أي سبب؛ لقد ذهبت وتحديثها!")

        return

    message.reply_text("⚡️ * فارض السيطرة 😏 * ⚡️")

    banner = update.effective_user  # type: Optional[User]
    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "<b>حظر عالمي</b>" \
                 "\n#حظر" \
                 "\n<b>الحالة:</b> <code>Enforcing</code>" \
                 "\n<b>بواسطة المشرف:</b> {}" \
                 "\n<b>للمستخدم:</b> {}" \
                 "\n<b>ID:</b> <code>{}</code>" \
                 "\n<b>السبب:</b> {}".format(mention_html(banner.id, banner.first_name),
                                              mention_html(user_chat.id, user_chat.first_name), 
                                                           user_chat.id, reason or "No reason given"), 
                html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            bot.kick_chat_member(chat_id, user_id)
        except BadRequest as excp:
            if excp.message in GBAN_ERRORS:
                pass
            else:
                message.reply_text("لا يمكن أن غبن بسبب: {}".format(excp.message))
                send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "Could not gban due to: {}".format(excp.message))
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, 
                  "{} وقد غلغت بنجاح!".format(mention_html(user_chat.id, user_chat.first_name)),
                html=True)
    message.reply_text("تم غلغان الشخص.")


@run_async
def ungban(bot: Bot, update: Update, args: List[str]):
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("لا يبدو أنك تشير إلى مستخدم.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("هذا ليس المستخدم!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("هذا المستخدم ليس gbanned!")
        return

    banner = update.effective_user  # type: Optional[User]

    message.reply_text("أنا عفوا {}، عالميا مع فرصة ثانية.".format(user_chat.first_name))

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS,
                 "<b>انحدار الحظر العالمي</b>" \
                 "\n#الغاء_الحظر" \
                 "\n<b>الحالة:</b> <code>Ceased</code>" \
                 "\n<b>بواسطة المشرف:</b> {}" \
                 "\n<b>للمستخدم:</b> {}" \
                 "\n<b>ID:</b> <code>{}</code>".format(mention_html(banner.id, banner.first_name),
                                                       mention_html(user_chat.id, user_chat.first_name), 
                                                                    user_chat.id),
                 html=True)

    chats = get_all_chats()
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'kicked':
                bot.unban_chat_member(chat_id, user_id)

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text("لا يمكن الأمم المتحدة غيابان بسبب: {}".format(excp.message))
                bot.send_message(OWNER_ID, "لا يمكن الأمم المتحدة غيابان بسبب: {}".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    send_to_list(bot, SUDO_USERS + SUPPORT_USERS, 
                  "{} وقد عفو عن الحظر!".format(mention_html(user_chat.id, 
                                                                         user_chat.first_name)),
                  html=True)

    message.reply_text("لقد تم منح هذا الشخص غير غالبون ومكفوا!")


@run_async
def gbanlist(bot: Bot, update: Update):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text("لا يوجد أي مستخدمين محظورين! أنت أفينكر مما كنت أتوقع ...")
        return

    banfile = 'Screw these guys.\n'
    for user in banned_users:
        banfile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            banfile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(document=output, filename="gbanlist.txt",
                                                caption="فيما يلي قائمة المستخدمين المحظورين حاليا.")


def check_and_ban(update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text("هذا هو شخص سيء، لا ينبغي أن يكونوا هنا!")


@run_async
def enforce_gban(bot: Bot, update: Update):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    if sql.does_chat_gban(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(bot: Bot, update: Update, args: List[str]):
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("I've enabled gbans in this group. This will help protect you "
                                                "from spammers, unsavoury characters, and the biggest trolls.")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text("لقد تعطيل الحظر في هذه المجموعة. حظر لن يؤثر على المستخدمين"
                                                "بعد الآن. ستكون أقل حماية من أي متصيد او سبامرز"
                                                "على الرغم!")
    else:
        update.effective_message.reply_text("أعطني بعض الحجج لاختيار الإعداد! on/off, yes/no!\n\n"
                                            "الإعداد الحالي الخاص بك هو: {}\n"
                                            "عند صحيح، سيحدث أي رجال البيئة التي تحدث أيضا في مجموعتك."
                                            "عندما خطأ، لن يغادرونك في الرحمة الممكنة"
                                            "spammers.".format(sql.does_chat_gban(update.effective_chat.id)))


def __stats__():
    return "{} المستخدمين المحظورين.".format(sql.num_gbanned_users())


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "محظورة عالميا: <b>{}</b>"
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\n بسبب: {}".format(html.escape(user.reason))
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "هذه الدردشة تنفذ * GBANS *: `{}`.".format(sql.does_chat_gban(chat_id))


__help__ = """
*للمشرف فقط*
 - /gbanstat <on/off/yes/no>: ستعطلان تأثير الحظر العالمي على مجموعتك، أو إرجاع الإعدادات الحالية الخاصة بك.

الحظر، والمعروف أيضا باسم الحظر العالمي، من قبل مالكي روبوت لحظر مرسلي البريد العشوائي في جميع المجموعات. هذا يساعد على حماية \ أنت ومجم مجموعتك عن طريق إزالة الفضلين البريد المزعج في أسرع وقت ممكن. يمكن تعطيلها لك المجموعة عن طريق الاتصال \
/gbanstat
"""

__mod_name__ = "Global Bans"

GBAN_HANDLER = CommandHandler("gban", gban, pass_args=True,
                              filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
UNGBAN_HANDLER = CommandHandler("ungban", ungban, pass_args=True,
                                filters=CustomFilters.sudo_filter | CustomFilters.support_filter)
GBAN_LIST = CommandHandler("gbanlist", gbanlist,
                           filters=CustomFilters.sudo_filter | CustomFilters.support_filter)

GBAN_STATUS = CommandHandler("gbanstat", gbanstat, pass_args=True, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
