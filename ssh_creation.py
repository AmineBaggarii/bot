import telebot
import threading
import time
import logging
from telebot import types
from config import *
from utils import execute_ssh_command

# Global variables
user_creation_limit = {}
admin_access = {}
user_data = {}
blocked_users = set()
creation_stats = {}

thread_lock = threading.Lock()

def create_ssh_menu(bot, chat_id):
    markup = types.InlineKeyboardMarkup()
    cloudflare_btn = types.InlineKeyboardButton('☁️ 𝘾𝙧𝙚𝙖𝙩𝙚 𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚', callback_data='add_user_ssh')
    cloudfront_btn = types.InlineKeyboardButton('🌩 𝘾𝙧𝙚𝙖𝙩𝙚 𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩', callback_data='add_user_cloudfront')
    udp_btn = types.InlineKeyboardButton('🔌 𝘾𝙧𝙚𝙖𝙩𝙚 𝙐𝘿𝙋 𝘾𝙪𝙨𝙩𝙤𝙢', callback_data='add_user_udp')
    slowdns_btn = types.InlineKeyboardButton('🐌 𝘾𝙧𝙚𝙖𝙩𝙚 𝙎𝙡𝙤𝙬𝘿𝙉𝙎', callback_data='add_user_slowdns')
    ssl_btn = types.InlineKeyboardButton('🔒 𝘾𝙧𝙚𝙖𝙩𝙚 𝙎𝙎𝙇 𝘿𝙞𝙧𝙚𝙘𝙩', callback_data='add_user_ssl_direct')
    back_btn = types.InlineKeyboardButton('↩️ 𝘽𝙖𝙘𝙠', callback_data='back_to_menu')
    
    markup.add(cloudflare_btn, cloudfront_btn)
    markup.add(udp_btn, slowdns_btn)
    markup.add(ssl_btn)
    markup.add(back_btn)
    
    bot.send_message(
        chat_id,
        "🔐 𝙎𝙎𝙃 𝘾𝙧𝙚𝙖𝙩𝙞𝙤𝙣 𝙈𝙚𝙣𝙪:\n\n"
        "𝙎𝙚𝙡𝙚𝙘𝙩 𝙩𝙝𝙚 𝙩𝙮𝙥𝙚 𝙤𝙛 𝙎𝙎𝙃 𝙩𝙤 𝙘𝙧𝙚𝙖𝙩𝙚:",
        reply_markup=markup
    )

def check_and_increment_user_limit(user_id, service_type):
    current_time = time.time()
    
    # Initialize service stats if not exists
    if user_id not in user_creation_limit:
        user_creation_limit[user_id] = {
            'time': current_time,
            'services': {}
        }
    
    # Initialize service counter if not exists
    if service_type not in user_creation_limit[user_id]['services']:
        user_creation_limit[user_id]['services'][service_type] = 0
    
    # Check if 2 days have passed since last reset
    if current_time - user_creation_limit[user_id]['time'] > 172800:  # 2 days in seconds
        user_creation_limit[user_id] = {
            'time': current_time,
            'services': {service_type: 0}
        }
    
    # Check if limit reached for this service
    if user_creation_limit[user_id]['services'][service_type] >= 6:
        time_left = 172800 - (current_time - user_creation_limit[user_id]['time'])
        days_left = int(time_left / 86400)
        hours_left = int((time_left % 86400) / 3600)
        minutes_left = int((time_left % 3600) / 60)
        
        time_msg = ""
        if days_left > 0:
            time_msg += f"{days_left} 𝙙𝙖𝙮𝙨 "
        if hours_left > 0:
            time_msg += f"{hours_left} 𝙝𝙤𝙪𝙧𝙨 "
        if minutes_left > 0:
            time_msg += f"{minutes_left} 𝙢𝙞𝙣𝙪𝙩𝙚𝙨"
            
        return False, f"""❌ 𝙇𝙞𝙢𝙞𝙩 𝙧𝙚𝙖𝙘𝙝𝙚𝙙 𝙛𝙤𝙧 {service_type}!

• 𝙈𝙖𝙭 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨: 6 𝙥𝙚𝙧 𝙨𝙚𝙧𝙫𝙞𝙘𝙚
• 𝙔𝙤𝙪𝙧 𝙪𝙨𝙖𝙜𝙚: {user_creation_limit[user_id]['services'][service_type]}/6
• 𝙍𝙚𝙨𝙚𝙩 𝙞𝙣: {time_msg}"""
    
    # Increment counter
    user_creation_limit[user_id]['services'][service_type] += 1
    creation_stats[service_type] = creation_stats.get(service_type, 0) + 1
    return True, None

