import telebot
import paramiko
import threading
import time
import logging
import psutil
import subprocess
import platform
import requests
import json
from logging import getLogger, Formatter, FileHandler, StreamHandler, DEBUG

TOKEN = '6768147175:AAH9-IT8GiLtS_ieezhpMu4fo_5okQqpxvw'
AMINE_ID = '6455079270'

# Cloudflare configuration
CLOUDFLARE_API_TOKEN = "X5v0gNw8F2RPwOSC2RXJnLSJubgxWhFoerciH0jY"
CLOUDFLARE_ZONE_ID = "c619be390559750d014eb4905ac57838"
DOMAIN = "aminebaggari.com"

# Add admin management
ADMIN_IDS = {AMINE_ID}  # Using set for faster lookups
OWNER_ID = AMINE_ID     # Original owner can't be removed

bot = telebot.TeleBot(TOKEN)

logging.basicConfig(filename='bot.log', level=logging.ERROR)

AMINE_IP = '64.226.120.120'
AMINE_USERNAME = 'root'
AMINE_PASSWORD = '010119966'

user_creation_limit = {}
admin_access = {}
user_data = {}
blocked_users = set()

MAX_CONCURRENT_THREADS = 10

thread_lock = threading.Lock()

service_status = {
    'Cloudflare': True,
    'Cloudfront': False,
    'UDP Custom': True,
    'SlowDNS': True,
    'SSL Direct': True
}

creation_stats = {
    'Cloudflare': 0,
    'Cloudfront': 0,
    'UDP Custom': 0,
    'SlowDNS': 0,
    'SSL Direct': 0
}

CHANNEL_USERNAME = "RT_CFG"  # Your channel username without @

# Store user domain counts and creation times
user_domain_counts = {}
domain_creation_times = {}

def can_create_domain(user_id):
    if user_id not in user_domain_counts:
        user_domain_counts[user_id] = 0
    return user_domain_counts[user_id] < 15

def execute_ssh_command(ip, username, password, command):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=ip, username=username, password=password)
    ssh_client.exec_command(command)
    ssh_client.close()

def execute_terminal_command(command):
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )
        stdout, stderr = process.communicate(timeout=30)
        
        if process.returncode == 0:
            return f"✅ Command executed successfully:\n\n{stdout}"
        else:
            return f"❌ Command failed:\n\n{stderr}"
    except subprocess.TimeoutExpired:
        return "❌ Command timed out after 30 seconds"
    except Exception as e:
        return f"❌ Error executing command: {str(e)}"

