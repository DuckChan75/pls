import logging
import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, 
    ContextTypes, ConversationHandler
)

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

# Conversation states
BROADCAST_MESSAGE = 1

def load_users():
    """Load users from the JSON file."""
    if not os.path.exists(USERS_FILE):
        logger.info(f"{USERS_FILE} not found, creating a new one.")
        return []

    try:
        with open(USERS_FILE, 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading users from {USERS_FILE}: {e}")
        return []

def save_users(users):
    """Save users to the JSON file."""
    try:
        with open(USERS_FILE, 'w') as file:
            json.dump(users, file)
        logger.info(f"Users file updated successfully.")
    except IOError as e:
        logger.error(f"Failed to write to {USERS_FILE}: {e}")

def save_user(user_id):
    """Save a user ID to the JSON file."""
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

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
            "To run the bot, click one of the buttons below 👇🏻\n"
            "pls choose the servers randomly 👍🏻"
        )
        keyboard = [
            [InlineKeyboardButton("Server 1 🔑", url="https://t.me/TWEHamsterGenBot/TWEKeyGen")],
            [InlineKeyboardButton("Server 2 🔑", url="https://t.me/HamsterKombat_keys_generator_bot/HamsterKeyGen2")]
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

async def count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /count command."""
    users = load_users()
    await update.message.reply_text(f"There are currently {len(users)} users in the bot.")

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the broadcast process by asking the admin for the message."""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    await update.message.reply_text("Please provide the message you would like to broadcast.")
    return BROADCAST_MESSAGE

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the message input and broadcast it to all users."""
    users = load_users()
    message = update.message.text

    successful = 0
    failed = 0
    users_to_remove = []

    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
            successful += 1
        except Exception as e:
            logger.warning(f"Failed to send message to user {user_id}: {e}")
            failed += 1
            users_to_remove.append(user_id)

    # Remove users who blocked the bot
    if users_to_remove:
        users = [user_id for user_id in users if user_id not in users_to_remove]
        save_users(users)
        logger.info(f"Removed {len(users_to_remove)} users who blocked the bot.")

    # Send feedback message to the admin
    feedback_message = (
        f"Broadcast message sent.\n"
        f"Successful: {successful}\n"
        f"Failed: {failed}\n"
        f"Users removed: {len(users_to_remove)}"
    )
    await update.message.reply_text(feedback_message)

    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Set up the conversation handler for broadcasting
    broadcast_handler = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)],
        },
        fallbacks=[],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("count", count))
    application.add_handler(broadcast_handler)

    application.run_polling()

if __name__ == '__main__':
    if BOT_TOKEN is None:
        logger.error("Bot token not set! Please set the BOT_TOKEN environment variable.")
    else:
        main()