def delete_user_after_4_hours(ip, username):
    time.sleep(14400)  # Wait for 4 hours
    execute_ssh_command(ip, AMINE_USERNAME, AMINE_PASSWORD, f"userdel {username}")

def process_ssh_creation(bot, message, service_type):
    if not check_subscription(message.chat.id):
        show_join_channel_message(message.chat.id)
        return

    can_create, error_message = check_and_increment_user_limit(message.from_user.id, service_type)
    if not can_create:
        bot.reply_to(message, error_message)
        return

    remaining = 6 - user_creation_limit.get(message.from_user.id, {}).get('services', {}).get(service_type, 0)
    bot.send_message(
        message.chat.id,
        f"""📝 𝙎𝙚𝙣𝙙 𝙐𝙨𝙚𝙧𝙣𝙖𝙢𝙚:

• 𝙎𝙚𝙧𝙫𝙞𝙘𝙚: {service_type}
• 𝙍𝙚𝙢𝙖𝙞𝙣𝙞𝙣𝙜: {remaining}/6 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨"""
    )
    bot.register_next_step_handler(message, lambda msg: process_username(msg, service_type))

def process_username(message, service_type):
    username = message.text.strip()
    
    # Validate username
    if not username or len(username) < 3 or len(username) > 32 or ' ' in username:
        bot.reply_to(message, "❌ Invalid username. Username must be 3-32 characters long and contain no spaces.")
        return
    
    # Check if username exists
    check_cmd = f"id {username} >/dev/null 2>&1"
    if execute_ssh_command(AMINE_IP, AMINE_USERNAME, AMINE_PASSWORD, check_cmd) == 0:
        bot.reply_to(message, "❌ Username already exists. Please choose another one.")
        return
        
    bot.send_message(message.chat.id, f"𝙎𝙚𝙣𝙙 𝙋𝙖𝙨𝙨𝙬𝙤𝙧𝙙 :")
    bot.register_next_step_handler(message, lambda msg: process_password(msg, service_type, username))

