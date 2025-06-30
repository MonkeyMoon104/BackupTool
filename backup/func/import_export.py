import json
import logging
import asyncio
from colorama import Fore
from ratelimit.ratelimiter import safe_create
import discord

export_data = {}
import_watching = False

async def import_backup(bot):
    global import_watching, export_data
    import_watching = False
    from backup.manager.backup_manager import get_existing_backups
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
                mentionable=role_data["mentionable"],
                reason="Backup import"
            )
            role_mapping[role_data["id"]] = new_role
            new_roles.append(new_role)
            logging.info(f"[{Fore.GREEN}+{Fore.RESET}] ✅ Role created: {new_role.name}")

        export_data["role_mapping"] = role_mapping

        import_watching = True
        print(f"[{Fore.GREEN}+{Fore.RESET}] ✅ Backup import started...")
    else:
        logging.info(f"[{Fore.YELLOW}!{Fore.RESET}] ⚠️ No backups available to import.")
