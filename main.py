import telebot
import logging
from telebot import types
from logging import getLogger, Formatter, FileHandler, StreamHandler, DEBUG
from config import *
from utils import *
from ssh_tools import *
from ssh_creation import *
from domain_manager import *
from admin_panel import create_admin_panel, handle_admin_callback, init_db, save_user

bot = telebot.TeleBot(TOKEN)
logging.basicConfig(filename='bot.log', level=logging.ERROR)

@bot.message_handler(commands=['start'])
def start(message):
    if not check_subscription(message.from_user.id):
        show_join_channel_message(message.chat.id)
        return

    # Save user to database
    save_user(message.from_user)
    
    markup = types.InlineKeyboardMarkup()
    
    # Main menu buttons
    create_ssh = types.InlineKeyboardButton('🔐 𝘾𝙧𝙚𝙖𝙩𝙚 𝙎𝙎𝙃', callback_data='create_ssh')
    ssh_tools = types.InlineKeyboardButton('🛠 𝙎𝙎𝙃 𝙏𝙤𝙤𝙡𝙨', callback_data='ssh_tools')
    create_domain = types.InlineKeyboardButton('🌐 𝘾𝙧𝙚𝙖𝙩𝙚 𝘿𝙤𝙢𝙖𝙞𝙣', callback_data='create_domain')
    contact = types.InlineKeyboardButton('📞 𝘾𝙤𝙣𝙩𝙖𝙘𝙩 𝘿𝙚𝙫𝙚𝙡𝙤𝙥𝙚𝙧', url='https://t.me/aminebaggarii')
    
    markup.add(create_ssh)
    markup.add(ssh_tools, create_domain)
    markup.add(contact)
    
    welcome_message = (
        "𝙒𝙚𝙡𝙘𝙤𝙢𝙚! 𝙏𝙝𝙖𝙣𝙠 𝙮𝙤𝙪 𝙛𝙤𝙧 𝙐𝙨𝙞𝙣𝙜 𝙩𝙝𝙚 𝙁𝙧𝙚𝙚 𝙎𝙎𝙃 𝘽𝙤𝙩.\n\n"
        "𝙏𝙤 𝙋𝙪𝙧𝙘𝙝𝙖𝙨𝙚 𝙩𝙝𝙚 𝘽𝙤𝙩, 𝙋𝙡𝙚𝙖𝙨𝙚 𝘾𝙤𝙣𝙩𝙖𝙘𝙩 @aminebaggarii. , "
        "𝙔𝙤𝙪 𝘾𝙖𝙣 𝙘𝙧𝙚𝙖𝙩𝙚 𝙐𝙣𝙡𝙞𝙢𝙞𝙩𝙚𝙙 𝙐𝙨𝙚𝙧𝙨 𝘼𝙣𝙙 𝙋𝙖𝙨𝙨𝙬𝙤𝙧𝙙𝙨."
    )
    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)

@bot.message_handler(commands=['admin'])
def admin(message):
    create_admin_panel(bot, message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    if call.data == 'create_ssh':
        create_ssh_menu(bot, call.message.chat.id)
    elif call.data == 'ssh_tools':
        create_ssh_tools_menu(bot, call.message.chat.id)
    elif call.data == 'create_domain':
        create_domain_menu(bot, call.message.chat.id)
    elif call.data == 'back_to_menu':
        start(call.message)
    elif call.data.startswith('tool_'):
        handle_tool_selection(call)
    elif call.data.startswith('add_user_'):
        service_type = call.data.replace('add_user_', '')
        process_ssh_creation(bot, call.message, service_type)
    elif call.data.startswith('record_'):
        record_type = call.data.replace('record_', '')
        handle_dns_record_type(call)
    elif call.data.startswith('admin_'):
        handle_admin_callback(bot, call)

def handle_tool_selection(call):
    chat_id = call.message.chat.id
    tool_type = call.data.replace('tool_', '')
    
    if tool_type == 'hostname':
        msg = bot.send_message(chat_id, "📝 𝙀𝙣𝙩𝙚𝙧 𝙩𝙝𝙚 𝙝𝙤𝙨𝙩𝙣𝙖𝙢𝙚:")
        bot.register_next_step_handler(msg, process_hostname)
    elif tool_type == 'port':
        msg = bot.send_message(chat_id, "📝 𝙀𝙣𝙩𝙚𝙧 𝙩𝙝𝙚 𝙝𝙤𝙨𝙩 𝙖𝙣𝙙 𝙥𝙤𝙧𝙩 (𝙚.𝙜. 1.1.1.1 80):")
        bot.register_next_step_handler(msg, process_port_check)
    elif tool_type == 'speed':
        msg = bot.send_message(chat_id, "⏳ 𝙍𝙪𝙣𝙣𝙞𝙣𝙜 𝙨𝙥𝙚𝙚𝙙 𝙩𝙚𝙨𝙩...")
        result = run_speed_test()
        bot.edit_message_text(result, chat_id, msg.message_id)
    elif tool_type == 'ip':
        msg = bot.send_message(chat_id, "📝 𝙀𝙣𝙩𝙚𝙧 𝙩𝙝𝙚 𝙄𝙋 𝙖𝙙𝙙𝙧𝙚𝙨𝙨:")
        bot.register_next_step_handler(msg, process_ip_lookup)

def process_hostname(message):
    result = hostname_to_ip(message.text)
    bot.reply_to(message, result, reply_markup=get_back_button())

def process_port_check(message):
    try:
        host, port = message.text.split()
        result = check_port(host, port)
    except:
        result = "❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙛𝙤𝙧𝙢𝙖𝙩. 𝙐𝙨𝙚: 𝙝𝙤𝙨𝙩 𝙥𝙤𝙧𝙩"
    bot.reply_to(message, result, reply_markup=get_back_button())

def process_ip_lookup(message):
    result = ip_lookup(message.text)
    bot.reply_to(message, result, reply_markup=get_back_button())

if __name__ == "__main__":
    logger = getLogger(__name__)
    logger.setLevel(DEBUG)
    
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = FileHandler('bot.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    # Initialize database
    init_db()
    logger.info("Bot started")
    bot.infinity_polling()
