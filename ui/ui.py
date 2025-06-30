import os
from pystyle import Write, Colors

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

user_action = None

def choose_action_before_start():
    global user_action
    show_title()
    while True:
        action = input("\n👉 Do you want to import a backup (I), create one (C), or list existing backups (L)? (I/C/L): ").strip().lower()
        if action in ['i', 'c', 'l']:
            user_action = action
            break
        else:
            print("❌ Invalid option. Try again.")
