import time
import threading
import asyncio
from getpass import getpass
# import logging

# Clients
from client import MainClient
from auth import RegisterClient, UnregisterClient
from menu import *
from settings import *

def app_thread(xmpp, stop):
    while True:
        # Run XMPP Client
        try:
            xmpp.process(forever=True, timeout=TIMEOUT)
        except:
            print("Error on XMPP client...")
        if stop(): 
            break

        time.sleep(WAIT_TIMEOUT)
    
    xmpp.got_disconnected()
    return

def start_xmpp_app():
    while True:
        try:
            print(main_menu)
            option = int(input('> '))

            if option < 1 or option > 4:
                print("Choose a valid option")
                continue
            break
        except:
            print("Choose a valid option")
            continue

    # OPTION: Register
    if option == 1:
        jid = input("JID: ")
        password = getpass("Password: ")
        xmpp = RegisterClient(jid, password)
        xmpp.connect()
        xmpp.process(forever=False)

    # OPTION: Login
    elif option == 2:
        jid = input("JID: ")
        password = getpass("Password: ")
        status = ""

        while True:
            status_option = 0
            status_message = ""
            print("Set as available? (y/n)? ")
            stat_opt = input('> ')
            
            if stat_opt.lower() == 'y' or stat_opt.lower() == "yes":
                status = AVAILABLE
                status_message = AVAILABLE
                break
            
            try:
                print(status_menu)
                status_option = int(input('> '))
                
                if status_option < 1 or status_option > 4:
                    print("Choose a valid option")
                    continue

                status_message = input("Add a status message: ")
            except:
                print("Choose a valid option")
                continue
            
            status = STATUS_OPTIONS[status_option - 1]
            break
        
        xmpp = MainClient(jid, password, status, status_message)
        xmpp.connect()

        # Threading options
        stop_threads = False
        xmpp_app_thread = threading.Thread(target = app_thread, args=(xmpp, lambda : stop_threads,))
        xmpp_app_thread.start()

        time.sleep(TIMEOUT)

        # Timeout connection
        if xmpp.is_client_offline:
            time.sleep(TIMEOUT - 1)
            if xmpp.is_client_offline:
                print("Can't connect to OpenFire server, try again.\n")
                stop_threads = True
                xmpp_app_thread.join()
                return

        # On App Start
        while True:
            try:
                print(secondary_menu)
                secondary_option = int(input('> '))

                # Check option is in range
                if secondary_option < 1 or secondary_option > 7:
                    print("Choose a valid option")
                    continue
            except:
                print("Choose a valid option")
                continue
            
            # SECONDARY OPTION: Show private messages
            if secondary_option == 1:
                if len(xmpp.messages.keys()) == 0:
                    print("Your inbox is empty...")
                    continue
                
                print("Choose one of the following chats:")

                order = 1
                for key in xmpp.messages.keys():
                    print(f"{order}. Chat with {key}")
                    order += 1

                # User select conversation
                try:
                    chat_idx = int(input("> "))
                except:
                    print("Choose a valid option")
                    continue
                
                if chat_idx < 1 or chat_idx > len(xmpp.messages.keys()):
                    print("Choose a valid option")
                else:
                    # Get user and messages
                    recipient = list(xmpp.messages.keys())[chat_idx - 1]
                    messages_sent = xmpp.messages[recipient]["messages"]
                    xmpp.last_chat_with = recipient

                    xmpp.pm_send_state_message(f"{recipient}@{DEFAULT_DOMAIN}", CHAT_STATE_ACTIVE)

                    print(f"\n--------- Chat with {recipient} ---------")
                    print("* write and press enter to respond (-q to quit) *")

                    for message in messages_sent:
                        print(message)

                    while True:
                        message_body = input('--> ')

                        # Excape reserved word
                        if message_body == '-q':
                            xmpp.pm_send_state_message(f"{recipient}@{DEFAULT_DOMAIN}", CHAT_STATE_PAUSED)
                            break
                        elif '-f ' in message_body:
                            filename = message_body.split()[1]
                            xmpp.file_sender(recipient, filename)
                        else:
                            # Send Response  
                            xmpp.direct_message(f"{recipient}@{DEFAULT_DOMAIN}", message_body)

                    xmpp.current_chat_with = None

            # SECONDARY OPTION: Send private message
            elif secondary_option == 2:
                message_to = input("To: ")
                message_body = input("Message: ")
                xmpp.direct_message(message_to, message_body)
            
            # SECONDARY OPTION: Add contact
            elif secondary_option == 3:
                message_to = input("Name: ")
                xmpp.send_contact_subscription(message_to)
            
            # SECONDARY OPTION: Show contacts info
            elif secondary_option == 4:
                print("\n ----------- CONTACTS ----------- ")
                xmpp.show_contacts()

            # SECONDARY OPTION: Room options
            elif secondary_option == 5:
                while True:
                    try:
                        print(room_menu)
                        room_option = int(input('> '))

                        # Check option is in range
                        if room_option < 1 or room_option > 4:
                            print("Choose a valid option")
                            continue

                        break
                    except:
                        room_option = 4
                        break
                
                # Go Back (default option)
                if room_option == 4:
                    continue
                
                # ROOM OPTION: Show rooms 
                elif room_option == 3:
                    xmpp.muc_discover_rooms()
                    continue
                
                # Join or create room
                room = input("Room: ")
                username = input("Username: ")

                # ROOM OPTION: Create new room
                if room_option == 2:
                    asyncio.run(xmpp.muc_create_room(room, username))
                
                # ROOM OPTION: Join room 
                elif room_option == 1:
                    xmpp.muc_join(room, username)

                print(f"\n--------- Group Chat @ {room} ---------")
                print("* write and press enter to respond (-q to quit) *")

                while True:
                    try:
                        message_body = input('--> ')
                        if message_body == '-q':
                            break

                        xmpp.muc_send_message(message_body)
                    except:
                        continue
                
                # Leave room on exit!
                xmpp.muc_exit_room()

            # SECONDARY OPTION: Send File
            elif secondary_option == 6:
                # TODO: Send Files
                print("Not implemented yet!")
                break

            # SECONDARY OPTION: Logout
            elif secondary_option == 7:
                stop_threads = True
                xmpp_app_thread.join()
                break

    # OPTION: Remove account
    elif option == 3:
        jid = input("JID: ")
        password = getpass("Password: ")
        xmpp = UnregisterClient(jid, password)
        xmpp.connect()
        xmpp.process(forever=False)

    # Exit
    elif option == 4:
        return


# logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')
start_xmpp_app()
exit(1)
