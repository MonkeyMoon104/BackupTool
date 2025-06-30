import os
import json
import logging
from colorama import Fore

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
    from ui.ui import show_title
    show_title()
    backups = get_existing_backups()
    if not backups:
        print(f"[{Fore.YELLOW}!{Fore.RESET}] ⚠️ No backups found in the 'backups' folder.")
    else:
        print(f"\n[{Fore.GREEN}+{Fore.RESET}] 📂 Available backups:")
        for i, (name, server_id) in enumerate(backups):
            print(f"[{Fore.GREEN}>{Fore.RESET}] {i + 1}. {name} (ID: {server_id})")
    input(f"\n[{Fore.GREEN}>{Fore.RESET}] 🔁 Press enter to return to the main menu...")
    from main.clone_tool import start_bot
    start_bot()
