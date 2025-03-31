#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import shutil
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
def clear_screen():
    os.system('clear')

def print_banner():
    banner = f"""{Colors.BLUE}
    ╔═══════════════════════════════════════════╗
    ║             SSH BOT INSTALLER             ║
    ║         Created by: {Colors.GREEN}@RT_YB{Colors.BLUE}             ║
    ╚═══════════════════════════════════════════╝{Colors.ENDC}
    """
    print(banner)

def print_step(step, total_steps, message):
    percentage = (step / total_steps) * 100
    bar_length = 40
    filled_length = int(bar_length * step // total_steps)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    print(f"\r{Colors.YELLOW}{message}")
    print(f"{Colors.BLUE}[{bar}] {Colors.GREEN}{percentage:.1f}%{Colors.ENDC}", end='\n')

def run_command(command, error_message="Error executing command"):
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"{Colors.YELLOW}│ {output.strip()}{Colors.ENDC}")
        
        if process.poll() != 0:
            print(f"{Colors.RED}╰─❯ {error_message}{Colors.ENDC}")
            return False
        return True
    except Exception as e:
        print(f"{Colors.RED}╰─❯ {error_message}: {str(e)}{Colors.ENDC}")
        return False

def get_terminal_size():
    return shutil.get_terminal_size()

def print_status(message, status):
    columns = get_terminal_size().columns
    status_color = Colors.GREEN if status else Colors.RED
    status_text = "✓ SUCCESS" if status else "✗ FAILED"
    print(f"{Colors.BLUE}├─{Colors.YELLOW}{message}{' ' * (columns - len(message) - 20)}{status_color}{status_text}{Colors.ENDC}")

def print_section(title):
    columns = get_terminal_size().columns
    print(f"\n{Colors.BLUE}╭{'═' * (columns - 2)}╮")
    print(f"│{Colors.GREEN}{title.center(columns - 2)}{Colors.BLUE}│")
    print(f"├{'─' * (columns - 2)}┤{Colors.ENDC}")

def main():
    if os.geteuid() != 0:
        print(f"{Colors.RED}This script must be run as root!{Colors.ENDC}")
        sys.exit(1)

    clear_screen()
    print_banner()
    
    total_steps = 8
    current_step = 0

    # Step 1: Update System
    current_step += 1
    print_section("System Update")
    print_step(current_step, total_steps, "Updating system packages...")
    status = run_command("apt update && apt upgrade -y")
    print_status("System update", status)

    # Step 2: Install Dependencies
    current_step += 1
    print_section("Installing Dependencies")
    print_step(current_step, total_steps, "Installing required packages...")
    status = run_command("apt install -y python3 python3-pip python3-venv git unzip wget systemd")
    print_status("Package installation", status)

    # Step 3: Create Directory
    current_step += 1
    print_section("Creating Workspace")
    print_step(current_step, total_steps, "Setting up workspace...")
    try:
        os.makedirs("/root/amine", exist_ok=True)
        os.chdir("/root/amine")
        print_status("Directory setup", True)
    except Exception as e:
        print_status(f"Directory setup failed: {str(e)}", False)
        sys.exit(1)

    # Step 4: Clone Repository
    current_step += 1
    print_section("Cloning Repository")
    print_step(current_step, total_steps, "Downloading bot files...")
    status = run_command("git clone https://github.com/AmineBaggarii/bot.git .")
    print_status("Repository clone", status)

    # Step 5: Setup Virtual Environment
    current_step += 1
    print_section("Python Environment Setup")
    print_step(current_step, total_steps, "Creating virtual environment...")
    status = run_command("python3 -m venv myenv && source myenv/bin/activate")
    print_status("Virtual environment", status)

    # Step 6: Install Requirements
    current_step += 1
    print_section("Installing Python Packages")
    print_step(current_step, total_steps, "Installing Python requirements...")
    status = run_command("pip install -r requirements.txt")
    print_status("Python packages", status)

    # Step 7: Create Service
    current_step += 1
    print_section("Creating System Service")
    print_step(current_step, total_steps, "Setting up systemd service...")
    service_content = """[Unit]
Description=SSH Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/amine
Environment="PATH=/root/amine/myenv/bin"
ExecStart=/root/amine/myenv/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    try:
        with open("/etc/systemd/system/sshbot.service", "w") as f:
            f.write(service_content)
        print_status("Service creation", True)
    except Exception as e:
        print_status(f"Service creation failed: {str(e)}", False)

    # Step 8: Start Service
    current_step += 1
    print_section("Starting Bot Service")
    print_step(current_step, total_steps, "Starting bot...")
    status = run_command("systemctl daemon-reload && systemctl enable sshbot && systemctl start sshbot")
    print_status("Service start", status)

    # Final Banner
    print(f"""
{Colors.BLUE}╔═══════════════════════════════════════════╗
║{Colors.GREEN}           Installation Complete!           {Colors.BLUE}║
╠═══════════════════════════════════════════╣
║{Colors.YELLOW} Bot Commands:                            {Colors.BLUE}║
║{Colors.YELLOW} • Status:  {Colors.GREEN}systemctl status sshbot       {Colors.BLUE}║
║{Colors.YELLOW} • Logs:    {Colors.GREEN}journalctl -u sshbot -f      {Colors.BLUE}║
║{Colors.YELLOW} • Restart: {Colors.GREEN}systemctl restart sshbot      {Colors.BLUE}║
║{Colors.YELLOW} • Stop:    {Colors.GREEN}systemctl stop sshbot         {Colors.BLUE}║
╚═══════════════════════════════════════════╝{Colors.ENDC}
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Installation cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Installation failed: {str(e)}{Colors.ENDC}")
        sys.exit(1)
