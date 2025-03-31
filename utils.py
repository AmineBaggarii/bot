import subprocess
import paramiko
import psutil
import platform
import requests
from config import *

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

def get_vps_status():
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    system_info = platform.uname()
    
    status_message = (
        f"🖥 𝙑𝙋𝙎 𝙎𝙩𝙖𝙩𝙪𝙨:\n\n"
        f"💻 𝙎𝙮𝙨𝙩𝙚𝙢: {system_info.system}\n"
        f"🏷 𝙃𝙤𝙨𝙩𝙣𝙖𝙢𝙚: {system_info.node}\n"
        f"📊 𝘾𝙋𝙐 𝙐𝙨𝙖𝙜𝙚: {cpu_percent}%\n"
        f"💾 𝙈𝙚𝙢𝙤𝙧𝙮 𝙐𝙨𝙖𝙜𝙚: {memory.percent}%\n"
        f"💿 𝘿𝙞𝙨𝙠 𝙐𝙨𝙖𝙜𝙚: {disk.percent}%\n"
    )
    return status_message

def get_service_status():
    status_text = "📊 𝙎𝙚𝙧𝙫𝙞𝙘𝙚 𝙎𝙩𝙖𝙩𝙪𝙨:\n\n"
    for service, is_active in service_status.items():
        status = "✅" if is_active else "❌"
        status_text += f"{status} {service}\n"
    return status_text

def get_bot_stats():
    stats_message = (
        f"📊 𝘾𝙧𝙚𝙖𝙩𝙞𝙤𝙣 𝙎𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨:\n\n"
        f"☁️ 𝘾𝙡𝙤𝙪𝙙𝙛𝙡𝙖𝙧𝙚: {creation_stats['Cloudflare']}\n"
        f"🌩 𝘾𝙡𝙤𝙪𝙙𝙛𝙧𝙤𝙣𝙩: {creation_stats['Cloudfront']}\n"
        f"🔌 𝙐𝘿𝙋 𝘾𝙪𝙨𝙩𝙤𝙢: {creation_stats['UDP Custom']}\n"
        f"🐌 𝙎𝙡𝙤𝙬𝘿𝙉𝙎: {creation_stats['SlowDNS']}\n"
        f"🔒 𝙎𝙎𝙇 𝘿𝙞𝙧𝙚𝙘𝙩: {creation_stats['SSL Direct']}\n"
    )
    return stats_message

def get_back_button():
    markup = telebot.types.InlineKeyboardMarkup()
    back_button = telebot.types.InlineKeyboardButton('↩️ 𝘽𝙖𝙘𝙠', callback_data='back_to_menu')
    markup.add(back_button)
    return markup
