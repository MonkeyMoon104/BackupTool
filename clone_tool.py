import discord
import asyncio
import json
import os
from discord.ext import commands
import logging
from pystyle import Write, Colors
from colorama import init, Fore, Style
import ratelimiter
import verify_license
from ratelimiter import AsyncRateLimiter, safe_create
from verify_license import LicenseVerifier
import datetime
import ctypes
from sys import exit
import time
import sys

def validate_license():
    license_file = "licensekey.txt"
    bot_token = ""
    channel_id = ""
    verifier = LicenseVerifier(bot_token, channel_id)

    def set_console_title(title):
        if os.name == 'nt':
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        else:
            print(f"\33]0;{title}\a", end='', flush=True)

    def ask_for_license():
        license_key = input("🔑 Enter your license key: ").strip()
        if verifier.verify_license(license_key):
            with open(license_file, "w") as f:
                f.write(license_key)
            return license_key
        else:
            print("🔒 Access denied. License invalid.")
            exit()

    if not os.path.exists(license_file):
        print(f"[{Fore.YELLOW}!{Fore.RESET}] No licensekey.txt file found.")
        license_key = None
        while not license_key:
            license_key = ask_for_license()
    else:
        with open(license_file, "r") as f:
            license_key = f.read().strip()
        if not verifier.verify_license(license_key):
            print(f"[{Fore.RED}-{Fore.RESET}] ❌ Invalid or expired license in licensekey.txt file\nIt will be deleted and a new one requested, program exiting.")
            os.remove(license_file)
            license_key = None
            exit()

    expiry_timestamp = verifier.get_license_expiry(license_key)
    if expiry_timestamp:
        remaining_time = expiry_timestamp - datetime.datetime.utcnow().timestamp()
        days, seconds = divmod(int(remaining_time), 86400)
        hours, minutes = divmod(seconds, 3600)
        title = f"{license_key[:8]}... | Expires in: {days}d {hours}h"
        set_console_title(title)
    else:
        set_console_title(f"{license_key[:8]}...")

    print(f"[{Fore.GREEN}+{Fore.RESET}] 🔓 Access granted with valid license.")


validate_license()

init(autoreset=True)

last_command_time = time.time()
import_watching = False 

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

user_action = None
user_token = None

def choose_action_before_start():
    global user_action
    show_title()
    while True:
        action = input(f"\n[{Fore.GREEN}>{Fore.RESET}] 👉 Do you want to import a backup (I), create one (C), or list existing backups (L)? (I/C/L): ").strip().lower()
        if action in ['i', 'c', 'l']:
            user_action = action
            break
        else:
            logging.error(f"[{Fore.RED}-{Fore.RESET}] ❌ Invalid option. Try again.")

def clear():
    os.system("cls" if os.name == "nt" else "clear")


def show_title():
    clear()
    Write.Print(r"""

.------..------..------..------..------..------.     .------..------..------..------.
|B.--. ||A.--. ||C.--. ||K.--. ||U.--. ||P.--. |.-.  |T.--. ||O.--. ||O.--. ||L.--. |
| :(): || (\/) || :/\: || :/\: || (\/) || :/\: ((5)) | :/\: || :/\: || :/\: || :/\: |
| ()() || :\/: || :\/: || :\/: || :\/: || (__) |'-.-.| (__) || :\/: || :\/: || (__) |
| '--'B|| '--'A|| '--'C|| '--'K|| '--'U|| '--'P| ((1)) '--'T|| '--'O|| '--'O|| '--'L|
`------'`------'`------'`------'`------'`------'  '-'`------'`------'`------'`------'

""", Colors.green_to_white, interval=0.000)

export_data = {}

def check_backup_folder():
    if not os.path.exists("backups"):
        os.makedirs("backups")
        logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 📁 'backups' folder created.")
    else:
        logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 📁 'backups' folder found.")

def get_existing_backups():
    if not os.path.exists("backups"):
        os.makedirs("backups")
        logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 📁 'backups' folder created.")
    backups = []
    for filename in os.listdir("backups"):
        if filename.endswith(".json"):
            with open(f"backups/{filename}", "r", encoding="utf-8") as f:
                data = json.load(f)
                server_id = filename.replace(".json", "")
                name = data.get("custom_name", data.get("server_name", server_id))
                backups.append((name, server_id))
    return backups

