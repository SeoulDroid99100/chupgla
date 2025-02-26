class Config(object):
    LOGGER = True

    # Get this value from my.telegram.org/apps
    OWNER_ID = "6783092268"
    sudo_users = "6783092268", "6765826972"
    GROUP_ID = -1002133191051
    TOKEN = "7227094800:AAHoegjcwXUFOgeJbLnxnwbKKeRjHT4Ba5A"
    mongo_url = "mongodb+srv://Lundmate:sUF$e7pzitFXCGH@cluster0.vpqx1.mongodb.net/?retryWrites=true&w=majority"
    PHOTO_URL = ["https://envs.sh/taC.jpg"]
    SUPPORT_CHAT = "Collect_em_support"
    UPDATE_CHAT = "Collect_em_support",
    BOT_USERNAME = "Collect_Em_AllBot"
    CHARA_CHANNEL_ID = "-1002133191051"
    api_id = 26626068
    api_hash = "bf423698bcbe33cfd58b11c78c42caa2"

    
class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
