import slixmpp
import time
import asyncio
from settings import *
from slixmpp.exceptions import IqError, IqTimeout
import xml.etree.ElementTree as ET

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
        self.register_plugin('xep_0363') # Files
        self.register_plugin('xep_0085') # Notifications
        
        self.local_jid = jid
        self.nickname = jid[:jid.index("@")]
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
        self.outter_presences = asyncio.Event()

        # Event handlers
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("presence_subscribe", self._handle_new_subscription)
        self.add_event_handler("got_online", self.got_online)
        self.add_event_handler("got_offline", self.got_offline)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("disco_info",self.show_info)
        self.add_event_handler("disco_items", self.show_info)
        

    async def start(self, event):
        # Send presence
        self.send_presence(pshow=self.status, pstatus=self.status_message)
        
        try:
            # Ask for roster
            await self.get_roster()
            print(f"\n Login successfully: {self.local_jid}")
            self.is_client_offline = False
        except:
            print("Error on login, try again...")
            self.disconnect()

    """
    Add contact
    """
    def send_contact_subscription(self, recipient):
        try:
            # Subscribe
            self.send_presence_subscription(recipient, self.local_jid)
            print("Contact added: ", recipient)
        except:
            print("ERROR ON SUBSCRIBE")
    
    """
    Messages
    """
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
            mfrom = self.local_jid
        )

        recipient = recipient[:recipient.index("@")]
        sender = self.local_jid[:self.local_jid.index("@")]

        # Final message
        current_message = f"{sender}: {message}"

        if recipient in self.messages.keys():
            self.messages[recipient]["messages"].append(current_message)
        else:
            self.messages[recipient] = {"messages":[current_message]}
        
        print("Message sent")

    def muc_message(self, message = ""):
        nickname = str(message['mucnick'])
        body = str(message['body'])

        is_same_sender = nickname != self.nickname
        is_valid_room = self.active_room in str(message['from'])
        current_message = f"{nickname}: {body}"

        if is_same_sender and is_valid_room:
            print(current_message)

    def muc_send_message(self, message):
        self.send_message(mto=self.active_room, mbody=message, mtype=ROOM_MESSAGE_TYPE)

    """
    Rooms
    """
    async def muc_create_room(self, room, nickname):
        self.active_room = room
        self.nickname = nickname
        self.is_room_owner = True
        
        # Create
        self['xep_0045'].join_muc(room, nickname)
        self['xep_0045'].set_affiliation(room, self.boundjid, affiliation='owner')

        # Event handlers
        self.add_event_handler(f"muc::{self.active_room}::got_online", self.muc_on_join)
        self.add_event_handler(f"muc::{self.active_room}::got_offline", self.muc_on_left)

        try:
            query = ET.Element('{http://jabber.org/protocol/muc#owner}query')
            elem = ET.Element('{jabber:x:data}x', type='submit')
            query.append(elem)

            iq = self.make_iq_set(query)
            iq['to'] = room
            iq['from'] = self.boundjid
            iq.send()
        except:
            print("Error on create room")

    def muc_discover_rooms(self):
        try:
            self['xep_0030'].get_items(jid = f"conference.{DEFAULT_DOMAIN}")
        except (IqError, IqTimeout):
            print("Error on discovering rooms")

    def muc_exit_room(self, message = ''):
        self['xep_0045'].leave_muc(self.active_room, self.nickname, msg=message)
        # Reset
        self.is_room_owner = False
        self.active_room = None
        self.nickname = ''

    def muc_join(self, room, nickname):
        # Set local atributes for room
        self.active_room = room
        self.nickname = nickname

        # Join
        self['xep_0045'].join_muc(room, nickname, wait=True, maxhistory=False)
        self.add_event_handler(f"muc::{self.active_room}::got_online", self.muc_on_join)
        self.add_event_handler(f"muc::{self.active_room}::got_offline", self.muc_on_left)


    def muc_on_join(self, presence):
        if presence['muc']['nick'] == self.nickname:
            print("Joined to your own room!")
        
        else:
            nickname = str(presence['muc']['nick'])
            # Affiliation if its owner
            if self.is_room_owner:
                self['xep_0045'].set_affiliation(self.active_room, nick=nickname, affiliation=AFFILIATION_TYPE)
            # TODO: Notification, terminal format
            print(f"{nickname} has arrived to the room!")
        

    def muc_on_left(self, presence):
        if presence['muc']['nick'] != self.nickname:
            nickname = presence['muc']['nick']
            # TODO: Notification, terminal format
            print(f"{nickname} left the room!")

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
        if not sender == self.local_jid[:self.local_jid.index("@")]:
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

    """
    Show info
    """
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

    """
    Contacts
    """
    def show_contacts(self):
        self.get_roster()
        contacts = self.roster[self.local_jid]

        if(len(contacts.keys()) == 0):
            print("No contacts yet...")

        for contact in contacts.keys():
            if contact != self.local_jid:
                # Print contact info
                print(f"Contact: {contact}")
                nickname = contact

                if nickname in self.contacts.keys():
                    info = self.contacts[nickname]['show']
                    status = self.contacts[nickname]['status']
                    print(f" INFO: { info }")
                    print(f" STATUS: { status }")

                else:
                    print(f" INFO: { UNAVAILABLE }")
                    print(f" STATUS: { UNAVAILABLE }")

                # Print general info
                print(f" - GROUPS: { contacts[nickname]['groups'] }")
                print(f" - SUBS: { contacts[nickname]['subscription'] }")
            
    """
    Presence and status
    """
    def _handle_new_subscription(self, new_presence):
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
    