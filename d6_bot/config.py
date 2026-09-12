import os

from dotenv import load_dotenv

load_dotenv()


def get_discord_token() -> str:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN not found. Create a .env file with the bot's token.")
    return token
