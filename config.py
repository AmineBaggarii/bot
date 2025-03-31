TOKEN = '6768147175:AAH9-IT8GiLtS_ieezhpMu4fo_5okQqpxvw'
AMINE_ID = '6455079270'

# Cloudflare configuration
CLOUDFLARE_API_TOKEN = "X5v0gNw8F2RPwOSC2RXJnLSJubgxWhFoerciH0jY"
CLOUDFLARE_ZONE_ID = "c619be390559750d014eb4905ac57838"
DOMAIN = "aminebaggari.com"

# Admin IDs
ADMIN_IDS = {AMINE_ID}  # Using set for faster lookups
OWNER_ID = AMINE_ID     # Original owner can't be removed

# Server credentials
AMINE_IP = '64.226.120.120'
AMINE_USERNAME = 'root'
AMINE_PASSWORD = '010119966'

# Channel settings
CHANNEL_USERNAME = "RT_CFG"

# Service configuration
MAX_CONCURRENT_THREADS = 10

# Initial service status
service_status = {
    'Cloudflare': True,
    'Cloudfront': False,
    'UDP Custom': True,
    'SlowDNS': True,
    'SSL Direct': True
}

# Creation statistics
creation_stats = {
    'Cloudflare': 0,
    'Cloudfront': 0,
    'UDP Custom': 0,
    'SlowDNS': 0,
    'SSL Direct': 0
}