def process_password(message, service_type, username):
    password = message.text.strip()
    
    # Validate password
    if not password or len(password) < 6 or len(password) > 32 or ' ' in password:
        bot.reply_to(message, "❌ Invalid password. Password must be 6-32 characters long and contain no spaces.")
        return
    
    if str(message.chat.id) not in admin_access:
        with thread_lock:
            threading.Thread(target=delete_user_after_4_hours, args=(AMINE_IP, username)).start()
    
    command = f"add_new_user {username} {password} 30 30 n n n"
    logging.info(f"Executing command: {command}")
    
    try:
        output = execute_ssh_command(AMINE_IP, AMINE_USERNAME, AMINE_PASSWORD, command)
        if "error" in output.lower() or "failed" in output.lower():
            bot.reply_to(message, f"❌ Failed to create account: {output}")
            return
            
        logging.info(f"Command output: {output}")
        
        # Update message template to show 4 hours expiration
        if service_type == "Cloudflare":
            bot.send_message(message.chat.id, f"""𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙧𝙚𝙖𝙩𝙚𝙙 ✅

• 𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚 𝘿𝙤𝙢𝙖𝙞𝙣 : <code>cf.aminebaggari.com</code>
• 𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚 𝙐𝙨𝙚𝙧 : <code>{username}</code>
• 𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚 𝙋𝙖𝙨𝙨 : <code>{password}</code>
• 𝙇𝙤𝙜𝙞𝙣𝙨 : 1
• 𝙀𝙭𝙥𝙞𝙧𝙖𝙩𝙞𝙤𝙣 : 4 𝙃𝙤𝙪𝙧𝙨
• 𝙏𝙤 𝙐𝙨𝙚 𝙊𝙣 𝙃𝙏𝙏𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 : <code>cf.aminebaggari.com:80@{username}:{password}</code>""",
                parse_mode='HTML')
        elif service_type == "Cloudfront":
            bot.send_message(message.chat.id, f"""𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙧𝙚𝙖𝙩𝙚𝙙 ✅

• 𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩 𝘿𝙤𝙢𝙖𝙞𝙣 : <code>d2uody9gsvyhbo.cloudfront.net</code>
• 𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩 𝙐𝙨𝙚𝙧 : <code>{username}</code>
• 𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩 𝙋𝙖𝙨𝙨 : <code>{password}</code>
• 𝙇𝙤𝙜𝙞𝙣𝙨 : 1
• 𝙀𝙭𝙥𝙞𝙧𝙖𝙩𝙞𝙤𝙣 : 4 𝙃𝙤𝙪𝙧𝙨
• 𝙏𝙤 𝙐𝙨𝙚 𝙊𝙣 𝙃𝙏𝙏𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 : <code>d2uody9gsvyhbo.cloudfront.net:80@{username}:{password}</code>""",
                parse_mode='HTML')
        elif service_type == "UDP Custom":
            bot.send_message(message.chat.id, f"""𝙐𝘿𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙧𝙚𝙖𝙩𝙚𝙙 ✅

• 𝙎𝙎𝙃 𝙄𝙋 : <code>{AMINE_IP}</code>
• 𝙐𝘿𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 𝘿𝙤𝙢𝙖𝙞𝙣 : <code>ws.aminebaggari.com</code>
• 𝙐𝘿𝙋 𝙐𝙨𝙚𝙧 : <code>{username}</code>
• 𝙐𝘿𝙋 𝙋𝙖𝙨𝙨 : <code>{password}</code>
• 𝙐𝘿𝙋 𝙋𝙤𝙧𝙩𝙨 : <code>7100, 7200, 7300</code> (𝙁𝙤𝙧 𝙑𝙤𝙸𝙋)
• 𝙇𝙤𝙜𝙞𝙣𝙨 : 1
• 𝙀𝙭𝙥𝙞𝙧𝙖𝙩𝙞𝙤𝙣 : 4 𝙃𝙤𝙪𝙧𝙨
• 𝙏𝙤 𝙐𝙨𝙚 𝙊𝙣 𝙃𝙏𝙏𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 : <code>ws.aminebaggari.com:80@{username}:{password}</code>""",
                parse_mode='HTML')
        elif service_type == "SlowDNS":
            bot.send_message(message.chat.id, f"""𝙎𝙡𝙤𝙬𝘿𝙉𝙎 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙧𝙚𝙖𝙩𝙚𝙙 ✅

• 𝙎𝙎𝙃 𝙄𝙋 : <code>{AMINE_IP}</code>
• 𝙎𝙡𝙤𝙬𝘿𝙉𝙎 𝘿𝙤𝙢𝙖𝙞𝙣 : <code>dns.aminebaggari.com</code>
• 𝙎𝙡𝙤𝙬𝘿𝙉𝙎 𝙐𝙨𝙚𝙧 : <code>{username}</code>
• 𝙎𝙡𝙤𝙬𝘿𝙉𝙎 𝙋𝙖𝙨𝙨 : <code>{password}</code>
• 𝙎𝙡𝙤𝙬𝘿𝙉𝙎 𝙋𝙤𝙧𝙩 : <code>53</code>
• 𝙇𝙤𝙜𝙞𝙣𝙨 : 1
• 𝙀𝙭𝙥𝙞𝙧𝙖𝙩𝙞𝙤𝙣 : 4 𝙃𝙤𝙪𝙧𝙨
• 𝙏𝙤 𝙐𝙨𝙚 𝙊𝙣 𝙃𝙏𝙏𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 : <code>dns.aminebaggari.com:53@{username}:{password}</code>""",
                parse_mode='HTML')
        elif service_type == "SSL Direct":
            bot.send_message(message.chat.id, f"""𝙎𝙎𝙇 𝘿𝙞𝙧𝙚𝙘𝙩 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙧𝙚𝙖𝙩𝙚𝙙 ✅

• 𝙎𝙎𝙃 𝙄𝙋 : <code>{AMINE_IP}</code>
• 𝙎𝙎𝙇 𝘿𝙞𝙧𝙚𝙘𝙩 𝘿𝙤𝙢𝙖𝙞𝙣 : <code>ssl.aminebaggari.com</code>
• 𝙎𝙎𝙇 𝘿𝙞𝙧𝙚𝙘𝙩 𝙐𝙨𝙚𝙧 : <code>{username}</code>
• 𝙎𝙎𝙇 𝘿𝙞𝙧𝙚𝙘𝙩 𝙋𝙖𝙨𝙨 : <code>{password}</code>
• 𝙎𝙎𝙇 𝘿𝙞𝙧𝙚𝙘𝙩 𝙋𝙤𝙧𝙩 : <code>443</code>
• 𝙇𝙤𝙜𝙞𝙣𝙨 : 1
• 𝙀𝙭𝙥𝙞𝙧𝙖𝙩𝙞𝙤𝙣 : 4 𝙃𝙤𝙪𝙧𝙨
• 𝙏𝙤 𝙐𝙨𝙚 𝙊𝙣 𝙃𝙏𝙏𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 : <code>ssl.aminebaggari.com:443@{username}:{password}</code>""",
                parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error creating account: {str(e)}")
        bot.reply_to(message, f"❌ An error occurred while creating your account. Please try again later.")
        return
