import os
import random
import string
import logging
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

# States for Conversations
BROADCAST_STATE = 1
ADD_CREDIT_USER = 2
ADD_CREDIT_AMOUNT = 3
REDEEM_CODE_STATE = 4

# In-Memory Database (Render Free Tier တွင် SQLite ထက် Simple Data Structures သုံးခြင်းက File Loss ဖြစ်တာမှလွဲ၍ ပိုမိုမြန်ဆန်ပါသည်)
# စာရင်းများကို persistent ဖြစ်ချင်ပါက SQLite database အဖြစ် ပြောင်းလဲအသုံးပြုနိုင်ပါသည်။
users = {} 
# users Structure: 
# {
#   user_id: {
#       "name": str, 
#       "credits": int, 
#       "code": str, 
#       "is_banned": bool, 
#       "referred_by": list
#   }
# }

services = {
    "1": {"name": "Telegram Post View Free 1K", "cost_per_1k": 50, "min": 100, "max": 100000},
    "2": {"name": "Telegram Reaction Free 1K", "cost_per_1k": 100, "min": 10, "max": 100000},
    "3": {"name": "Telegram Members 1K", "cost_per_1k": 1000, "min": 10, "max": 100000},
    "4": {"name": "Tiktok View 1K", "cost_per_1k": 300, "min": 10, "max": 100000},
}

# Helper Function: Random Code Generation (5 to 20 English letters)
def generate_random_code():
    length = random.randint(5, 20)
    return ''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=length))

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id not in users:
        users[user_id] = {
            "name": user.full_name,
            "credits": 100,  # Auto Start Bonus 100 Credits
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

# Callback Query Handler
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
            f"🔑 Referral Code: `{u_info['code']}`\n"
            f"💰 Credits Balance: **{u_info['credits']} Credits**\n\n"
            f"💡 *သင့် Code ကို အခြားသူများအား မျှဝေ၍ Redeem လုပ်ခိုင်းပါက ၁ ယောက်လျှင် 100 Credits ရရှိပါမည်။*"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="main_menu")]]
        await query.message.edit_text(msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "services":
        keyboard = []
        for s_id, s_data in services.items():
            keyboard.append([InlineKeyboardButton(f"{s_data['name']} ({s_data['cost_per_1k']} Cr/1K)", callback_data=f"buy_{s_id}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
        await query.message.edit_text("ကျေးဇူးပြု၍ လိုအပ်သော Service ကို ရွေးချယ်ပါ:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("buy_"):
        s_id = data.split("_")[1]
        s_data = services[s_id]
        u_credits = users[user_id]["credits"]

        if u_credits < (s_data["cost_per_1k"] / 1000 * s_data["min"]):
            await query.message.edit_text(
                f"❌ သင့်မှာ Credit မလုံလောက်ပါ။ အနည်းဆုံး ရယူရန် Credit {int(s_data['cost_per_1k'] / 1000 * s_data['min'])} လိုအပ်ပါသည်။\n\n"
                f"လက်ရှိ Credit: {u_credits}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="services")]])
            )
            return

        # Auto Deduct Credit (1K unit calculation example)
        cost = int(s_data["cost_per_1k"])
        if u_credits >= cost:
            users[user_id]["credits"] -= cost
            await query.message.edit_text(
                f"✅ **Service အောင်မြင်စွာ ရယူပြီးပါပြီ!**\n\n"
                f"📌 Service: {s_data['name']}\n"
                f"💸 Deducted: {cost} Credits\n"
                f"💰 Remaining Credits: {users[user_id]['credits']} Credits",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="services")]])
            )
        else:
            await query.message.edit_text("❌ Credit မလုံလောက်ပါ။", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="services")]]))

    # Admin Panel Handlers
    elif data == "admin_panel" and user_id == OWNER_ID:
        keyboard = [
            [InlineKeyboardButton("📢 Broadcast Post", callback_data="admin_broadcast")],
            [InlineKeyboardButton("➕ Add/Set Credit", callback_data="admin_add_credit")],
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

# --- Conversation: Redeem Code ---
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
        await update.message.reply_text("❌ မှားယွင်းသော Code ဖြစ်ပါသည်။ ကျေးဇူးပြု၍ ပြန်လည် စစ်ဆေးပါ။")
        return ConversationHandler.END

    if target_user_id == user_id:
        await update.message.reply_text("❌ မိမိကိုယ်ပိုင် Code ကို ပြန်လည် Redeem လုပ်၍ မရပါ။")
        return ConversationHandler.END

    if user_id in users[target_user_id]["referred_by"]:
        await update.message.reply_text("❌ သင်သည် ဒီ Code ကို တစ်ကြိမ် အသုံးပြုပြီးသား ဖြစ်ပါသည်။")
        return ConversationHandler.END

    # Award 100 Credits to Code Owner
    users[target_user_id]["credits"] += 100
    users[target_user_id]["referred_by"].append(user_id)

    await update.message.reply_text(f"✅ Code အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ! Code ပိုင်ရှင်ထံသို့ 100 Credits ထည့်ပေးလိုက်ပါပြီ။")
    
    # Notify Code Owner
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 သင့် Referral Code အား လူတစ်ယောက်မှ အသုံးပြုလိုက်သဖြင့် +100 Credits ရရှိပါသည်။"
        )
    except Exception:
        pass

    return ConversationHandler.END

# --- Conversation: Broadcast Post (Owner Only) ---
async def start_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != OWNER_ID:
        return ConversationHandler.END
    
    await query.message.edit_text("📢 User များထံ ပို့ချင်သော Post/Message/Image ကို ပို့ပေးပါ:")
    return BROADCAST_STATE

async def process_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return ConversationHandler.END

    success = 0
    failed = 0
    for uid in users.keys():
        try:
            await update.message.copy(chat_id=uid)
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"📢 Broadcast ပြီးစီးပါပြီ။\n✅ အောင်မြင်: {success}\n❌ ကျရှုံး: {failed}")
    return ConversationHandler.END

# Cancel Conversation
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("လုပ်ဆောင်ချက်ကို ပယ်ဖျက်လိုက်ပါပြီ။")
    return ConversationHandler.END
def main():
    # Application Build
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers များ ထည့်သွင်းခြင်း
    app.add_handler(CommandHandler("start", start))
    app.add_handler(redeem_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(CallbackQueryHandler(button_handler))

    # Bot စတင်ပွဲထုတ်ခြင်း
    print("Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
