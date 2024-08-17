import logging
import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define your channels and admin IDs
CHANNELS = ['@crypto_Dragonz', '@TWENewss']
ADMIN_IDS = {5226868404, 800092886}

# Get the bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Path to the users file
USERS_FILE = 'users.json'

def load_users():
    """Load users from the JSON file."""
    if not os.path.exists(USERS_FILE):
        logger.info(f"{USERS_FILE} not found, creating a new one.")
        return []

    try:
        with open(USERS_FILE, 'r') as file:
            data = json.load(file)
            return list(data) if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading users from {USERS_FILE}: {e}")
        return []

def save_user(user_id):
    """Save a user ID to the JSON file."""
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        try:
            with open(USERS_FILE, 'w') as file:
                json.dump(users, file)
            logger.info(f"User {user_id} saved successfully.")
        except IOError as e:
            logger.error(f"Failed to write to {USERS_FILE}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user_id = update.effective_user.id
    username = update.effective_user.username

    logger.info(f"User @{username} triggered /start command")
    save_user(user_id)

    welcome_message = (
        f"Peace be upon you, my friend @{username}\n"
        "Welcome to the free hamster keys bot 🫱🏻‍🫲🏻"
    )

    joined_channels = []
    for channel in CHANNELS:
        try:
            chat_member = await context.bot.get_chat_member(channel, user_id)
            if chat_member.status in ['member', 'creator', 'administrator']:
                joined_channels.append(channel)
        except Exception as e:
            logger.warning(f"Could not access channel {channel} for user {user_id}: {e}")
            await update.message.reply_text(
                f"Could not verify membership in {channel}. "
                "Please ensure the bot has the correct permissions."
            )
            return

    if len(joined_channels) == len(CHANNELS):
        success_message = (
            "You have successfully joined all required channels.\n"
            "To run the bot, click the button 👇🏻"
        )
        keyboard = [
            [InlineKeyboardButton("Get KeyGen 🔑", url="https://t.me/TWEHamsterGenBot/TWEKeyGen")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(success_message, reply_markup=reply_markup)
    else:
        join_message = (
            f"{welcome_message}\n\n"
            "You must join these 2 channels to use the bot 👇🏻\n"
            "Then use /start to get the bot."
        )
        keyboard = [
            [InlineKeyboardButton("TWE | News 🤝🏻", url="https://t.me/TWENewss")],
            [InlineKeyboardButton("Crypto Dragon 🐉", url="https://t.me/crypto_Dragonz")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(join_message, reply_markup=reply_markup)

async def get(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /get command."""
    user_id = update.effective_user.id
    save_user(user_id)

    joined_channels = []
    for channel in CHANNELS:
        try:
            chat_member = await context.bot.get_chat_member(channel, user_id)
            if chat_member.status in ['member', 'creator', 'administrator']:
                joined_channels.append(channel)
        except Exception as e:
            logger.warning(f"Could not access channel {channel} for user {user_id}: {e}")
            await update.message.reply_text(
                f"Could not verify membership in {channel}. "
                "Please ensure the bot has the correct permissions."
            )
            return

    if len(joined_channels) == len(CHANNELS):
        keyboard = [
            [InlineKeyboardButton("🔑 Get KeyGen", url="https://t.me/TWEHamsterGenBot/TWEKeyGen")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Click the button below:', reply_markup=reply_markup)
    else:
        keyboard = [
            [InlineKeyboardButton("TWE | News 🤝🏻", url="https://t.me/TWENewss")],
            [InlineKeyboardButton("Crypto Dragon 🐉", url="https://t.me/crypto_Dragonz")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("You must join these 2 channels to use the bot:", reply_markup=reply_markup)

async def count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /count command."""
    users = load_users()
    await update.message.reply_text(f"There are currently {len(users)} users in the bot.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /broadcast command."""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    users = load_users()
    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text("Please provide a message to broadcast.")
        return

    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}: {e}")

    await update.message.reply_text("Broadcast message sent to all users.")

def main() -> None:
    """Start the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("get", get))
    application.add_handler(CommandHandler("count", count))
    application.add_handler(CommandHandler("broadcast", broadcast))

    application.run_polling()

if __name__ == '__main__':
    if BOT_TOKEN is None:
        logger.error("Bot token not set! Please set the BOT_TOKEN environment variable.")
    else:
        main()
