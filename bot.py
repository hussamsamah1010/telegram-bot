
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
from langdetect import detect, DetectorFactory

# Ensure consistent language detection results
DetectorFactory.seed = 0

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Bot token from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OWNER_CHAT_ID = int(os.environ.get("OWNER_CHAT_ID"))  # Owner\\'s Telegram Chat ID

# OpenRouter API configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "deepseek/deepseek-chat"

# OpenAI API client (configured for OpenRouter)
client = OpenAI(
    base_url=OPENROUTER_API_BASE,
    api_key=OPENROUTER_API_KEY,
)

# Business services in Arabic
SERVICES = [
    "تصميم الباترونات للملابس (Garment pattern design)",
    "خدمات فنية في برنامج Gerber AccuMark (Technical services in Gerber AccuMark)",
    "بيع برامج مطورة خصيصاً (Selling custom-developed programs)"
]

async def forward_message_to_owner(context: ContextTypes.DEFAULT_TYPE, client_name: str, message_type: str, content: str = None, file_id: str = None) -> None:
    """Forwards client messages and bot replies to the owner."""
    forward_text = f"""رسالة جديدة من العميل:
اسم العميل: {client_name}
نوع الرسالة: {message_type}
"""
    if content:
        forward_text += f"المحتوى: {content}"
    
    try:
        if file_id:
            # For media, send the file directly
            if message_type == "صورة":
                await context.bot.send_photo(chat_id=OWNER_CHAT_ID, photo=file_id, caption=forward_text)
            elif message_type == "مستند":
                await context.bot.send_document(chat_id=OWNER_CHAT_ID, document=file_id, caption=forward_text)
            elif message_type == "رسالة صوتية":
                await context.bot.send_voice(chat_id=OWNER_CHAT_ID, voice=file_id, caption=forward_text)
            else:
                await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=f"{forward_text}\n(ملف غير مدعوم للعرض المباشر)")
        else:
            await context.bot.send_message(chat_id=OWNER_CHAT_ID, text=forward_text)
    except Exception as e:
        logger.error(f"Error forwarding message to owner: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a greeting message when the command /start is issued."""
    user = update.effective_user
    client_name = user.full_name or user.username
    client_message = "/start"

    greeting_message = f"""مرحباً بك يا {user.mention_html()}! أنا بوت مساعد لشركة تصميم الباترونات والخدمات الفنية.
يمكنني مساعدتك في التعرف على خدماتنا والإجابة على أسئلتك.
خدماتنا تشمل:
{os.linesep.join([f’\- {service}’ for service in SERVICES])}

كيف يمكنني مساعدتك اليوم؟ يمكنك طرح سؤال أو استخدام الأوامر التالية:
/services - لعرض الخدمات المتاحة
/contact - للحصول على معلومات الاتصال"""
    await update.message.reply_html(greeting_message)
    await forward_message_to_owner(context, client_name, "نص", client_message + "\n" + greeting_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message when the command /help is issued."""
    user = update.effective_user
    client_name = user.full_name or user.username
    client_message = "/help"

    help_text = f"""أهلاً بك! أنا هنا لمساعدتك في كل ما يتعلق بخدماتنا.
يمكنك سؤالي عن:
- تصميم الباترونات للملابس
- خدمات Gerber AccuMark الفنية
- البرامج المخصصة للبيع
إذا كان لديك سؤال معقد، سأقوم بتوجيهك إلى المختصين لدينا.
الأوامر المتاحة:
/start - لبدء المحادثة والترحيب
/services - لعرض الخدمات المتاحة
/contact - للحصول على معلومات الاتصال"""
    await update.message.reply_text(help_text)
    await forward_message_to_owner(context, client_name, "نص", client_message + "\n" + help_text)

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with available services when the command /services is issued."""
    user = update.effective_user
    client_name = user.full_name or user.username
    client_message = "/services"

    services_text = f"""يسعدنا أن نقدم لك الخدمات التالية:
{os.linesep.join([f’\- {service}’ for service in SERVICES])}

إذا كان لديك أي استفسار حول أي خدمة، فلا تتردد في السؤال!"""
    await update.message.reply_text(services_text)
    await forward_message_to_owner(context, client_name, "نص", client_message + "\n" + services_text)

async def contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends contact information when the command /contact is issued."""
    user = update.effective_user
    client_name = user.full_name or user.username
    client_message = "/contact"

    contact_text = f"""للتواصل معنا، يمكنك استخدام المعلومات التالية:
البريد الإلكتروني: info@example.com
الهاتف: +966 50 123 4567
الموقع الإلكتروني: www.example.com
أو يمكنك ترك بياناتك وسنتواصل معك قريباً."""
    await update.message.reply_text(contact_text)
    await forward_message_to_owner(context, client_name, "نص", client_message + "\n" + contact_text)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles photos sent by clients."""
    user = update.effective_user
    client_name = user.full_name or user.username
    photo_file_id = update.message.photo[-1].file_id  # Get the largest photo

    acknowledgment_message = "تم استلام الصورة، شكراً! سيتم مراجعتها والرد عليك قريباً"
    await update.message.reply_text(acknowledgment_message)
    logger.info(f"Photo received from {client_name}. Forwarding to owner.")
    await forward_message_to_owner(context, client_name, "صورة", content=acknowledgment_message, file_id=photo_file_id)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles documents sent by clients."""
    user = update.effective_user
    client_name = user.full_name or user.username
    document_file_id = update.message.document.file_id
    document_caption = update.message.caption or "(لا يوجد وصف)"

    acknowledgment_message = "تم استلام المستند، شكراً! سيتم مراجعته والرد عليك قريباً"
    await update.message.reply_text(acknowledgment_message)
    logger.info(f"Document received from {client_name}. Forwarding to owner.")
    await forward_message_to_owner(context, client_name, "مستند", content=f"وصف: {document_caption}\n{acknowledgment_message}", file_id=document_file_id)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles voice messages sent by clients."""
    user = update.effective_user
    client_name = user.full_name or user.username
    voice_file_id = update.message.voice.file_id

    acknowledgment_message = "تم استلام الرسالة الصوتية، شكراً! سيتم الاستماع إليها والرد عليك قريباً"
    await update.message.reply_text(acknowledgment_message)
    logger.info(f"Voice message received from {client_name}. Forwarding to owner.")
    await forward_message_to_owner(context, client_name, "رسالة صوتية", content=acknowledgment_message, file_id=voice_file_id)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles regular text messages using OpenRouter (DeepSeek) for intelligent responses."""
    user = update.effective_user
    client_name = user.full_name or user.username
    user_message = update.message.text
    logger.info(f"User message: {user_message}")
    logger.info(f"Attempting to get response from OpenRouter (DeepSeek) for user: {client_name}")

    try:
        detected_lang = detect(user_message)
        logger.info(f"Detected language: {detected_lang}")
    except Exception as e:
        logger.warning(f"Could not detect language, defaulting to Arabic: {e}")
        detected_lang = "ar"

    # Define a system prompt for the OpenRouter model
    system_prompt_base = (
        "أنت بوت مساعد لشركة تقدم خدمات تصميم الباترونات للملابس، خدمات فنية في برنامج Gerber AccuMark، وبيع برامج مطورة خصيصاً. "
        "مهمتك هي الترحيب بالعملاء، شرح الخدمات، الإجابة على الأسئلة الشائعة بأسلوب احترافي وودود. "
        "إذا طلب العميل معلومات اتصال، قم بتوجيهه إلى الأمر /contact. "
        "إذا كانت المعلومات المطلوبة هي بيانات العميل (الاسم، ما يحتاجه، معلومات الاتصال)، قم بطلب هذه المعلومات منه. "
        "إذا كان السؤال معقدًا ولا يمكنك الإجابة عليه، اطلب من العميل ترك بياناته (الاسم، رقم الهاتف/البريد الإلكتروني، وما يحتاجه) وأخبره أن صاحب العمل سيتواصل معه قريبًا."
    )

    language_instruction = "You must always reply in the same language the client uses. If they write in English, reply in English. If they write in Arabic, reply in Arabic. Always match the client\\\\'s language."

    system_prompt = f"{system_prompt_base} {language_instruction}"

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL, # Using the specified OpenRouter model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200,
            temperature=0.7,
        )
        bot_response = response.choices[0].message.content
        logger.info(f"OpenRouter (DeepSeek) response: {bot_response}")
        await update.message.reply_text(bot_response)
        logger.info(f"Bot replied to user: {client_name}")
        await forward_message_to_owner(context, client_name, "نص", user_message + "\n" + bot_response)
    except Exception as e:
        logger.error(f"Error communicating with OpenRouter (DeepSeek): {e}", exc_info=True)
        error_message = "عذرًا، حدث خطأ أثناء معالجة طلبك. يرجى المحاولة مرة أخرى لاحقًا."
        await update.message.reply_text(error_message)
        await forward_message_to_owner(context, client_name, "نص", user_message + "\n" + error_message)

async def handle_unsupported_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles unsupported message types."""
    user = update.effective_user
    client_name = user.full_name or user.username
    message_type = update.message.effective_attachment.mime_type if update.message.effective_attachment else "غير معروف"

    acknowledgment_message = "عذرًا، لا يمكنني التعامل مع هذا النوع من الرسائل حالياً. يرجى إرسال رسالة نصية أو صورة أو مستند أو رسالة صوتية."
    await update.message.reply_text(acknowledgment_message)
    logger.info(f"Unsupported message type ({message_type}) received from {client_name}. Acknowledged and forwarding to owner.")
    await forward_message_to_owner(context, client_name, f"غير مدعوم ({message_type})", content=acknowledgment_message)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("services", show_services))
    application.add_handler(CommandHandler("contact", contact_info))

    # Message handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.TEXT & ~filters.PHOTO & ~filters.Document.ALL & ~filters.VOICE, handle_unsupported_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(poll_interval=1.0, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
