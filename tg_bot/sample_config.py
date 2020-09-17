if not __name__.endswith("sample_config"):
    import sys
    print("تم العثور على README للقراءة. قم بتوسيع نموذج التكوين هذا إلى ملف تكوين ، لا تقم فقط بإعادة التسمية والتغيير "
          "القيم هنا. القيام بذلك سوف يأتي بنتائج عكسية عليك. \ عدم الانسحاب.", file=sys.stderr)
    quit(1)


# قم بإنشاء ملف config.py جديد في نفس الدليل واستيراد ، ثم قم بتوسيع هذه الفئة.
class Config(object):
    LOGGER = True

    # مطلوب
    API_KEY = ""
    OWNER_ID = "683538773" # إذا كنت لا تعرف ، فقم بتشغيل الروبوت وقم بإجراء / معرف في محادثتك الخاصة معه
    OWNER_USERNAME = "ViruZs"

    # موصى به
    SQLALCHEMY_DATABASE_URI = 'sqldbtype://username:pw@hostname:port/db_name'  # needed for any database modules
    MESSAGE_DUMP = None  # اللازمة للتأكد من استمرار رسائل "الحفظ من"
    LOAD = []
    NO_LOAD = ['translation', 'rss']
    WEBHOOK = False
    URL = None

    # اختياري
    SUDO_USERS = []  # قائمة المعرفات (وليس أسماء المستخدمين) للمستخدمين الذين لديهم وصول sudo إلى الروبوت.
    SUPPORT_USERS = []  # قائمة المعرفات (وليس أسماء المستخدمين) للمستخدمين المسموح لهم باستخدام gban ، ولكن يمكن أيضًا حظرهم.
    WHITELIST_USERS = []  # قائمة المعرفات (وليس أسماء المستخدمين) للمستخدمين الذين لن يتم حظرهم / طردهم من قبل الروبوت.
    DONATION_LINK = None  # EG ، paypal
    CERT_PATH = None
    PORT = 5000
    DEL_CMDS = False  # ما إذا كان يجب عليك حذف أوامر "يجب أن ينقر النص الأزرق" أم لا
    STRICT_GBAN = False
    WORKERS = 8  # عدد النقاط الفرعية المراد استخدامها. هذا هو المبلغ الموصى به - انظر بنفسك إلى الأفضل!
    BAN_STICKER = 'CAADAgADOwADPPEcAXkko5EB3YGYAg'  # 
    ALLOW_EXCL = False  # سمح! الأوامر وكذلك /


class Production(Config):
    LOGGER = False


class Development(Config):
    LOGGER = True
