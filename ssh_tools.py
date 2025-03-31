import telebot
import socket
import speedtest
import requests
import dns.resolver
import whois
import ssl
import subprocess
from telebot import types
from config import *

def create_ssh_tools_menu(bot, chat_id):
    markup = types.InlineKeyboardMarkup()
    
    # Network Tools
    hostname_btn = types.InlineKeyboardButton('🔍 𝙃𝙤𝙨𝙩𝙣𝙖𝙢𝙚 𝙩𝙤 𝙄𝙋', callback_data='tool_hostname')
    port_btn = types.InlineKeyboardButton('🔌 𝙋𝙤𝙧𝙩 𝘾𝙝𝙚𝙘𝙠𝙚𝙧', callback_data='tool_port')
    speed_btn = types.InlineKeyboardButton('⚡️ 𝙎𝙥𝙚𝙚𝙙 𝙏𝙚𝙨𝙩', callback_data='tool_speed')
    ip_btn = types.InlineKeyboardButton('🌐 𝙄𝙋 𝙇𝙤𝙤𝙠𝙪𝙥', callback_data='tool_ip')
    
    # Domain Tools
    dns_btn = types.InlineKeyboardButton('🔄 𝘿𝙉𝙎 𝙇𝙤𝙤𝙠𝙪𝙥', callback_data='tool_dns')
    ssl_btn = types.InlineKeyboardButton('🔒 𝙎𝙎𝙇 𝘾𝙝𝙚𝙘𝙠𝙚𝙧', callback_data='tool_ssl')
    whois_btn = types.InlineKeyboardButton('📋 𝙒𝙃𝙊𝙄𝙎', callback_data='tool_whois')
    
    # Server Tools
    ping_btn = types.InlineKeyboardButton('📡 𝙋𝙞𝙣𝙜 𝙏𝙚𝙨𝙩', callback_data='tool_ping')
    trace_btn = types.InlineKeyboardButton('🛤 𝙏𝙧𝙖𝙘𝙚𝙧𝙤𝙪𝙩𝙚', callback_data='tool_trace')
    http_btn = types.InlineKeyboardButton('🌍 𝙃𝙏𝙏𝙋 𝙏𝙚𝙨𝙩', callback_data='tool_http')
    
    # Navigation
    back_btn = types.InlineKeyboardButton('↩️ 𝘽𝙖𝙘𝙠', callback_data='back_to_menu')
    
    # Arrange buttons in grid
    markup.add(hostname_btn, port_btn)
    markup.add(speed_btn, ip_btn)
    markup.add(dns_btn, ssl_btn)
    markup.add(whois_btn, ping_btn)
    markup.add(trace_btn, http_btn)
    markup.add(back_btn)
    
    bot.send_message(
        chat_id,
        "🛠 𝙎𝙎𝙃 𝙏𝙤𝙤𝙡𝙨 𝙈𝙚𝙣𝙪:\n\n"
        "𝙎𝙚𝙡𝙚𝙘𝙩 𝙖 𝙩𝙤𝙤𝙡 𝙩𝙤 𝙪𝙨𝙚:",
        reply_markup=markup
    )

