# Term colors
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
ENDC = '\033[0m'

main_menu = f"""
    {HEADER}|=================| AUTH MENU |=================|{ENDC}
    1. Register
    2. Login
    3. Remove Account
    4. Exit
    {HEADER}|===============================================|{ENDC}
"""

secondary_menu = f"""
    {HEADER}|=================| APP MENU |=================|{ENDC}
    1. Show PM
    2. Send PM
    3. Add contact
    4. Show contacts
    5. Room Chats
    6. Send File
    7. Logout
    {HEADER}|==============================================|{ENDC}
"""

status_menu =  f"""
    {HEADER}|=================| STATUS MENU |=================|{ENDC}
    1. Available
    2. Unavailable
    3. AFK
    4. In a meeting
    {HEADER}|=================================================|{ENDC}
"""

room_menu = f"""
    {HEADER}|=================| ROOM MENU |=================|{ENDC}
    1. Join room
    2. Create room
    3. Show rooms
    4. Go Back
    {HEADER}|==============================================|{ENDC}
"""