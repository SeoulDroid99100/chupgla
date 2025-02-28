# shivu/modules/grow/utils.py

from datetime import datetime
from .config import TRAINING_MODES  # Import from local config

async def validate_session(user_data: dict, mode: str) -> tuple:
    training_log = user_data.get("progression", {}).get("training_log", {})
    last_session = training_log.get(mode)

    # Cooldown check
    if last_session and (datetime.utcnow() - last_session).seconds < TRAINING_MODES[mode]["cooldown"]:
        remaining = TRAINING_MODES[mode]["cooldown"] - (datetime.utcnow() - last_session).seconds
        return False, f"⏳ Cooldown: {remaining}s remaining"

    # Resource checks
    if user_data["economy"]["wallet"] < TRAINING_MODES[mode]["cost"]:
        return False, "❌ Insufficient funds!"

    endurance = user_data["combat_stats"]["skills"]["endurance"]
    if endurance < TRAINING_MODES[mode]["strain"]:
        return False, "❌ Exceeds endurance capacity!"

    return True, ""
