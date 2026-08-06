import random
import string
import logging
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Logging setup
logging.basicConfig(level=logging.INFO)

# Configuration
BOT_TOKEN = "8999318803:AAE1iGnIWsAKdUa1fltCJoua3yFLSnvEqJM"
OWNER_ID = 8305397892
OWNER_USERNAME = "@Xylo_Offical"

bot = telebot.TeleBot(BOT_TOKEN)

# In-Memory Database
users = {}

services = {
    "1": {"name": "Telegram Post View Free 1K", "cost": 50},
    "2": {"name": "Telegram Reaction Free 1K", "cost": 100},
    "3": {"name": "Telegram Members 1K", "cost": 1000},
    "4": {"name": "Tiktok View 1K", "cost": 300},
}

def generate_random_code():
    length = random.randint(5, 20)
    return ''.join(random.choices(string.ascii_letters, k=length))

def get_main_keyboard(user_id):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🛒 Free Services", callback_data="services"))
    markup.row(
        InlineKeyboardButton("👤 My Account / Wallet", callback_data="wallet"),
        InlineKeyboardButton("🎁 Redeem Code", callback_data="redeem")
    )
    markup.row(InlineKeyboardButton("💳 Buy Credit (Owner)", url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}"))
    if user_id == OWNER_ID:
        markup.row(InlineKeyboardButton("⚙️ Owner Panel", callback_data="admin_panel"))
    return markup

@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    if user_id not in users:
        users[user_id] = {
            "name": name,
            "credits": 100,
            "code": generate_random_code(),
            "is_banned": False,
            "referred_by": []
        }

    if users[user_id]["is_banned"]:
        bot.reply_to(message, "❌ သင့်အကောင့်အား အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည် (Banned)။")
        return

    bot.send_message(
        message.chat.id,
        f"မင်္ဂလာပါ {name}!\nFree Service Bot မှ ကြိုဆိုပါတယ်။\n\n🎁 Welcome Bonus: 100 Credits ထည့်ပေးထားပါသည်။",
        reply_markup=get_main_keyboard(user_id)
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if users.get(user_id, {}).get("is_banned", False):
        bot.answer_callback_query(call.id, "❌ Banned Account", show_alert=True)
        return

    data = call.data

    if data == "main_menu":
        bot.edit_message_text("ပင်မစာမျက်နှာ သို့ရောက်ရှိနေပါသည်:", chat_id, call.message.message_id, reply_markup=get_main_keyboard(user_id))

    elif data == "wallet":
        u_info = users[user_id]
        msg = (
            f"👤 *User Information*\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"📛 Name: {u_info['name']}\n"
            f"🔑 Code: `{u_info['code']}`\n"
            f"💰 Credits Balance: *{u_info['credits']} Credits*\n\n"
            f"💡 *သင့် Code ကို အခြားသူများအား မျှဝေ၍ Redeem လုပ်ခိုင်းပါက ၁ ယောက်လျှင် 100 Credits ရရှိပါမည်။*"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
        bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data == "services":
        markup = InlineKeyboardMarkup()
        for s_id, s_data in services.items():
            markup.row(InlineKeyboardButton(f"{s_data['name']} ({s_data['cost']} Cr)", callback_data=f"buy_{s_id}"))
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
        bot.edit_message_text("ကျေးဇူးပြု၍ လိုအပ်သော Service ကို ရွေးချယ်ပါ:", chat_id, call.message.message_id, reply_markup=markup)

    elif data.startswith("buy_"):
        s_id = data.split("_")[1]
        s_data = services[s_id]
        cost = s_data["cost"]
        u_credits = users[user_id]["credits"]

        if u_credits < cost:
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🔙 Back", callback_data="services"))
            bot.edit_message_text(f"❌ သင့်မှာ Credit မလုံလောက်ပါ။\nလိုအပ်သော Credit: {cost}\nလက်ရှိ Credit: {u_credits}", chat_id, call.message.message_id, reply_markup=markup)
            return

        users[user_id]["credits"] -= cost
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="services"))
        bot.edit_message_text(
            f"✅ *Service အောင်မြင်စွာ ရယူပြီးပါပြီ!*\n\n📌 Service: {s_data['name']}\n💸 Deducted: {cost} Credits\n💰 Remaining: {users[user_id]['credits']} Credits",
            chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup
        )

    elif data == "redeem":
        msg = bot.send_message(chat_id, "✏️ မိတ်ဆွေ ရရှိထားသော Referral Code ကို စာရိုက်၍ ပို့ပေးပါ:")
        bot.register_next_step_handler(msg, process_redeem_code)

    elif data == "admin_panel" and user_id == OWNER_ID:
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("📢 Broadcast Post", callback_data="admin_broadcast"))
        markup.row(InlineKeyboardButton("👥 Check Users List", callback_data="admin_users"))
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="main_menu"))
        bot.edit_message_text("⚙️ *Owner Control Panel*", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data == "admin_users" and user_id == OWNER_ID:
        msg = "👥 *Registered Users List:*\n\n"
        for uid, udata in users.items():
            status = "🚫 Banned" if udata["is_banned"] else "✅ Active"
            msg += f"• ID: `{uid}` | Name: {udata['name']}\n  Code: `{udata['code']}` | Credits: {udata['credits']} | {status}\n\n"
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔙 Back", callback_data="admin_panel"))
        bot.edit_message_text(msg, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data == "admin_broadcast" and user_id == OWNER_ID:
        msg = bot.send_message(chat_id, "📢 User များထံ ပို့ချင်သော Post/Message ကို ပို့ပေးပါ:")
        bot.register_next_step_handler(msg, process_broadcast_msg)

def process_redeem_code(message):
    user_id = message.from_user.id
    code_entered = message.text.strip()

    target_user_id = None
    for uid, udata in users.items():
        if udata["code"] == code_entered:
            target_user_id = uid
            break

    if not target_user_id:
        bot.reply_to(message, "❌ မှားယွင်းသော Code ဖြစ်ပါသည်။")
        return

    if target_user_id == user_id:
        bot.reply_to(message, "❌ မိမိကိုယ်ပိုင် Code ကို ပြန်လည် Redeem လုပ်၍ မရပါ။")
        return

    if user_id in users[target_user_id]["referred_by"]:
        bot.reply_to(message, "❌ သင်သည် ဒီ Code ကို အသုံးပြုပြီးသား ဖြစ်ပါသည်။")
        return

    users[target_user_id]["credits"] += 100
    users[target_user_id]["referred_by"].append(user_id)
    bot.reply_to(message, "✅ Code အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ! Code ပိုင်ရှင်ထံသို့ 100 Credits ထည့်ပေးလိုက်ပါပြီ။")

    try:
        bot.send_message(target_user_id, "🎉 သင့် Referral Code အအား အသုံးပြုလိုက်သဖြင့် +100 Credits ရရှိပါသည်။")
    except Exception:
        pass

def process_broadcast_msg(message):
    if message.from_user.id != OWNER_ID:
        return

    success, failed = 0, 0
    for uid in users.keys():
        try:
            bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
        except Exception:
            failed += 1

    bot.reply_to(message, f"📢 Broadcast ပြီးစီးပါပြီ။\n✅ အောင်မြင်: {success}\n❌ ကျရှုံး: {failed}")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True)
