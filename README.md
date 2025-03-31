# Telegram Bot with VPS Management

A powerful Telegram bot that allows users to manage VPS services and execute commands remotely.

## Features

- VPS Service Management
- User Management
- Command Execution
- Service Status Monitoring
- Admin Panel
- User Limits Management

## Prerequisites

- Python 3.7 or higher
- pip3
- A VPS server
- Telegram Bot Token (from @BotFather)
- Your Telegram User ID

## Installation

1. Clone this repository or download the files:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

2. Make the installer script executable:
```bash
chmod +x install.sh
```

3. Run the installer:
```bash
./install.sh
```

4. Follow the prompts to enter your:
   - Telegram Bot Token
   - Telegram User ID
   - VPS IP Address
   - VPS Username
   - VPS Password

The installer will:
- Install required dependencies
- Configure the bot with your credentials
- Set up the bot as a system service
- Start the bot automatically

## Usage

### Admin Commands

- `/admin` - Access the admin control panel
- `/cmd <command>` - Execute a command on the VPS
- `/block <user_id>` - Block a user
- `/unblock <user_id>` - Unblock a user

### User Commands

- `/start` - Start the bot
- `/help` - Show help information

## Service Management

The bot runs as a system service. You can manage it using these commands:

```bash
# Check status
sudo systemctl status telegram-bot

# View logs
sudo journalctl -u telegram-bot

# Restart the bot
sudo systemctl restart telegram-bot

# Stop the bot
sudo systemctl stop telegram-bot

# Start the bot
sudo systemctl start telegram-bot
```

## Security Notes

- Keep your bot token and VPS credentials secure
- Regularly update your VPS password
- Monitor the bot logs for suspicious activity
- Use the block/unblock commands to manage user access

## Support

For support, please contact the bot administrator or create an issue in the GitHub repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 