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

    def message(self, message):
        if message['type'] == CHAT_MESSAGE_TYPE:

            sender = str(message['from'])
            sender = sender[:sender.index("@")]
            body = str(message['body'])
            
            current_message = sender + ": " + body

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