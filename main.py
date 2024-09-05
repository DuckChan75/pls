import logging
import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, 
    ContextTypes, ConversationHandler
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration variables
CHANNELS = ['@crypto_Dragonz', '@TWENewss']
ADMIN_IDS = {5226868404, 800092886}
BOT_TOKEN = os.getenv("BOT_TOKEN")
USERS_FILE = 'users.json'

BROADCAST_MESSAGE = 1

# Utility functions
def load_users():
    try:
        with open(USERS_FILE, 'r') as file:
            return set(json.load(file))
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading users from {USERS_FILE}: {e}")
        return set()

def save_users(users):
    try:
        with open(USERS_FILE, 'w') as file:
            json.dump(list(users), file)
        logger.info("Users file updated successfully.")
    except IOError as e:
        logger.error(f"Failed to write to {USERS_FILE}: {e}")

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        save_users(users)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            "Please choose the servers randomly 👍🏻"
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
    users = load_users()
    await update.message.reply_text(f"There are currently {len(users)} users in the bot.")

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    await update.message.reply_text("Please provide the message you would like to broadcast.")
    return BROADCAST_MESSAGE

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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

    if users_to_remove:
        users.difference_update(users_to_remove)
        save_users(users)
        logger.info(f"Removed {len(users_to_remove)} users who blocked the bot.")

    feedback_message = (
        f"Broadcast complete.\n"
        f"Successful: {successful}\n"
        f"Failed: {failed}\n"
        f"Users removed: {len(users_to_remove)}"
    )
    await update.message.reply_text(feedback_message)

    return ConversationHandler.END

# Main function
def main() -> None:
    if BOT_TOKEN is None:
        logger.error("Bot token not set! Please set the BOT_TOKEN environment variable.")
        return

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
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
    main()
