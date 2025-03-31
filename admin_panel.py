import telebot
from telebot import types
import sqlite3
import subprocess
from config import *

# Initialize database
def init_db():
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id TEXT PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, join_date TEXT)''')
    conn.commit()
    conn.close()

def save_user(user):
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, join_date) VALUES (?, ?, ?, ?, datetime("now"))',
              (str(user.id), user.username, user.first_name, user.last_name))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('bot_users.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]

def create_admin_panel(bot, chat_id):
    if str(chat_id) != AMINE_ID:
        bot.send_message(chat_id, "⛔️ 𝙔𝙤𝙪 𝙖𝙧𝙚 𝙣𝙤𝙩 𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙯𝙚𝙙!")
        return

    markup = types.InlineKeyboardMarkup()
    
    # Broadcast button
    broadcast_btn = types.InlineKeyboardButton('📢 𝘽𝙧𝙤𝙖𝙙𝙘𝙖𝙨𝙩', callback_data='admin_broadcast')
    
    # Reset limits button
    reset_btn = types.InlineKeyboardButton('🔄 𝙍𝙚𝙨𝙚𝙩 𝙇𝙞𝙢𝙞𝙩𝙨', callback_data='admin_reset_limits')
    
    # Delete users button
    delete_btn = types.InlineKeyboardButton('🗑 𝘿𝙚𝙡𝙚𝙩𝙚 𝘼𝙡𝙡 𝙐𝙨𝙚𝙧𝙨', callback_data='admin_delete_users')
    
    # Statistics button
    stats_btn = types.InlineKeyboardButton('📊 𝙎𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨', callback_data='admin_stats')

    markup.add(broadcast_btn)
    markup.add(reset_btn, delete_btn)
    markup.add(stats_btn)

    bot.send_message(
        chat_id,
        "👑 𝘼𝙙𝙢𝙞𝙣 𝙋𝙖𝙣𝙚𝙡\n\n"
        "𝙎𝙚𝙡𝙚𝙘𝙩 𝙖𝙣 𝙤𝙥𝙩𝙞𝙤𝙣:",
        reply_markup=markup
    )

def handle_admin_callback(bot, call):
    if str(call.message.chat.id) != AMINE_ID:
        bot.answer_callback_query(call.id, "⛔️ 𝙔𝙤𝙪 𝙖𝙧𝙚 𝙣𝙤𝙩 𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙯𝙚𝙙!")
        return

    action = call.data.replace('admin_', '')
    
    if action == 'broadcast':
        bot.send_message(call.message.chat.id, "📢 𝙎𝙚𝙣𝙙 𝙢𝙚 𝙩𝙝𝙚 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙩𝙤 𝙗𝙧𝙤𝙖𝙙𝙘𝙖𝙨𝙩:")
        bot.register_next_step_handler(call.message, process_broadcast)
    
    elif action == 'reset_limits':
        reset_all_limits(bot, call.message.chat.id)
    
    elif action == 'delete_users':
        delete_all_users(bot, call.message.chat.id)
    
    elif action == 'stats':
        show_statistics(bot, call.message.chat.id)

def process_broadcast(message):
    users = get_all_users()
    success = 0
    failed = 0
    
    status_msg = bot.send_message(message.chat.id, "📤 𝘽𝙧𝙤𝙖𝙙𝙘𝙖𝙨𝙩𝙞𝙣𝙜...")
    
    for user_id in users:
        try:
            bot.send_message(user_id, message.text, parse_mode='HTML')
            success += 1
        except:
            failed += 1
        
        # Update status every 10 users
        if (success + failed) % 10 == 0:
            bot.edit_message_text(
                f"📤 𝘽𝙧𝙤𝙖𝙙𝙘𝙖𝙨𝙩𝙞𝙣𝙜...\n"
                f"✅ 𝙎𝙪𝙘𝙘𝙚𝙨𝙨: {success}\n"
                f"❌ 𝙁𝙖𝙞𝙡𝙚𝙙: {failed}",
                message.chat.id,
                status_msg.message_id
            )
    
    bot.edit_message_text(
        f"📢 𝘽𝙧𝙤𝙖𝙙𝙘𝙖𝙨𝙩 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!\n\n"
        f"✅ 𝙎𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡: {success}\n"
        f"❌ 𝙁𝙖𝙞𝙡𝙚𝙙: {failed}",
        message.chat.id,
        status_msg.message_id
    )

def reset_all_limits(bot, chat_id):
    global user_creation_limit
    user_creation_limit.clear()
    bot.send_message(chat_id, "🔄 𝘼𝙡𝙡 𝙪𝙨𝙚𝙧 𝙡𝙞𝙢𝙞𝙩𝙨 𝙝𝙖𝙫𝙚 𝙗𝙚𝙚𝙣 𝙧𝙚𝙨𝙚𝙩!")

def delete_all_users(bot, chat_id):
    # Delete SSH users
    try:
        # Get list of all non-root users
        result = subprocess.run(['awk', '-F:', '$3 >= 1000 && $3 != 65534 {print $1}', '/etc/passwd'], 
                             capture_output=True, text=True)
        users = result.stdout.strip().split('\n')
        
        deleted = 0
        for user in users:
            if user:  # Skip empty lines
                subprocess.run(['userdel', '-r', user])
                deleted += 1
        
        bot.send_message(
            chat_id, 
            f"🗑 𝘿𝙚𝙡𝙚𝙩𝙚𝙙 {deleted} 𝙎𝙎𝙃 𝙪𝙨𝙚𝙧𝙨!"
        )
    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙙𝙚𝙡𝙚𝙩𝙞𝙣𝙜 𝙎𝙎𝙃 𝙪𝙨𝙚𝙧𝙨: {str(e)}"
        )

def show_statistics(bot, chat_id):
    # Get total users
    total_users = len(get_all_users())
    
    # Get active SSH users
    try:
        result = subprocess.run(['who'], capture_output=True, text=True)
        active_users = len(result.stdout.strip().split('\n'))
    except:
        active_users = 0
    
    # Get system info
    try:
        # CPU usage
        cpu = subprocess.run(['top', '-bn1'], capture_output=True, text=True)
        cpu_usage = cpu.stdout.split('\n')[2].split(',')[0].split(':')[1].strip()
        
        # Memory usage
        mem = subprocess.run(['free', '-m'], capture_output=True, text=True)
        mem_total = int(mem.stdout.split('\n')[1].split()[1])
        mem_used = int(mem.stdout.split('\n')[1].split()[2])
        mem_percent = round((mem_used / mem_total) * 100, 1)
        
        bot.send_message(
            chat_id,
            f"📊 𝙎𝙮𝙨𝙩𝙚𝙢 𝙎𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨\n\n"
            f"👥 𝙏𝙤𝙩𝙖𝙡 𝙐𝙨𝙚𝙧𝙨: {total_users}\n"
            f"👤 𝘼𝙘𝙩𝙞𝙫𝙚 𝙎𝙎𝙃: {active_users}\n"
            f"💻 𝘾𝙋𝙐 𝙐𝙨𝙖𝙜𝙚: {cpu_usage}\n"
            f"💾 𝙍𝘼𝙈 𝙐𝙨𝙖𝙜𝙚: {mem_percent}%"
        )
    except Exception as e:
        bot.send_message(
            chat_id,
            f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙜𝙚𝙩𝙩𝙞𝙣𝙜 𝙨𝙮𝙨𝙩𝙚𝙢 𝙨𝙩𝙖𝙩𝙨: {str(e)}"
        )