def hostname_to_ip(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        return f"✅ 𝙃𝙤𝙨𝙩𝙣𝙖𝙢𝙚: {hostname}\n🌐 𝙄𝙋 𝘼𝙙𝙙𝙧𝙚𝙨𝙨: {ip}"
    except:
        return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙧𝙚𝙨𝙤𝙡𝙫𝙚 𝙝𝙤𝙨𝙩𝙣𝙖𝙢𝙚"

def check_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        
        if result == 0:
            return f"✅ 𝙋𝙤𝙧𝙩 {port} 𝙞𝙨 𝙤𝙥𝙚𝙣 𝙤𝙣 {host}"
        else:
            return f"❌ 𝙋𝙤𝙧𝙩 {port} 𝙞𝙨 𝙘𝙡𝙤𝙨𝙚𝙙 𝙤𝙣 {host}"
    except:
        return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙘𝙝𝙚𝙘𝙠 𝙥𝙤𝙧𝙩"

def run_speed_test():
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        ping = st.results.ping
        
        return (
            "📊 𝙎𝙥𝙚𝙚𝙙 𝙏𝙚𝙨𝙩 𝙍𝙚𝙨𝙪𝙡𝙩𝙨:\n\n"
            f"⬇️ 𝘿𝙤𝙬𝙣𝙡𝙤𝙖𝙙: {download_speed:.2f} 𝙈𝙗𝙥𝙨\n"
            f"⬆️ 𝙐𝙥𝙡𝙤𝙖𝙙: {upload_speed:.2f} 𝙈𝙗𝙥𝙨\n"
            f"📶 𝙋𝙞𝙣𝙜: {ping:.2f} 𝙢𝙨"
        )
    except:
        return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙧𝙪𝙣 𝙨𝙥𝙚𝙚𝙙 𝙩𝙚𝙨𝙩"

def ip_lookup(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        
        if data['status'] == 'success':
            return (
                f"🌐 𝙄𝙋 𝙇𝙤𝙤𝙠𝙪𝙥 𝙍𝙚𝙨𝙪𝙡𝙩𝙨 𝙛𝙤𝙧 {ip}:\n\n"
                f"🌍 𝘾𝙤𝙪𝙣𝙩𝙧𝙮: {data['country']}\n"
                f"🏢 𝙄𝙎𝙋: {data['isp']}\n"
                f"🌆 𝘾𝙞𝙩𝙮: {data['city']}\n"
                f"🗺 𝙍𝙚𝙜𝙞𝙤𝙣: {data['regionName']}\n"
                f"⏰ 𝙏𝙞𝙢𝙚𝙯𝙤𝙣𝙚: {data['timezone']}"
            )
        else:
            return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙡𝙤𝙤𝙠𝙪𝙥 𝙄𝙋"
    except:
        return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙡𝙤𝙤𝙠𝙪𝙥 𝙄𝙋"

def check_dns(domain):
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, 'A')
        result = f"🔄 𝘿𝙉𝙎 𝙇𝙤𝙤𝙠𝙪𝙥 𝙛𝙤𝙧 {domain}:\n\n"
        for rdata in answers:
            result += f"• 𝙄𝙋: {rdata}\n"
        return result
    except:
        return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙧𝙚𝙨𝙤𝙡𝙫𝙚 𝘿𝙉𝙎"

def check_ssl(domain):
    try:
        import ssl
        import socket
        context = ssl.create_default_context()
        with context.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.connect((domain, 443))
            cert = s.getpeercert()
            return (
                f"🔒 𝙎𝙎𝙇 𝘾𝙚𝙧𝙩𝙞𝙛𝙞𝙘𝙖𝙩𝙚 𝙄𝙣𝙛𝙤:\n\n"
                f"• 𝙄𝙨𝙨𝙪𝙚𝙧: {dict(cert['issuer'][0])[('commonName',)]}\n"
                f"• 𝙀𝙭𝙥𝙞𝙧𝙚𝙨: {cert['notAfter']}\n"
                f"• 𝙎𝙪𝙗𝙟𝙚𝙘𝙩: {dict(cert['subject'][0])[('commonName',)]}"
            )
    except:
        return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙘𝙝𝙚𝙘𝙠 𝙎𝙎𝙇"

def check_whois(domain):
    try:
        import whois
        w = whois.whois(domain)
        return (
            f"📋 𝙒𝙃𝙊𝙄𝙎 𝙄𝙣𝙛𝙤 𝙛𝙤𝙧 {domain}:\n\n"
            f"• 𝙍𝙚𝙜𝙞𝙨𝙩𝙧𝙖𝙧: {w.registrar}\n"
            f"• 𝘾𝙧𝙚𝙖𝙩𝙞𝙤𝙣 𝘿𝙖𝙩𝙚: {w.creation_date}\n"
            f"• 𝙀𝙭𝙥𝙞𝙧𝙮 𝘿𝙖𝙩𝙚: {w.expiration_date}\n"
            f"• 𝙎𝙩𝙖𝙩𝙪𝙨: {w.status}"
        )
    except:
        return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙜𝙚𝙩 𝙒𝙃𝙊𝙄𝙎 𝙞𝙣𝙛𝙤"

def ping_host(host):
    try:
        import subprocess
        result = subprocess.run(['ping', '-c', '4', host], capture_output=True, text=True)
        return f"📡 𝙋𝙞𝙣𝙜 𝙍𝙚𝙨𝙪𝙡𝙩𝙨:\n\n{result.stdout}"
    except:
        return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙥𝙞𝙣𝙜 𝙝𝙤𝙨𝙩"

def traceroute(host):
    try:
        import subprocess
        result = subprocess.run(['traceroute', host], capture_output=True, text=True)
        return f"🛤 𝙏𝙧𝙖𝙘𝙚𝙧𝙤𝙪𝙩𝙚 𝙍𝙚𝙨𝙪𝙡𝙩𝙨:\n\n{result.stdout}"
    except:
        return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙧𝙪𝙣 𝙩𝙧𝙖𝙘𝙚𝙧𝙤𝙪𝙩𝙚"

def http_test(url):
    try:
        response = requests.get(url)
        return (
            f"🌍 𝙃𝙏𝙏𝙋 𝙏𝙚𝙨𝙩 𝙍𝙚𝙨𝙪𝙡𝙩𝙨:\n\n"
            f"• 𝙎𝙩𝙖𝙩𝙪𝙨: {response.status_code}\n"
            f"• 𝙍𝙚𝙨𝙥𝙤𝙣𝙨𝙚 𝙏𝙞𝙢𝙚: {response.elapsed.total_seconds()}s\n"
            f"• 𝙎𝙚𝙧𝙫𝙚𝙧: {response.headers.get('Server', 'Unknown')}"
        )
    except:
        return "❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙩𝙚𝙨𝙩 𝙃𝙏𝙏𝙋"

@bot.callback_query_handler(func=lambda call: call.data.startswith('tool_'))
def handle_tool_callback(call):
    chat_id = call.message.chat.id
    tool = call.data.replace('tool_', '')
    
    if tool == 'hostname':
        bot.send_message(chat_id, "𝙎𝙚𝙣𝙙 𝙩𝙝𝙚 𝙝𝙤𝙨𝙩𝙣𝙖𝙢𝙚 𝙩𝙤 𝙘𝙝𝙚𝙘𝙠:")
        bot.register_next_step_handler(call.message, process_hostname)
    elif tool == 'port':
        bot.send_message(chat_id, "𝙎𝙚𝙣𝙙 𝙩𝙝𝙚 𝙝𝙤𝙨𝙩:𝙥𝙤𝙧𝙩 𝙩𝙤 𝙘𝙝𝙚𝙘𝙠:")
        bot.register_next_step_handler(call.message, process_port)
    elif tool == 'speed':
        bot.send_message(chat_id, "𝙍𝙪𝙣𝙣𝙞𝙣𝙜 𝙨𝙥𝙚𝙚𝙙 𝙩𝙚𝙨𝙩...")
        result = run_speed_test()
        bot.send_message(chat_id, result)
    elif tool == 'ip':
        bot.send_message(chat_id, "𝙎𝙚𝙣𝙙 𝙩𝙝𝙚 𝙄𝙋 𝙩𝙤 𝙡𝙤𝙤𝙠𝙪𝙥:")
        bot.register_next_step_handler(call.message, process_ip)
    elif tool == 'dns':
        bot.send_message(chat_id, "𝙎𝙚𝙣𝙙 𝙩𝙝𝙚 𝙙𝙤𝙢𝙖𝙞𝙣 𝙩𝙤 𝙘𝙝𝙚𝙘𝙠 𝘿𝙉𝙎:")
        bot.register_next_step_handler(call.message, process_dns)
    elif tool == 'ssl':
        bot.send_message(chat_id, "𝙎𝙚𝙣𝙙 𝙩𝙝𝙚 𝙙𝙤𝙢𝙖𝙞𝙣 𝙩𝙤 𝙘𝙝𝙚𝙘𝙠 𝙎𝙎𝙇:")
        bot.register_next_step_handler(call.message, process_ssl)
    elif tool == 'whois':
        bot.send_message(chat_id, "𝙎𝙚𝙣𝙙 𝙩𝙝𝙚 𝙙𝙤𝙢𝙖𝙞𝙣 𝙛𝙤𝙧 𝙒𝙃𝙊𝙄𝙎:")
        bot.register_next_step_handler(call.message, process_whois)
    elif tool == 'ping':
        bot.send_message(chat_id, "𝙎𝙚𝙣𝙙 𝙩𝙝𝙚 𝙝𝙤𝙨𝙩 𝙩𝙤 𝙥𝙞𝙣𝙜:")
        bot.register_next_step_handler(call.message, process_ping)
    elif tool == 'trace':
        bot.send_message(chat_id, "𝙎𝙚𝙣𝙙 𝙩𝙝𝙚 𝙝𝙤𝙨𝙩 𝙩𝙤 𝙩𝙧𝙖𝙘𝙚:")
        bot.register_next_step_handler(call.message, process_traceroute)
    elif tool == 'http':
        bot.send_message(chat_id, "𝙎𝙚𝙣𝙙 𝙩𝙝𝙚 𝙐𝙍𝙇 𝙩𝙤 𝙩𝙚𝙨𝙩:")
        bot.register_next_step_handler(call.message, process_http)

def process_hostname(message):
    result = hostname_to_ip(message.text)
    bot.reply_to(message, result)

def process_port(message):
    host, port = message.text.split(':')
    result = check_port(host, port)
    bot.reply_to(message, result)

def process_ip(message):
    result = ip_lookup(message.text)
    bot.reply_to(message, result)

def process_dns(message):
    result = check_dns(message.text)
    bot.reply_to(message, result)

def process_ssl(message):
    result = check_ssl(message.text)
    bot.reply_to(message, result)

def process_whois(message):
    result = check_whois(message.text)
    bot.reply_to(message, result)

def process_ping(message):
    result = ping_host(message.text)
    bot.reply_to(message, result)

def process_traceroute(message):
    result = traceroute(message.text)
    bot.reply_to(message, result)

def process_http(message):
    result = http_test(message.text)
    bot.reply_to(message, result)
