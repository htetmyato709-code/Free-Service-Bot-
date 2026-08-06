import os
import random
import string
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configuration
BOT_TOKEN = "8999318803:AAE1iGnIWsAKdUa1fltCJoua3yFLSnvEqJM"
OWNER_ID = 8305397892
OWNER_USERNAME = "@Xylo_Offical"

# Conversation States
BROADCAST_STATE = 1
REDEEM_CODE_STATE = 2

# In-Memory Data Store
users = {} 

services = {
    "1": {"name": "Telegram Post View Free 1K", "cost_per_1k": 50, "min": 100, "max": 100000},
    "2": {"name": "Telegram Reaction Free 1K", "cost_per_1k": 100, "min": 10, "max": 100000},
    "3": {"name": "Telegram Members 1K", "cost_per_1k": 1000, "min": 10, "max": 100000},
    "4": {"name": "Tiktok View 1K", "cost_per_1k": 300, "min": 10, "max": 100000},
}

def generate_random_code():
    length = random.randint(5, 20)
    return ''.join(random.choices(string.ascii_letters, k=length))

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id not in users:
        users[user_id] = {
            "name": user.full_name,
            "credits": 100,
            "code": generate_random_code(),
            "is_banned": False,
            "referred_by": []
        }

    if users[user_id]["is_banned"]:
        await update.message.reply_text("❌ သင့်အကောင့်အား အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည် (Banned)။")
        return

    keyboard = [
        [InlineKeyboardButton("🛒 Free Services", callback_data="services")],
        [InlineKeyboardButton("👤 My Account / Wallet", callback_data="wallet"), InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem")],
        [InlineKeyboardButton("💳 Buy Credit (Owner)", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}")]
    ]

    if user_id == OWNER_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Owner Panel", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"မင်္ဂလာပါ {user.first_name}!\nFree Service Bot မှ ကြိုဆိုပါတယ်။\n\n🎁 Welcome Bonus: 100 Credits ထည့်ပေးထားပါသည်။",
        reply_markup=reply_markup
    )

# Callback Handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if users.get(user_id, {}).get("is_banned", False):
        await query.message.edit_text("❌ သင့်အကောင့်အား အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည် (Banned)။")
        return

    data = query.data

    if data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("🛒 Free Services", callback_data="services")],
            [InlineKeyboardButton("👤 My Account / Wallet", callback_data="wallet"), InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem")],
            [InlineKeyboardButton("💳 Buy Credit (Owner)", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}")]
        ]
        if user_id == OWNER_ID:
            keyboard.append([InlineKeyboardButton("⚙️ Owner Panel", callback_data="admin_panel")])
        await query.message.edit_text("ပင်မစာမျက်နှာ သို့ရောက်ရှိနေပါသည်:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "wallet":
        u_info = users[user_id]
        msg = (
            f"👤 **User Information**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"📛 Name: {u_info['name']}\n"
            f"🔑 Code: `{u_info['code']}`\n"
            f"💰 Credits Balance: **{u_info['credits']} Credits**\n\n"
            f"💡 *သင့် Code ကို အခြားသူများအား မျှဝေ၍ Redeem လုပ်ခိုင်းပါက ၁ ယောက်လျှင် 100 Credits ရရှိပါမည်။*"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
        await query.message.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "services":
        keyboard = []
        for s_id, s_data in services.items():
            keyboard.append([InlineKeyboardButton(f"{s_data['name']} ({s_data['cost_per_1k']} Cr)", callback_data=f"buy_{s_id}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.message.edit_text("ကျေးဇူးပြု၍ လိုအပ်သော Service ကို ရွေးချယ်ပါ:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("buy_"):
        s_id = data.split("_")[1]
        s_data = services[s_id]
        u_credits = users[user_id]["credits"]
        cost = int(s_data["cost_per_1k"])

        if u_credits < cost:
            await query.message.edit_text(
                f"❌ သင့်မှာ Credit မလုံလောက်ပါ။ လိုအပ်သော Credit: {cost}\nလက်ရှိ Credit: {u_credits}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="services")]])
            )
            return

        users[user_id]["credits"] -= cost
        await query.message.edit_text(
            f"✅ **Service အောင်မြင်စွာ ရယူပြီးပါပြီ!**\n\n"
            f"📌 Service: {s_data['name']}\n"
            f"💸 Deducted: {cost} Credits\n"
            f"💰 Remaining Credits: {users[user_id]['credits']} Credits",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="services")]])
        )

    elif data == "admin_panel" and user_id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("📢 Broadcast Post", callback_data="admin_broadcast")],
            [InlineKeyboardButton("👥 Check Users List", callback_data="admin_users")],
            [InlineKeyboardButton("🔙 Back", callback_data="main_menu")]
        ]
        await query.message.edit_text("⚙️ **Owner Control Panel**", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "admin_users" and user_id == OWNER_ID:
        msg = "👥 **Registered Users List:**\n\n"
        for uid, udata in users.items():
            status = "🚫 Banned" if udata["is_banned"] else "✅ Active"
            msg += f"• ID: `{uid}` | Name: {udata['name']}\n  Code: `{udata['code']}` | Credits: {udata['credits']} | {status}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="admin_panel")]]
        await query.message.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# Conversation: Redeem Code
async def start_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("✏️ မိတ်ဆွေ ရရှိထားသော Referral Code ကို စာရိုက်၍ ပို့ပေးပါ:")
    return REDEEM_CODE_STATE

async def process_redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code_entered = update.message.text.strip()

    target_user_id = None
    for uid, udata in users.items():
        if udata["code"] == code_entered:
            target_user_id = uid
            break

    if not target_user_id:
        await update.message.reply_text("❌ မှားယွင်းသော Code ဖြစ်ပါသည်။")
        return ConversationHandler.END

    if target_user_id == user_id:
        await update.message.reply_text("❌ မိမိကိုယ်ပိုင် Code ကို ပြန်လည် Redeem လုပ်၍ မရပါ။")
        return ConversationHandler.END

    if user_id in users[target_user_id]["referred_by"]:
        await update.message.reply_text("❌ သင်သည် ဒီ Code ကို အသုံးပြုပြီးသား ဖြစ်ပါသည်။")
        return ConversationHandler.END

    users[target_user_id]["credits"] += 100
    users[target_user_id]["referred_by"].append(user_id)

    await update.message.reply_text("✅ Code အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ! Code ပိုင်ရှင်ထံသို့ 100 Credits ထည့်ပေးလိုက်ပါပြီ။")
    
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 သင့် Referral Code အား အသုံးပြုလိုက်သဖြင့် +100 Credits ရရှိပါသည်။"
        )
    except Exception:
        pass

    return ConversationHandler.END

# Conversation: Broadcast Post
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != OWNER_ID:
        return ConversationHandler.END
    
    await query.message.edit_text("📢 User များထံ ပို့ချင်သော Post/Message ကို ပို့ပေးပါ:")
    return BROADCAST_STATE

async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return ConversationHandler.END

    success, failed = 0, 0
    for uid in users.keys():
        try:
            await update.message.copy(chat_id=uid)
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"📢 Broadcast ပြီးစီးပါပြီ။\n✅ အောင်မြင်: {success}\n❌ ကျရှုံး: {failed}")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("လုပ်ဆောင်ချက်ကို ပယ်ဖျက်လိုက်ပါပြီ။")
    return ConversationHandler.END

# Render Engine အတွက် Async Main Function ရေးသားထားခြင်း
async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    redeem_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_redeem, pattern="^redeem$")],
        states={
            REDEEM_CODE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_redeem)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_broadcast, pattern="^admin_broadcast$")],
        states={
            BROADCAST_STATE: [MessageHandler(filters.ALL & ~filters.COMMAND, process_broadcast)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(redeem_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(CallbackQueryHandler(button_handler))

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        print("Bot is running successfully...")
        # Keeps the bot running forever on Render
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        pass
