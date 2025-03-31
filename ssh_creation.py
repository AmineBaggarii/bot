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
    
    # Clean up old entries
    for uid in list(user_creation_limit.keys()):
        if current_time - user_creation_limit[uid]['time'] > 3600:  # 1 hour
            del user_creation_limit[uid]
    
    # Initialize user if not exists
    if user_id not in user_creation_limit:
        user_creation_limit[user_id] = {'count': 0, 'time': current_time}
    
    # Check if limit reached
    if user_creation_limit[user_id]['count'] >= 2:
        time_left = 3600 - (current_time - user_creation_limit[user_id]['time'])
        minutes_left = int(time_left / 60)
        return False, f"❌ 𝙇𝙞𝙢𝙞𝙩 𝙧𝙚𝙖𝙘𝙝𝙚𝙙. 𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 {minutes_left} 𝙢𝙞𝙣𝙪𝙩𝙚𝙨."
    
    # Increment counter and update time
    user_creation_limit[user_id]['count'] += 1
    creation_stats[service_type] = creation_stats.get(service_type, 0) + 1
    return True, None

def delete_user_after_60_minutes(ip, username):
    time.sleep(3600)  # Wait for 60 minutes
    execute_ssh_command(ip, AMINE_USERNAME, AMINE_PASSWORD, f"userdel {username}")

def process_ssh_creation(bot, message, service_type):
    if not check_subscription(message.from_user.id):
        show_join_channel_message(message.chat.id)
        return

    can_create, error_message = check_and_increment_user_limit(message.from_user.id, service_type)
    if not can_create:
        bot.reply_to(message, error_message)
        return

    bot.send_message(message.chat.id, f"𝙎𝙚𝙣𝙙 𝙐𝙨𝙚𝙧 :")
    bot.register_next_step_handler(message, lambda msg: process_username(msg, service_type))

def process_username(message, service_type):
    username = message.text
    bot.send_message(message.chat.id, f"𝙎𝙚𝙣𝙙 𝙋𝙖𝙨𝙨𝙬𝙤𝙧𝙙 :")
    bot.register_next_step_handler(message, lambda msg: process_password(msg, service_type, username))