def save_backup(server_id, data, custom_name=None):
    os.makedirs("backups", exist_ok=True)
    if custom_name:
        data["custom_name"] = custom_name
    else:
        data["custom_name"] = data.get("server_name", server_id)

    filename = f"backups/{server_id}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 💾 Backup saved in '{filename}'")

def list_backups_and_return():
    show_title()
    backups = get_existing_backups()
    if not backups:
        print(f"[{Fore.YELLOW}!{Fore.RESET}] ⚠️ No backups found in the 'backups' folder.")
    else:
        print(f"\n[{Fore.GREEN}+{Fore.RESET}] 📂 Available backups:")
        for i, (name, server_id) in enumerate(backups):
            print(f"[{Fore.GREEN}>{Fore.RESET}] {i + 1}. {name} (ID: {server_id})")
    input(f"\n[{Fore.GREEN}>{Fore.RESET}] 🔁 Press enter to return to the main menu...")
    start_bot()

async def handle_user_choice():
    while True:
        choice = input(f"\n[{Fore.GREEN}>{Fore.RESET}] 👉 Do you want to import a backup (I) or create one (C)? (I/C): ").strip().lower()
        if choice == "i":
            await import_backup()
            break
        elif choice == "c":
            await create_clonation()
            break
        else:
            logging.error(f"[{Fore.RED}-{Fore.RESET}] ❌ Invalid option.")

