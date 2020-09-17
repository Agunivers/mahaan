
from telegram import Update, Bot
from telegram.ext import run_async

from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot import dispatcher

from requests import get

@run_async
def ud(bot: Bot, update: Update):
  message = update.effective_message
  text = message.text[len('/ud '):]
  results = get(f'http://api.urbandictionary.com/v0/define?term={text}').json()
  reply_text = f'Word: {text}\nDefinition: {results["list"][0]["definition"]}'
  message.reply_text(reply_text)

__help__ = """
 - /ud:{word} اكتب الكلمة أو التعبير الذي تريد البحث عنه. مثل / UD Telegram Word: Telegram التعريف: نظام شائع من الاتصالات ذات مرة، حيث سيقوم المرسل بالاتصال بخدمة Telegram والتحدث [رسالة] عبر [الهاتف]. من شأنه أن يرسله الشخص الذي يتخذ الرسالة، عبر جهاز TeleType، إلى مكتب برقية بالقرب من [عنوان]. سيتم بعد ذلك تسليم الرسالة باليد إلى المرسل إليه. من عام 1851 إلى أن أوقفت الخدمة في عام 2006، كانت ويسترن يونيون هي خدمة برقية معروفة في العالم.
"""

__mod_name__ = "Urban dictionary"
  
ud_handle = DisableAbleCommandHandler("ud", ud)

dispatcher.add_handler(ud_handle)