def check_subscription(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return False

def show_join_channel_message(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    channel_button = telebot.types.InlineKeyboardButton('📢 𝙅𝙤𝙞𝙣 𝘾𝙝𝙖𝙣𝙣𝙚𝙡', url=f'https://t.me/{CHANNEL_USERNAME}')
    markup.row(channel_button)
    
    msg = bot.send_message(
        chat_id,
        "🔔| 𝙅𝙤𝙞𝙣 𝙈𝙮 𝘾𝙝𝙖𝙣𝙣𝙚𝙡 𝙁𝙤𝙧 𝘽𝙤𝙩 𝙐𝙥𝙙𝙖𝙩𝙚𝙨\n\n"
        "🌟| @RT_CFG\n\n"
        "⏳ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙮𝙤𝙪𝙧 𝙨𝙪𝙗𝙨𝙘𝙧𝙞𝙥𝙩𝙞𝙤𝙣...",
        reply_markup=markup
    )
    
    # Start real-time checking in a separate thread
    threading.Thread(target=check_subscription_realtime, args=(chat_id, msg.chat.id, msg.message_id)).start()
    return msg

@bot.message_handler(commands=['start'])
def start(message):
    if not check_subscription(message.from_user.id):
        show_join_channel_message(message.chat.id)
        return

    show_main_menu(message.chat.id)

def check_subscription_realtime(chat_id, user_id, msg_id):
    check_count = 0
    dots = 1
    while check_count < 60:  # Check for 60 seconds max
        if check_subscription(user_id):
            try:
                # Delete the join channel message
                bot.delete_message(chat_id, msg_id)
                # Show the main menu
                show_main_menu(chat_id)
                break
            except Exception as e:
                print(f"Error in subscription check: {e}")
                break
        
        # Update checking message every 2 seconds with animated dots
        if check_count % 2 == 0:
            try:
                dots = (dots % 3) + 1
                bot.edit_message_text(
                    "🔔| 𝙅𝙤𝙞𝙣 𝙈𝙮 𝘾𝙝𝙖𝙣𝙣𝙚𝙡 𝙁𝙤𝙧 𝘽𝙤𝙩 𝙐𝙥𝙙𝙖𝙩𝙚𝙨\n\n"
                    "🌟| @RT_CFG\n\n"
                    f"⏳ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙮𝙤𝙪𝙧 𝙨𝙪𝙗𝙨𝙘𝙧𝙞𝙥𝙩𝙞𝙤𝙣{'.' * dots}",
                    chat_id,
                    msg_id,
                    reply_markup=telebot.types.InlineKeyboardMarkup().row(
                        telebot.types.InlineKeyboardButton('📢 𝙅𝙤𝙞𝙣 𝘾𝙝𝙖𝙣𝙣𝙚𝙡', url=f'https://t.me/{CHANNEL_USERNAME}')
                    )
                )
            except:
                break
                
        time.sleep(1)
        check_count += 1

def show_main_menu(chat_id):
    markup = telebot.types.InlineKeyboardMarkup()
    item1 = telebot.types.InlineKeyboardButton('𝘾𝙧𝙚𝙖𝙩𝙚 𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚', callback_data='add_user_ssh')
    item2 = telebot.types.InlineKeyboardButton('𝘾𝙧𝙚𝙖𝙩𝙚 𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩', callback_data='add_user_cloudfront')
    item3 = telebot.types.InlineKeyboardButton('𝘾𝙧𝙚𝙖𝙩𝙚 𝙐𝘿𝙋 𝘾𝙪𝙨𝙩𝙤𝙢', callback_data='add_user_udp')
    item4 = telebot.types.InlineKeyboardButton('𝘾𝙧𝙚𝙖𝙩𝙚 𝙎𝙡𝙤𝙬𝘿𝙉𝙎', callback_data='add_user_slowdns')
    item5 = telebot.types.InlineKeyboardButton('𝘾𝙧𝙚𝙖𝙩𝙚 𝙎𝙎𝙇 𝘿𝙞𝙧𝙚𝙘𝙩', callback_data='add_user_ssl_direct')
    item6 = telebot.types.InlineKeyboardButton('𝘾𝙤𝙣𝙩𝙖𝙘𝙩 𝘿𝙚𝙫𝙚𝙡𝙤𝙥𝙚𝙧', url='https://t.me/aminebaggarii')
    item7 = telebot.types.InlineKeyboardButton('𝘾𝙧𝙚𝙖𝙩𝙚 𝘿𝙤𝙢𝙖𝙞𝙣', callback_data='create_domain')
    markup.add(item1, item2)
    markup.add(item3, item4)
    markup.add(item5, item7)
    markup.add(item6)
    welcome_message = ("𝙒𝙚𝙡𝙘𝙤𝙢𝙚! 𝙏𝙝𝙖𝙣𝙠 𝙮𝙤𝙪 𝙛𝙤𝙧 𝙐𝙨𝙞𝙣𝙜 𝙩𝙝𝙚 𝙁𝙧𝙚𝙚 𝙎𝙎𝙃 𝘽𝙤𝙩.\n\n"
                      "𝙏𝙤 𝙋𝙪𝙧𝙘𝙝𝙖𝙨𝙚 𝙩𝙝𝙚 𝘽𝙤𝙩, 𝙋𝙡𝙚𝙖𝙨𝙚 𝘾𝙤𝙣𝙩𝙖𝙘𝙩 @aminebaggarii. , 𝙔𝙤𝙪 𝘾𝙖𝙣 𝙘𝙧𝙚𝙖𝙩𝙚 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙 𝙐𝙨𝙚𝙧𝙨 𝘼𝙣𝙙 𝙋𝙖𝙨𝙨𝙬𝙤𝙧𝙙𝙨.")
    bot.send_message(chat_id, welcome_message, reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        return  # Only allow admins to use this command
    
    markup = telebot.types.InlineKeyboardMarkup()
    
    # First row
    reset_button = telebot.types.InlineKeyboardButton('🔄 Reset Limits', callback_data='admin_reset')
    vps_button = telebot.types.InlineKeyboardButton('🖥 VPS Health', callback_data='admin_vps_status')
    markup.row(reset_button, vps_button)
    
    # Second row
    terminal_button = telebot.types.InlineKeyboardButton('💻 Terminal', callback_data='admin_terminal')
    broadcast_button = telebot.types.InlineKeyboardButton('📢 Broadcast', callback_data='admin_broadcast')
    markup.row(terminal_button, broadcast_button)
    
    # Third row - Admin management (only for owner)
    if str(message.from_user.id) == OWNER_ID:
        admin_button = telebot.types.InlineKeyboardButton('👑 Manage Admins', callback_data='admin_manage')
        markup.row(admin_button)
    
    admin_msg = bot.send_message(
        message.chat.id,
        "🎛 *Admin Control Panel*\n"
        "-----------------\n"
        "Select an option below:",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    
    bot.pin_chat_message(message.chat.id, admin_msg.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'admin_reset')
def reset_limits(call):
    if str(call.from_user.id) != AMINE_ID:
        return
    
    user_creation_limit.clear()  # Reset all limits
    bot.answer_callback_query(call.id, "All user limits have been reset!")
    bot.edit_message_text(
        "🔄 All user limits have been reset!\nUsers can now create accounts again.",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=get_back_button()
    )

@bot.callback_query_handler(func=lambda call: call.data == 'admin_vps_status')
def send_vps_status(call):
    status = get_vps_status()
    bot.send_message(call.message.chat.id, status, parse_mode='Markdown')

def get_vps_status():
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        if memory.percent > 90 or disk.percent > 90:
            status = "🔴 Critical - Immediate action needed!"
        elif memory.percent > 70 or disk.percent > 70:
            status = "🟡 Warning - Consider cleanup"
        else:
            status = "🟢 Healthy"
            
        status_msg = f"""🖥 *VPS Health Check*
Status: {status}
Memory: {memory.percent}% used
Disk: {disk.percent}% used"""
        
        return status_msg
    except Exception as e:
        return f"Error checking VPS health: {str(e)}"

@bot.callback_query_handler(func=lambda call: call.data == 'admin_terminal')
def start_terminal_session(call):
    if str(call.from_user.id) != AMINE_ID:
        return
        
    markup = telebot.types.InlineKeyboardMarkup()
    exit_button = telebot.types.InlineKeyboardButton('❌ Exit Terminal', callback_data='exit_terminal')
    markup.row(exit_button)
    
    msg = bot.send_message(
        call.message.chat.id,
        "💻 *Terminal Session Started*\n"
        "Send commands directly in chat.\n"
        "Each message will be executed as a command.\n"
        "Type 'exit' or click button to end session.",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    
    # Store session state
    user_data[call.from_user.id] = {'terminal_session': True, 'session_msg_id': msg.message_id}

@bot.message_handler(func=lambda message: 
    str(message.from_user.id) == AMINE_ID and 
    message.from_user.id in user_data and 
    user_data[message.from_user.id].get('terminal_session', False))
def handle_terminal_input(message):
    if message.text.lower() == 'exit':
        user_data[message.from_user.id]['terminal_session'] = False
        bot.reply_to(message, "Terminal session ended.")
        return
        
    response = execute_terminal_command(message.text)
    # Split long responses into chunks
    max_length = 4000
    for i in range(0, len(response), max_length):
        chunk = response[i:i + max_length]
        bot.reply_to(message, f"```\n{chunk}\n```", parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'exit_terminal')
def exit_terminal_session(call):
    if str(call.from_user.id) != AMINE_ID:
        return
        
    if call.from_user.id in user_data:
        user_data[call.from_user.id]['terminal_session'] = False
    
    bot.edit_message_text(
        "Terminal session ended.",
        call.message.chat.id,
        call.message.message_id
    )

def check_and_increment_user_limit(user_id, service_type):
    # Admins have unlimited access
    if str(user_id) in ADMIN_IDS:
        return True
        
    if user_id not in user_creation_limit:
        user_creation_limit[user_id] = {
            'Cloudflare': 0,
            'Cloudfront': 0,
            'UDP Custom': 0,
            'SlowDNS': 0,
            'SSL Direct': 0
        }
    if user_creation_limit[user_id][service_type] >= 6:
        return False
    user_creation_limit[user_id][service_type] += 1
    return True

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == 'back_to_menu':
        show_main_menu(call.message.chat.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return
    
    if call.data == 'create_domain':
        if not can_create_domain(call.from_user.id):
            bot.send_message(call.message.chat.id, "❌ 𝙔𝙤𝙪'𝙫𝙚 𝙧𝙚𝙖𝙘𝙝𝙚𝙙 𝙩𝙝𝙚 𝙢𝙖𝙭𝙞𝙢𝙪𝙢 𝙡𝙞𝙢𝙞𝙩 𝙤𝙛 15 𝙙𝙤𝙢𝙖𝙞𝙣𝙨.")
            show_main_menu(call.message.chat.id)
            return

        show_record_type_selection(call.message)
        bot.answer_callback_query(call.id)
        #bot.delete_message(call.message.chat.id, call.message.message_id)
        return

    if call.data.startswith('dns_'):
        handle_dns_record_type(call)
        return

    if call.data.startswith('proxy_'):
        handle_proxy_selection(call)
        return
        
    # Handle other services (SSH, etc)
    if not check_subscription(call.from_user.id):
        show_join_channel_message(call.message.chat.id)
        return

    if call.data == 'add_user_ssh':
        service_type = 'Cloudflare'
    elif call.data == 'add_user_cloudfront':
        service_type = 'Cloudfront'
    elif call.data == 'add_user_udp':
        service_type = 'UDP Custom'
    elif call.data == 'add_user_slowdns':
        service_type = 'SlowDNS'
    elif call.data == 'add_user_ssl_direct':
        service_type = 'SSL Direct'
    else:
        return

    if not check_and_increment_user_limit(call.from_user.id, service_type):
        bot.send_message(call.message.chat.id, f"❌ 𝙔𝙤𝙪'𝙫𝙚 𝙧𝙚𝙖𝙘𝙝𝙚𝙙 𝙩𝙝𝙚 𝙡𝙞𝙢𝙞𝙩 𝙤𝙛 6 𝙖𝙘𝙘𝙤𝙪𝙣𝙩𝙨 𝙛𝙤𝙧 {service_type}. 𝘾𝙤𝙣𝙩𝙖𝙘𝙩 @aminebaggarii")
        return

    if not service_status.get(service_type, True):
        bot.answer_callback_query(call.id, "❌ 𝙏𝙝𝙞𝙨 𝙨𝙚𝙧𝙫𝙞𝙘𝙚 𝙞𝙨 𝙘𝙪𝙧𝙧𝙚𝙣𝙩𝙡𝙮 𝙙𝙞𝙨𝙖𝙗𝙡𝙚𝙙.")
        return

    bot.answer_callback_query(call.id)
    #bot.delete_message(call.message.chat.id, call.message.message_id)
    process_access(call.message, service_type)

def process_access(message, service_type):
    if str(message.chat.id) not in admin_access:
        bot.send_message(message.chat.id, f"𝙎𝙚𝙣𝙙 𝙐𝙨𝙚𝙧 :")
        bot.register_next_step_handler(message, lambda msg: process_username(msg, service_type))
    else:
        bot.send_message(message.chat.id, f"𝙎𝙚𝙣𝙙 𝙐𝙨𝙚𝙧 :")
        bot.register_next_step_handler(message, lambda msg: process_username(msg, service_type))

def process_username(message, service_type):
    username = message.text
    bot.send_message(message.chat.id, f"𝙎𝙚𝙣𝙙 𝙐𝙨𝙚𝙧 :")
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
                                          f"• 𝙏𝙤 ��𝙨𝙚 𝙊𝙣 𝙃𝙏𝙏𝙋 𝙪𝙨𝙩𝙤𝙢 : <code>cf.aminebaggari.com:80@{username}:{password}</code>",
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

@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, "ma3ndk madir hna wa79 rb gha rj3 /start")

def get_bot_stats():
    total_users = len(user_data)
    blocked_count = len(blocked_users)
    active_users = total_users - blocked_count
    
    stats = (
        "📊 *Bot Statistics*\n"
        f"Total Users: {total_users}\n"
        f"Active Users: {active_users}\n"
        f"Blocked Users: {blocked_count}\n\n"
        "*Account Creation Stats:*\n"
    )
    
    for service, count in creation_stats.items():
        stats += f"{service}: {count} accounts\n"
    
    return stats

def get_service_status():
    status_text = "⚙️ *Service Status*\n\n"
    for service, is_active in service_status.items():
        status = "✅ Active" if is_active else "❌ Disabled"
        status_text += f"{service}: {status}\n"
    return status_text

def handle_error(e):
    logging.error(f"An error occurred: {str(e)}")

def delete_user_after_60_minutes(ip, username):
    time.sleep(3600)  # Wait for 60 minutes (3600 seconds)
    command = f"deluser {username}"  # Replace with your actual command to delete the user
    execute_ssh_command(ip, AMINE_USERNAME, AMINE_PASSWORD, command)

def get_back_button():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton('🔙 Back', callback_data='admin_back'))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'admin_broadcast')
def start_broadcast(call):
    if str(call.from_user.id) != AMINE_ID:
        return
        
    msg = bot.send_message(
        call.message.chat.id,
        "📢 *Send the message you want to broadcast to all users*\n"
        "You can use HTML formatting:\n"
        "- `<b>bold</b>`\n"
        "- `<i>italic</i>`\n"
        "- `<code>monospace</code>`\n"
        "- `<a href='URL'>link text</a>`",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    if str(message.from_user.id) != AMINE_ID:
        return
        
    broadcast_text = message.text
    if not broadcast_text:
        bot.reply_to(message, "❌ Please provide a message to broadcast")
        return
        
    # Start broadcasting with progress updates
    total_users = len(user_data)
    sent_count = 0
    failed_count = 0
    
    progress_msg = bot.send_message(
        message.chat.id,
        "📤 Broadcasting message...\n"
        "Progress: 0%"
    )
    
    for user_id in user_data.keys():
        try:
            bot.send_message(
                user_id,
                broadcast_text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            logging.error(f"Failed to send broadcast to {user_id}: {str(e)}")
            
        # Update progress every 10 users
        if sent_count % 10 == 0:
            progress = (sent_count + failed_count) * 100 // total_users
            bot.edit_message_text(
                f"📤 Broadcasting message...\n"
                f"Progress: {progress}%\n"
                f"✅ Sent: {sent_count}\n"
                f"❌ Failed: {failed_count}",
                message.chat.id,
                progress_msg.message_id
            )
    
    # Final status update
    bot.edit_message_text(
        f"📤 Broadcast completed!\n"
        f"✅ Successfully sent: {sent_count}\n"
        f"❌ Failed: {failed_count}",
        message.chat.id,
        progress_msg.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data == 'admin_manage')
def admin_management(call):
    if str(call.from_user.id) != OWNER_ID:
        bot.answer_callback_query(call.id, "Only the owner can manage admins!")
        return
        
    markup = telebot.types.InlineKeyboardMarkup()
    add_admin = telebot.types.InlineKeyboardButton('➕ Add Admin', callback_data='admin_add')
    list_admin = telebot.types.InlineKeyboardButton('📋 List Admins', callback_data='admin_list')
    remove_admin = telebot.types.InlineKeyboardButton('➖ Remove Admin', callback_data='admin_remove')
    back = telebot.types.InlineKeyboardButton('🔙 Back', callback_data='admin_back')
    
    markup.row(add_admin, list_admin)
    markup.row(remove_admin)
    markup.row(back)
    
    bot.edit_message_text(
        "👑 *Admin Management*\n"
        "-----------------\n"
        "Select an action below:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == 'admin_add')
def add_admin_prompt(call):
    if str(call.from_user.id) != OWNER_ID:
        return
        
    msg = bot.send_message(
        call.message.chat.id,
        "👤 Send the User ID of the new admin:",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_new_admin)

def process_new_admin(message):
    if str(message.from_user.id) != OWNER_ID:
        return
        
    try:
        new_admin_id = str(message.text.strip())
        if new_admin_id in ADMIN_IDS:
            bot.reply_to(message, "❌ This user is already an admin!")
            return
            
        ADMIN_IDS.add(new_admin_id)
        bot.reply_to(
            message, 
            f"✅ Success! User ID `{new_admin_id}` is now an admin.\n"
            f"They can now use /admin command and have unlimited access.",
            parse_mode='Markdown'
        )
        
        # Notify the new admin
        try:
            bot.send_message(
                new_admin_id,
                "🎉 *Congratulations!*\n"
                "You have been promoted to admin.\n"
                "You can now use the /admin command.",
                parse_mode='Markdown'
            )
        except:
            bot.reply_to(message, "⚠️ Note: Couldn't notify the user. Make sure they have started the bot.")
            
    except ValueError:
        bot.reply_to(message, "❌ Invalid User ID! Please send a valid numeric ID.")

@bot.callback_query_handler(func=lambda call: call.data == 'admin_list')
def list_admins(call):
    if str(call.from_user.id) != OWNER_ID:
        return
        
    admin_list = "👑 *Admin List*\n\n"
    for admin_id in ADMIN_IDS:
        try:
            user = bot.get_chat(admin_id)
            username = user.username if user.username else "No username"
            name = user.first_name if user.first_name else "No name"
            admin_list += f"• ID: `{admin_id}`\n  Username: @{username}\n  Name: {name}\n"
        except:
            admin_list += f"• ID: `{admin_id}`\n  (User info unavailable)\n"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton('🔙 Back', callback_data='admin_manage'))
    
    bot.edit_message_text(
        admin_list,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data == 'admin_remove')
def remove_admin_prompt(call):
    if str(call.from_user.id) != OWNER_ID:
        return
        
    msg = bot.send_message(
        call.message.chat.id,
        "👤 Send the User ID of the admin to remove:",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, process_remove_admin)

def process_remove_admin(message):
    if str(message.from_user.id) != OWNER_ID:
        return
        
    try:
        admin_id = str(message.text.strip())
        if admin_id == OWNER_ID:
            bot.reply_to(message, "❌ You cannot remove the owner!")
            return
            
        if admin_id not in ADMIN_IDS:
            bot.reply_to(message, "❌ This user is not an admin!")
            return
            
        ADMIN_IDS.remove(admin_id)
        bot.reply_to(
            message, 
            f"✅ Success! User ID `{admin_id}` has been removed from admins.",
            parse_mode='Markdown'
        )
        
        # Notify the removed admin
        try:
            bot.send_message(
                admin_id,
                "ℹ️ *Notice*\n"
                "You have been removed from admin position.",
                parse_mode='Markdown'
            )
        except:
            pass
            
    except ValueError:
        bot.reply_to(message, "❌ Invalid User ID! Please send a valid numeric ID.")

# Cloudflare DNS Management
user_states = {}

def show_record_type_selection(message):
    if not can_create_domain(message.chat.id):
        bot.send_message(message.chat.id, "❌ 𝙔𝙤𝙪'𝙫𝙚 𝙧𝙚𝙖𝙘𝙝𝙚𝙙 𝙩𝙝𝙚 𝙢𝙖𝙭𝙞𝙢𝙪𝙢 𝙡𝙞𝙢𝙞𝙩 𝙤𝙛 15 𝙙𝙤𝙢𝙖𝙞𝙣𝙨.")
        show_main_menu(message.chat.id)
        return

    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    types = [
        ('⚡️ 𝘼 𝙍𝙚𝙘𝙤𝙧𝙙 (𝙄𝙋𝙫4)', 'dns_a'),
        ('⚡️ 𝘼𝘼𝘼𝘼 𝙍𝙚𝙘𝙤𝙧𝙙 (𝙄𝙋𝙫6)', 'dns_aaaa'),
        ('⚡️ 𝘾𝙉𝘼𝙈𝙀 𝙍𝙚𝙘𝙤𝙧𝙙', 'dns_cname'),
        ('⚡️ 𝙏𝙓𝙏 𝙍𝙚𝙘𝙤𝙧𝙙', 'dns_txt'),
        ('⚡️ 𝙉𝙎 𝙍𝙚𝙘𝙤𝙧𝙙', 'dns_ns')
    ]
    
    for text, callback in types:
        markup.add(telebot.types.InlineKeyboardButton(text, callback_data=callback))
    markup.add(telebot.types.InlineKeyboardButton('🔙 𝘽𝙖𝙘𝙠 𝙏𝙤 𝙈𝙚𝙣𝙪', callback_data='back_to_menu'))
    bot.send_message(message.chat.id, "⚡️ 𝙎𝙚𝙡𝙚𝙘𝙩 𝘿𝙉𝙎 𝙍𝙚𝙘𝙤𝙧𝙙 𝙏𝙮𝙥𝙚", reply_markup=markup)

def schedule_domain_deletion(record_id, user_id):
    def delete_domain():
        time.sleep(4 * 24 * 60 * 60)  # 4 days
        url = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records/{record_id}"
        headers = {
            "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
            "Content-Type": "application/json"
        }
        requests.delete(url, headers=headers)
        if user_id in user_domain_counts:
            user_domain_counts[user_id] -= 1

    threading.Thread(target=delete_domain, daemon=True).start()

def ask_proxied_status(message, record_type, name, content):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton('✅ 𝙔𝙚𝙨', callback_data=f'proxy_yes_{record_type}_{name}_{content}'),
        telebot.types.InlineKeyboardButton('❌ 𝙉𝙤', callback_data=f'proxy_no_{record_type}_{name}_{content}')
    )
    bot.send_message(message.chat.id, "⚡️ 𝙀𝙣𝙖𝙗𝙡𝙚 𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚 𝙋𝙧𝙤𝙭𝙮?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('proxy_'))
def handle_proxy_selection(call):
    _, proxy_choice, record_type, name, content = call.data.split('_')
    proxied = proxy_choice == 'yes'
    
    create_dns_record(call.message, record_type, name, content, proxied)

def handle_dns_record_type(call):
    user_id = call.from_user.id
    record_type = call.data.split('_')[1].upper()
    user_states[user_id] = {'type': record_type}
    
    bot.answer_callback_query(call.id)
    #bot.delete_message(call.message.chat.id, call.message.message_id)
    msg = f"⚡️ 𝙎𝙚𝙣𝙙 𝙮𝙤𝙪𝙧 𝙨𝙪𝙗𝙙𝙤𝙢𝙖𝙞𝙣"
    sent = bot.send_message(call.message.chat.id, msg)
    bot.register_next_step_handler(sent, process_record_name)

def process_record_name(message):
    user_id = message.from_user.id
    if user_id not in user_states:
        bot.send_message(message.chat.id, "❌ 𝙀𝙧𝙧𝙤𝙧: 𝙋𝙡𝙚𝙖𝙨𝙚 𝙨𝙩𝙖𝙧𝙩 𝙤𝙫𝙚𝙧")
        return
    
    user_states[user_id]['name'] = message.text.lower()
    record_type = user_states[user_id]['type']
    
    msg = f"⚡️ 𝙎𝙚𝙣𝙙 𝙮𝙤𝙪𝙧 {record_type} 𝙧𝙚𝙘𝙤𝙧𝙙 𝙘𝙤𝙣𝙩𝙚𝙣𝙩"
    sent = bot.send_message(message.chat.id, msg)
    bot.register_next_step_handler(sent, process_record_content)

def process_record_content(message):
    user_id = message.from_user.id
    if user_id not in user_states:
        bot.send_message(message.chat.id, "❌ 𝙀𝙧𝙧𝙤𝙧: 𝙋𝙡𝙚𝙖𝙨𝙚 𝙨𝙩𝙖𝙧𝙩 𝙤𝙫𝙚𝙧")
        return
    
    state = user_states[user_id]
    record_type = state['type']
    
    # Only A, AAAA, and CNAME records can be proxied
    if record_type in ['A', 'AAAA', 'CNAME']:
        ask_proxied_status(message, record_type, state['name'], message.text)
    else:
        create_dns_record(message, record_type, state['name'], message.text, False)
    del user_states[user_id]

def create_dns_record(message, record_type, name, content, proxied):
    user_id = message.chat.id
    if not can_create_domain(user_id):
        bot.send_message(message.chat.id, "❌ 𝙔𝙤𝙪'𝙫𝙚 𝙧𝙚𝙖𝙘𝙝𝙚𝙙 𝙩𝙝𝙚 𝙢𝙖𝙭𝙞𝙢𝙪𝙢 𝙡𝙞𝙢𝙞𝙩 𝙤𝙛 15 𝙙𝙤𝙢𝙖𝙞𝙣𝙨.")
        return

    url = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "type": record_type,
        "name": f"{name}.{DOMAIN}",
        "content": content,
        "ttl": 1,
        "proxied": proxied and record_type in ['A', 'AAAA', 'CNAME']  # Only allow proxy for A, AAAA, and CNAME
    }
    
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get('success'):
        record = result['result']
        msg = (f"✅ 𝘿𝙉𝙎 𝙍𝙚𝙘𝙤𝙧𝙙 𝘾𝙧𝙚𝙖𝙩𝙚𝙙!\n\n"
               f"• 𝙏𝙮𝙥𝙚: {record_type}\n"
               f"• 𝙁𝙪𝙡𝙡 𝘿𝙤𝙢𝙖𝙞𝙣: <code>{record['name']}</code>\n"
               f"• 𝙋𝙤𝙞𝙣𝙩𝙨 𝙩𝙤: <code>{record['content']}</code>"
               + (f"\n• 𝙋𝙧𝙤𝙭𝙞𝙚𝙙: {'✅' if record['proxied'] else '❌'}" if record_type in ['A', 'AAAA', 'CNAME'] else ""))
        
        # Increment domain count and schedule deletion
        user_domain_counts[user_id] = user_domain_counts.get(user_id, 0) + 1
        schedule_domain_deletion(record['id'], user_id)
    else:
        error_msg = result.get('errors', [{'message': 'Unknown error'}])[0]['message']
        msg = f"❌ 𝙀𝙧𝙧𝙤𝙧: {error_msg}"
    
    bot.send_message(message.chat.id, msg, parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: call.data == 'create_domain')
def handle_create_domain(call):
    if not can_create_domain(call.from_user.id):
        bot.send_message(call.message.chat.id, "❌ 𝙔𝙤𝙪'𝙫𝙚 𝙧𝙚𝙖𝙘𝙝𝙚𝙙 𝙩𝙝𝙚 𝙢𝙖𝙭𝙞𝙢𝙪𝙢 𝙡𝙞𝙢𝙞𝙩 𝙤𝙛 15 𝙙𝙤𝙢𝙖𝙞𝙣𝙨.")
        show_main_menu(call.message.chat.id)
        return

    show_record_type_selection(call.message)
    bot.answer_callback_query(call.id)
    #bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == 'back_to_menu')
def handle_back_to_menu(call):
    bot.answer_callback_query(call.id)
    #bot.delete_message(call.message.chat.id, call.message.message_id)
    show_main_menu(call.message.chat.id)

if __name__ == "__main__":
    # Create a logger
    logger = getLogger(__name__)
    logger.setLevel(DEBUG)

    # Create handlers
    file_handler = FileHandler('bot.log')
    console_handler = StreamHandler()  # Output to console

    # Create formatters and add them to the handlers
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Now you can log messages using the logger
    logger.info('Logger configured successfully')

    print("Sf bot khdam asat")
    while True:
        try:
            bot.polling()
        except Exception as e:
            handle_error(e)