async def import_backup():
    global import_watching
    import_watching = False
    backups = get_existing_backups()
    if backups:
        print(f"\n[{Fore.GREEN}+{Fore.RESET}] 📂 Backups available:")
        for i, (name, server_id) in enumerate(backups):
            print(f"[{Fore.GREEN}>{Fore.RESET}] {i + 1}. {name} ({server_id})")
        try:
            backup_choice = int(input(f"\n[{Fore.GREEN}>{Fore.RESET}] 👉 Choose a backup to import (number): ")) - 1
        except ValueError:
            logging.error(f"[{Fore.RED}-{Fore.RESET}] ❌ Insert a valid number.")
            return

        if backup_choice < 0 or backup_choice >= len(backups):
            logging.error(f"[{Fore.RED}-{Fore.RESET}] ❌ Invalid option")
            return

        selected_backup_name, selected_backup_id = backups[backup_choice]

        print(f"\n[{Fore.GREEN}+{Fore.RESET}] 🔎 Servers available where to import:")
        for guild in bot.guilds:
            print(f"[{Fore.GREEN}>{Fore.RESET}] {guild.name} (ID: {guild.id})")

        try:
            target_id = int(input(f"\n[{Fore.GREEN}>{Fore.RESET}] 👉 Enter the server ID where you want to import the backup: "))
        except ValueError:
            logging.error(f"[{Fore.RED}-{Fore.RESET}] ❌ Insert a valid ID.")
            return

        target_guild = bot.get_guild(target_id)
        if not target_guild:
            logging.error(f"[{Fore.RED}-{Fore.RESET}] ❌ The bot is not present on the destination server.")
            return

        with open(f"backups/{selected_backup_id}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            export_data.clear()
            export_data.update(data)
            logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 📂 Backup '{selected_backup_name}' loaded.")

        logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 🧹 Removing channels from '{target_guild.name}'")
        for channel in target_guild.channels:
            try:
                await safe_create(channel.delete)
                logging.info(f"[{Fore.GREEN}+{Fore.RESET}] ✅ Channel delete: {channel.name}")
            except Exception as e:
                logging.warning(f"[{Fore.YELLOW}>{Fore.RESET}] ⚠️ Impossible delete the channel {channel.name}: {e}")

        logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 🧹 Removing roles from '{target_guild.name}'")
        for role in reversed(target_guild.roles):
            if role.name != "@everyone":
                try:
                    await safe_create(role.delete)
                    logging.info(f"[{Fore.GREEN}+{Fore.RESET}] ✅ Role delete: {role.name}")
                except Exception as e:
                    logging.warning(f"[{Fore.YELLOW}>{Fore.RESET}] ⚠️ Impossible delete the role {role.name}: {e}")

        role_mapping = {}
        new_roles = []

        for role_data in sorted(export_data["roles"], key=lambda r: r["position"]):
            new_role = await safe_create(
                target_guild.create_role,
                name=role_data["name"],
                permissions=discord.Permissions(role_data["permissions"]),
                color=discord.Color(role_data["color"]),
                hoist=role_data["hoist"],
                mentionable=role_data["mentionable"]
            )
            role_mapping[role_data["id"]] = new_role
            new_roles.append((new_role, role_data["position"]))
            logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 🎭 Role create: {new_role.name} (position: {role_data['position']})")

        try:
            positions = {
                role: pos for role, pos in new_roles
            }
            await safe_create(target_guild.edit_role_positions, positions=positions)
            logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 📌 Position roles restored.")
        except Exception as e:
            logging.warning(f"[{Fore.YELLOW}>{Fore.RESET}] ⚠️ Error restoring role positions: {e}")

        for category in export_data["categories"]:
            new_cat = await safe_create(target_guild.create_category, category["name"])
            logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 📁 Category create: {category['name']}")

            category_overwrites = {}
            for role_id, perms in category.get("overwrites", {}).items():
                role_obj = role_mapping.get(int(role_id))
                if role_obj:
                    allow = discord.Permissions(perms["allow"])
                    deny = discord.Permissions(perms["deny"])
                    category_overwrites[role_obj] = discord.PermissionOverwrite.from_pair(allow, deny)

            await safe_create(new_cat.edit, overwrites=category_overwrites)
            logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 🔒 Permission apply to category: {category['name']}")

            for ch in category["channels"]:
                overwrites = {}
                for role_id, perms in ch.get("overwrites", {}).items():
                    role_obj = role_mapping.get(int(role_id))
                    if role_obj:
                        allow = discord.Permissions(perms["allow"])
                        deny = discord.Permissions(perms["deny"])
                        overwrites[role_obj] = discord.PermissionOverwrite.from_pair(allow, deny)

                if ch["type"] == "text":
                    await safe_create(
                        target_guild.create_text_channel,
                        name=ch["name"],
                        topic=ch["topic"],
                        category=new_cat,
                        nsfw=ch["nsfw"],
                        overwrites=overwrites
                    )
                    logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 💬 Text channel create: {ch['name']}")
                elif ch["type"] == "voice":
                    await safe_create(
                        target_guild.create_voice_channel,
                        name=ch["name"],
                        category=new_cat,
                        user_limit=ch["user_limit"],
                        overwrites=overwrites
                    )
                    logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 🔊 Voice channel create: {ch['name']}")

        for emoji in export_data["emojis"]:
            try:
                async with bot.http._HTTPClient__session.get(emoji["url"]) as resp:
                    if resp.status == 200:
                        img = await resp.read()
                        await safe_create(target_guild.create_custom_emoji, name=emoji["name"], image=img)
                        logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 😄 Emoji create: {emoji['name']}")
            except Exception as e:
                logging.warning(f"[{Fore.YELLOW}>{Fore.RESET}] ⚠️ Error loading emoji {emoji['name']}: {e}")

        logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 🎉 Import completed!")
        import_watching = True
        input(f"[{Fore.GREEN}>{Fore.RESET}] Press to continue... ")
        await shutdown_bot()
    else:
        print(f"\n[{Fore.RED}-{Fore.RESET}] 📂 No backups available:")
        import_watching = True
        input(f"[{Fore.GREEN}>{Fore.RESET}] Press to continue... ")
        await shutdown_bot()

async def create_clonation():
    global import_watching
    import_watching = False
    print(f"\n[{Fore.GREEN}+{Fore.RESET}] 🔎 Server available:")
    for guild in bot.guilds:
        print(f"[{Fore.GREEN}>{Fore.RESET}] {guild.name} (ID: {guild.id})")

    try:
        source_id = int(input(f"\n[{Fore.GREEN}>{Fore.RESET}] 👉 Enter the server ID to clone: "))
    except ValueError:
        logging.error(f"[{Fore.RED}-{Fore.RESET}] ❌ Insert valid ID.")
        return

    source_guild = bot.get_guild(source_id)
    if not source_guild:
        logging.error(f"[{Fore.RED}-{Fore.RESET}]❌ The bot is not present on this server.")
        return

    logging.info(f"[{Fore.GREEN}+{Fore.RESET}] 📥 Export of '{source_guild.name}'")

    export_data.clear()
    export_data["roles"] = []
    export_data["categories"] = []
    export_data["emojis"] = []
    export_data["server_name"] = source_guild.name

    for role in source_guild.roles:
        if role.name != "@everyone":
            export_data["roles"].append({
                "id": role.id,
                "name": role.name,
                "permissions": role.permissions.value,
                "color": role.color.value,
                "hoist": role.hoist,
                "mentionable": role.mentionable,
                "position": role.position
            })

    for category in source_guild.categories:
        cat = {"name": category.name, "channels": [], "overwrites": {}}
        for role, overwrite in category.overwrites.items():
            if isinstance(role, discord.Role):
                cat["overwrites"][str(role.id)] = {
                    "allow": overwrite.pair()[0].value,
                    "deny": overwrite.pair()[1].value
                }
        for channel in category.channels:
            overwrites = {}
            for target, overwrite in channel.overwrites.items():
                if isinstance(target, discord.Role):
                    overwrites[str(target.id)] = {
                        "allow": overwrite.pair()[0].value,
                        "deny": overwrite.pair()[1].value
                    }

            overwrites[str(category.guild.default_role.id)] = {
            "allow": category.overwrites.get(category.guild.default_role, discord.PermissionOverwrite()).pair()[0].value,
            "deny": category.overwrites.get(category.guild.default_role, discord.PermissionOverwrite()).pair()[1].value
            }

            if isinstance(channel, discord.TextChannel):
                cat["channels"].append({
                    "type": "text",
                    "name": channel.name,
                    "topic": channel.topic,
                    "nsfw": channel.nsfw,
                    "overwrites": overwrites
                })
            elif isinstance(channel, discord.VoiceChannel):
                cat["channels"].append({
                    "type": "voice",
                    "name": channel.name,
                    "user_limit": channel.user_limit,
                    "overwrites": overwrites
                })
        export_data["categories"].append(cat)

    for emoji in source_guild.emojis:
        export_data["emojis"].append({
            "name": emoji.name,
            "url": str(emoji.url)
        })

    custom_name = input(f"\n[{Fore.GREEN}>{Fore.RESET}] 👉 Enter a custom name for the backup (enter to use '{source_guild.name}'): ").strip()
    if not custom_name:
        custom_name = source_guild.name

    save_backup(source_id, export_data, custom_name)
    logging.info(f"[{Fore.GREEN}+{Fore.RESET}] ✅ Cloning completed.")
    import_watching = True
    input(f"[{Fore.GREEN}>{Fore.RESET}] Press to continue... ")
    await shutdown_bot()

async def shutdown_bot():
    await main()


async def main():
    show_title()
    await handle_user_choice()

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


@bot.event
async def on_message(message):
    global last_command_time
    last_command_time = time.time()
    await bot.process_commands(message)

@bot.event
async def on_ready():
    logging.info(f"[{Fore.GREEN}+{Fore.RESET}] ✅ Bot connected as {bot.user}")
    bot.loop.create_task(watchdog())
    await asyncio.sleep(1)
    
    if user_action == 'i':
        await import_backup()
    elif user_action == 'c':
        await create_clonation()
    else:
        logging.error(f"[{Fore.RED}-{Fore.RESET}] ❌ No action selected.")
        await bot.close()

def start_bot():
    global user_token
    check_backup_folder()

    choose_action_before_start()

    if user_action == 'l':
        list_backups_and_return()
        return

    user_token = input(f"[{Fore.GREEN}>{Fore.RESET}] 🔐 Enter bot token: ")
    bot.run(user_token)


if __name__ == "__main__":
    start_bot()
