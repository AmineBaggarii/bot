import requests
from telebot import types
from config import *

def create_domain_menu(bot, chat_id):
    if not can_create_domain(chat_id):
        bot.send_message(chat_id, "❌ 𝙔𝙤𝙪'𝙫𝙚 𝙧𝙚𝙖𝙘𝙝𝙚𝙙 𝙩𝙝𝙚 𝙢𝙖𝙭𝙞𝙢𝙪𝙢 𝙙𝙤𝙢𝙖𝙞𝙣 𝙡𝙞𝙢𝙞𝙩.")
        return

    markup = types.InlineKeyboardMarkup()
    a_record = types.InlineKeyboardButton('𝘼 𝙍𝙚𝙘𝙤𝙧𝙙', callback_data='record_A')
    aaaa_record = types.InlineKeyboardButton('𝘼𝘼𝘼𝘼 𝙍𝙚𝙘𝙤𝙧𝙙', callback_data='record_AAAA')
    cname_record = types.InlineKeyboardButton('𝘾𝙉𝘼𝙈𝙀 𝙍𝙚𝙘𝙤𝙧𝙙', callback_data='record_CNAME')
    back_btn = types.InlineKeyboardButton('↩️ 𝘽𝙖𝙘𝙠', callback_data='back_to_menu')
    
    markup.add(a_record, aaaa_record)
    markup.add(cname_record)
    markup.add(back_btn)
    
    bot.send_message(
        chat_id,
        "🌐 𝘿𝙤𝙢𝙖𝙞𝙣 𝙈𝙖𝙣𝙖𝙜𝙚𝙢𝙚𝙣𝙩:\n\n"
        "𝙎𝙚𝙡𝙚𝙘𝙩 𝙩𝙝𝙚 𝙩𝙮𝙥𝙚 𝙤𝙛 𝘿𝙉𝙎 𝙧𝙚𝙘𝙤𝙧𝙙:",
        reply_markup=markup
    )

def create_dns_record(message, record_type, name, content, proxied):
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'type': record_type,
        'name': name,
        'content': content,
        'proxied': proxied
    }
    
    url = f'https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records'
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()
        
        if response_data['success']:
            record_id = response_data['result']['id']
            user_domain_counts[message.from_user.id] = user_domain_counts.get(message.from_user.id, 0) + 1
            domain_creation_times[record_id] = time.time()
            
            # Schedule domain deletion after 60 minutes
            threading.Thread(target=schedule_domain_deletion, args=(record_id, message.from_user.id)).start()
            
            return (
                f"✅ 𝘿𝙉𝙎 𝙧𝙚𝙘𝙤𝙧𝙙 𝙘𝙧𝙚𝙖𝙩𝙚𝙙 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮!\n\n"
                f"📝 𝙏𝙮𝙥𝙚: {record_type}\n"
                f"🏷 𝙉𝙖𝙢𝙚: {name}\n"
                f"📊 𝘾𝙤𝙣𝙩𝙚𝙣𝙩: {content}\n"
                f"🛡 𝙋𝙧𝙤𝙭𝙞𝙚𝙙: {'Yes' if proxied else 'No'}\n\n"
                "⏳ 𝙏𝙝𝙞𝙨 𝙧𝙚𝙘𝙤𝙧𝙙 𝙬𝙞𝙡𝙡 𝙗𝙚 𝙖𝙪𝙩𝙤𝙢𝙖𝙩𝙞𝙘𝙖𝙡𝙡𝙮 𝙙𝙚𝙡𝙚𝙩𝙚𝙙 𝙖𝙛𝙩𝙚𝙧 60 𝙢𝙞𝙣𝙪𝙩𝙚𝙨."
            )
        else:
            return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙘𝙧𝙚𝙖𝙩𝙚 𝘿𝙉𝙎 𝙧𝙚𝙘𝙤𝙧𝙙"
    except Exception as e:
        return f"❌ 𝙀𝙧𝙧𝙤𝙧: {str(e)}"

def schedule_domain_deletion(record_id, user_id):
    time.sleep(3600)  # Wait for 60 minutes
    
    headers = {
        'Authorization': f'Bearer {CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    url = f'https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records/{record_id}'
    
    try:
        requests.delete(url, headers=headers)
        if user_id in user_domain_counts:
            user_domain_counts[user_id] -= 1
    except:
        pass  # Silently fail if deletion fails
