import os
import datetime
import ctypes
from sys import exit
from colorama import Fore
from license.verify.verify_license import LicenseVerifier

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
