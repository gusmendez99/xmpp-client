from logging import info
import slixmpp
from settings import *
from slixmpp.exceptions import IqError, IqTimeout

class MainClient(slixmpp.ClientXMPP):

    def __init__(self, jid, password, status, status_message):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        
        # Plugins
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0045') # MUC
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0133') # Service administration
        self.register_plugin('xep_0199') # XMPP Ping
        
        self.jid = jid
        self.username = jid[:jid.index("@")]
        self.status = status
        self.status_message = status_message
        
        # App logic
        self.messages = {}
        self.contacts = {}
        self.active_room = ""
        self.is_room_owner = False
        self.last_chat_with = None
        self.is_client_offline = True
        # Auto authorize & subscribe on subscription received
        self.roster.auto_authorize = True
        self.roster.auto_subscribe = True

        # Event handlers
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("presence_subscribe", self.on_presence_subscription)
        self.add_event_handler("got_online", self.got_online)
        self.add_event_handler("got_offline", self.got_offline)
        self.add_event_handler("disco_info",self.show_info)
        self.add_event_handler("disco_items", self.show_info)
        

    async def start(self, event):
        # Send presence
        self.send_presence(pshow=self.status, pstatus=self.status_message)
        try:
            # Ask for roster
            await self.get_roster()
            print(f"\n Login successfully: {self.jid}")
            self.is_client_offline = False
        except:
            print("Error on login, try again...")
            self.disconnect()

    def send_contact_subscription(self, recipient):
        try:
            # Subscribe
            self.send_presence_subscription(recipient, self.jid)
        except:
            print("ERROR ON SUBSCRIBE")
    
    def message(self, message):
        if message['type'] == CHAT_MESSAGE_TYPE:

            sender = str(message['from'])
            sender = sender[:sender.index("@")]
            body = str(message['body'])
            
            current_message = f"{sender}: {body}"

            if sender in self.messages.keys():
                self.messages[sender]["messages"].append(current_message)
            else:
                self.messages[sender] = {"messages": [current_message]}

            # TODO: Notification, terminal format
            if not self.last_chat_with == sender:
                print(f" NEW MESSAGE FROM  {sender}")
            else:
                # If is a message from last chat, just print it
                print(current_message)

    def direct_message(self, recipient, message = ""):
        self.send_message(
            mto = recipient, 
            mbody = message, 
            mtype = CHAT_MESSAGE_TYPE, 
            mfrom = self.jid
        )

        recipient = recipient[:recipient.index("@")]
        sender = self.jid[:self.jid.index("@")]

        # Final message
        current_message = f"{sender}: {message}"

        if recipient in self.messages.keys():
            self.messages[recipient]["messages"].append(current_message)
        else:
            self.messages[recipient] = {"messages":[current_message]}
    
    def on_presence_subscription(self, new_presence):
        roster = self.roster[new_presence['to']]
        item = self.roster[new_presence['to']][new_presence['from']]
        try_auto_sub = False

        if item[WHITELIST_STATUS]:
            item.authorize()
            if roster.auto_subscribe:
                try_auto_sub = True

        # Auto authorize
        elif roster.auto_authorize:
            item.authorize()
            if roster.auto_subscribe:
                try_auto_sub = True

        elif roster.auto_authorize == False:
            item.unauthorize()

        # Subscribe
        if try_auto_sub:
            item.subscribe()

    def got_online(self, event):
        sender = str(event['from'])
        if MUC_DEFAULT_SENDER in sender:
            return

        sender = sender[:sender.index("@")]

        event_show = ""
        event_status = ""

        # Try getting the show and status
        try:
            event_show = str(event['show'])
            event_status = str(event['status'])
        except:
            event_show = AVAILABLE
            event_status = AVAILABLE

        self.contacts[sender] = {
            "from": sender, 
            "show": event_show, 
            "status": event_status
        }

        # TODO: Notification, terminal format
        if not sender == self.jid[:self.jid.index("@")]:
            print(f"{sender} IS ONLINE NOW. ({event_status})")

    def got_offline(self, event):
        sender = str(event['from'])
        if MUC_DEFAULT_SENDER in sender:
            return

        sender = sender[:sender.index("@")]
        self.contacts[sender]["show"] = UNAVAILABLE
        self.contacts[sender]["status"] = UNAVAILABLE

        # TODO: Notification, terminal format
        print(f"{sender} IS NOW OFFLINE")

    def got_disconnected(self):
        new_presence = self.Presence()
        new_presence['type'] = UNAVAILABLE
        # Send stanza
        new_presence.send()

    def show_info(self, iq):
        if str(iq['type']) == 'result' \
            and MUC_DEFAULT_SENDER in str(iq['from']):
            
            order = 1
            text_formatted = ""
            
            print("\n Rooms: ")
            for char in str(iq):
                if len(text_formatted) > 7 and char == '/':
                    print(f"{str(order)}. {text_formatted}")
                    text_formatted = ""
                    order += 1
                    continue

                elif "jid=" in text_formatted:
                    text_formatted += char
                    continue
                
                if char in ('j', 'i', 'd', '='):
                    text_formatted += char
                    if char == 'j':
                        text_formatted = char
                else:
                    # Reset
                    text_formatted = ''

    def show_contacts(self):
        self.get_roster()
        contacts = self.roster[self.jid]

        for contact in contacts.keys():
            if contact != self.jid:
                # Print contact info
                print(f"Contact: {contact}")
                username = contact[:str(contact).index("@")]

                if username in self.contacts.keys():
                    info = self.contacts[username]['show']
                    status = self.contacts[username]['status']
                    print(f" INFO: { info }")
                    print(f" STATUS: { status }")

                else:
                    print(f" INFO: { UNAVAILABLE }")
                    print(f" STATUS: { UNAVAILABLE }")

                # Print general info
                print(f" - GROUPS: { contacts[username]['groups'] }")
                print(f" - SUBS: { contacts[username]['subscription'] }")
            
    