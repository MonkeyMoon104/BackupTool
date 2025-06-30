import asyncio
import logging
import time
import sys
import os
from colorama import init, Fore
from discord.ext import commands
import discord
from license.manager.license_manager import validate_license
from ui.ui import choose_action_before_start, show_title, clear
from backup.manager.backup_manager import check_backup_folder, list_backups_and_return
from backup.func.import_export import import_backup, create_clonation, shutdown_bot
from ratelimit.ratelimiter import safe_create

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

init(autoreset=True)

last_command_time = time.time()
import_watching = False

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

user_action = None
user_token = None

def start_bot():
    global user_token, user_action
    check_backup_folder()
    choose_action_before_start()
    if user_action == 'l':
        list_backups_and_return()
        return

    user_token = input(f"[{Fore.GREEN}>{Fore.RESET}] 🔐 Enter bot token: ")
    bot.run(user_token)

@bot.event
async def on_message(message):
    global last_command_time
    last_command_time = time.time()
    await bot.process_commands(message)

@bot.event
async def on_ready():
    global user_action
    logging.info(f"[{Fore.GREEN}+{Fore.RESET}] ✅ Bot connected as {bot.user}")
    bot.loop.create_task(watchdog())
    await asyncio.sleep(1)
    
    if user_action == 'i':
        await import_backup(bot)
    elif user_action == 'c':
        await create_clonation(bot)
    else:
        logging.error(f"[{Fore.RED}-{Fore.RESET}] ❌ No action selected.")
        await bot.close()

async def watchdog():
    global last_command_time, import_watching
    while True:
        await asyncio.sleep(5)
        if import_watching and time.time() - last_command_time > 10:
            print("❗ Inactivity detected. Restarting the bot...")
            restart_bot()

def restart_bot():
    python = sys.executable
    os.execl(python, python, *sys.argv)

if __name__ == "__main__":
    validate_license()
    start_bot()