def process_password(message, service_type, username):
    password = message.text
    if str(message.chat.id) not in admin_access:
        with thread_lock:
            threading.Thread(target=delete_user_after_60_minutes, args=(AMINE_IP, username)).start()
    
    command = f"add_new_user {username} {password} 30 30 n n n"
    logging.info(f"Executing command: {command}")
    
    output = execute_ssh_command(AMINE_IP, AMINE_USERNAME, AMINE_PASSWORD, command)
    logging.info(f"Command output: {output}")
    
    creation_stats[service_type] = creation_stats.get(service_type, 0) + 1
    
    if service_type == "Cloudflare":
        bot.send_message(message.chat.id, f"𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙧𝙚𝙖𝙩𝙚𝙙 ;)\n\n"
                                          f"• 𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚 𝘿𝙤𝙢𝙖𝙞𝙣 : <code>cf.aminebaggari.com</code>\n\n"
                                          f"• 𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚 𝙐𝙨𝙚𝙧 : <code>{username}</code>\n\n"
                                          f"• 𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚 𝙋𝙖𝙨𝙨 : <code>{password}</code>\n\n"
                                          f"• 𝙇𝙤𝙜𝙞𝙣𝙨 : 1\n\n"
                                          f"• 𝙀𝙭𝙥𝙞𝙧𝙖𝙩𝙞𝙤𝙣 : 3 𝙃𝙤𝙪𝙧𝙨\n\n"
                                          f"• 𝙏𝙤 𝙐𝙨𝙚 𝙊𝙣 𝙃𝙏𝙏𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 : <code>cf.aminebaggari.com:80@{username}:{password}</code>",
                                          parse_mode='HTML')
    elif service_type == "Cloudfront":
        bot.send_message(message.chat.id, f"𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙧𝙚𝙖𝙩𝙚𝙙 ;)\n\n"
                                          f"• 𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩 𝘿𝙤𝙢𝙖𝙞𝙣 : <code>d2uody9gsvyhbo.cloudfront.net</code>\n\n"
                                          f"• 𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩 𝙐𝙨𝙚𝙧 : <code>{username}</code>\n\n"
                                          f"• 𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩 𝙋𝙖𝙨𝙨 : <code>{password}</code>\n\n"
                                          f"• 𝙇𝙤𝙜𝙞𝙣𝙨 : 1\n\n"
                                          f"• 𝙀𝙭𝙥𝙞𝙧𝙖𝙩𝙞𝙤𝙣 : 3 𝙃𝙤𝙪𝙧𝙨\n\n"
                                          f"• 𝙏𝙤 𝙐𝙨𝙚 𝙊𝙣 𝙃𝙏𝙏𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 : <code>d2uody9gsvyhbo.cloudfront.net:80@{username}:{password}</code>",
                                          parse_mode='HTML')
    elif service_type == "UDP Custom":
        bot.send_message(message.chat.id, f"𝙐𝘿𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙧𝙚𝙖𝙩𝙚𝙙 ;)\n\n"
                                          f"• 𝙎𝙎𝙃 𝙄𝙋 : <code>{AMINE_IP}</code>\n\n"
                                          f"•𝙐𝘿𝙋 𝙨𝙩𝙤𝙢 𝘿𝙤𝙢𝙖𝙞𝙣: <code>ws.aminebaggari.com</code>\n\n"
                                          f"•𝙐𝘿𝙋 𝙐𝙨𝙚𝙧 : <code>{username}</code>\n\n"
                                          f"• 𝙐𝘿𝙋 𝙋𝙖𝙨𝙨 : <code>{password}</code>\n\n"
                                          f"• 𝙐𝙙𝙬 𝙋𝙤𝙧𝙩: 7100, 7200, 7300 (𝙁𝙤𝙧 𝙑𝙤𝙄𝙋)\n\n"
                                          f"• 𝙇𝙤𝙜𝙞𝙣𝙨 : 1\n\n"
                                          f"• 𝙀𝙭𝙥𝙞𝙧𝙖𝙩𝙞𝙤𝙣 : 3 𝙃𝙤𝙪𝙧𝙨\n\n"
                                          f"• 𝙏𝙤 𝙐𝙨𝙚 𝙊𝙣 𝙃𝙏𝙏𝙋 𝘾𝙪𝙨𝙩𝙤𝙢 : <code>ws.aminebaggari.com:1-36712@{username}:{password}</code>",
                                          parse_mode='HTML')
    elif service_type == "SlowDNS":
        bot.send_message(message.chat.id, f"𝙎𝙇𝙊𝙒𝘿𝙉𝙎 𝘼𝙘𝙘𝙤𝙪𝙣𝙩 𝘾𝙧𝙚𝙖𝙩𝙚𝙙 ;)\n\n"
                                          f"• 𝙎𝙎𝙃 𝙄𝙋 : <code>{AMINE_IP}</code>\n\n"
                                          f"• 𝙎𝙡𝙤𝙬𝘿𝙉𝙎 𝙉𝙖𝙢𝙚 𝙎𝙚𝙧𝙫𝙚𝙧 (𝙉𝙎) : <code>slowdns.aminebaggari.com</code>\n\n"
                                          f"• 𝙎𝙡𝙤𝙬𝘿𝙉𝙎 𝙐𝙨𝙚𝙧: <code>{username}</code>\n"
                                          f"• 𝙎𝙡𝙤𝙬𝘿𝙉𝙎 𝙋𝙖𝙨𝙨: <code>{password}</code>\n"
                                          f"• 𝙋𝙪𝙗𝙡𝙞𝙘 𝙆𝙚𝙮 : <code>9dbbfb7374360504a22e71b8ffda2c9c3c8ee62283d171fef9d881bd6b51b605</code>\n\n"
                                          f"• 𝙀𝙭𝙥𝙞𝙧𝙖𝙩𝙞𝙤𝙣 : 3 𝙃𝙤𝙪𝙧𝙨\n\n"
                                          f"• 𝘽𝙖𝙣𝙙𝙬𝙞𝙙𝙩𝙝: 𝙐𝙣𝙢𝙚𝙩𝙚𝙧𝙚𝙙\n\n"
                                          f"• 𝙐𝙙𝙥𝙜𝙬 𝙋𝙤𝙧𝙩: 7100, 7200, 7300 (𝙁𝙤𝙧 𝙑𝙤𝙄𝙋)",
                                          parse_mode='HTML')
    elif service_type == "SSL Direct":
        bot.send_message(message.chat.id, f"𝗦𝗦𝗟 𝗗𝗶𝗿𝗲𝗰𝘁 𝗔𝗰𝗰𝗼𝘂𝙣𝘁 𝗖𝗿𝗲𝗮𝘁𝗲𝗱 ;)\n\n"
                                          f"• 𝙎𝙎𝙇 𝙄𝙋 : <code>64.226.120.120</code>\n\n"
                                          f"• 𝙎𝙎𝙇 𝘿𝙊𝙈𝘼𝙄𝙉 : <code>ws.aminebaggari.com</code>\n\n"
                                          f"• 𝙎𝙎𝙇 𝙐𝙨𝙚𝙧: <code>{username}</code>\n\n"
                                          f"• 𝙎𝙎𝙇 𝙋𝙖𝙨𝙨: <code>{password}</code>\n\n"
                                          f"• 𝙀𝙭𝙥𝙞𝙧𝙖𝙩𝙞𝙤𝙣 : 3 𝙃𝙤𝙪𝙧𝙨\n\n"
                                          f"•  𝙎𝙎𝙃 𝙎𝙎𝙇 / 𝙏𝙻𝙎 : <code>64.226.120.120:443@{username}:{password}</code>",
                                          parse_mode='HTML')
