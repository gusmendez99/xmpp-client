# xmpp-client
Simple XMPP Client using Python & Slixmpp

## Requirements

* Python 3.6+


## Install

1. Clone repo
2. Create a virtualenv: `python -m venv venv` and activate it
3. Open source code and install dependencies with `pip install -r requirements.txt`
4. Run `python main.py`


## Features

This client provides basic features related with chat-application stuff, all throughout a CLI program.

- [x] Register new account.
- [x] Login / Logout.
- [x] Delete account from server.
- [x] Add contact.
- [x] Display contact info.
- [x] Chat 1v1 with any user.
- [x] Room options:
    - [x] Create room.
    - [x] Join an existing room.
    - [x] Send a message to a room.
    - [x] Leave room (auto on leave room chat).
- [x] Send presence message.
- [x] Send/Receive files.
- [x] Send/Receive notifications.


### Updates

- **2021-07-25**: Initial commit.
- **2021-07-02**: Test & OpenFire Setup on local (after connection errors...).
- **2021-07-09**: Slixmpp Test done, starting with final code and refactor.
- **2021-07-12**: Client(s) & Project requirements done
