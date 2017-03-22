# Created using http://www.instructables.com/id/Twitchtv-Moderator-Bot/?ALLSTEPS

import logging
import json
import socket
import re
from threading import Thread
from queue import Queue
from collections import deque
from time import sleep
from typing import Tuple

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
config_file = 'config.json'


# Chatbot config
class Config:
    host = 'irc.twitch.tv'
    port = 6667
    channel = None
    username = None
    oauth = None

    def __init__(self):
        try:
            config = json.load(open(config_file, 'r'))
        except Exception:
            logger.error('Unable to open config file %s. Did you follow instructions in README.md?' %config_file)

        try:
            self.username = config['username']
            self.oauth = config['oauth_token']
        except KeyError as err:
            logger.error('Could not extract %s from config file %s.' %(err.message, config_file))

    def __str__(self):
        return 'host: {host}\n' \
               'port: {port}\n' \
               'channel: {channel}\n' \
               'username: {username}\n' \
               'oauth: {oauth}'\
            .format(host=self.host,
                    port=self.port,
                    channel=self.channel,
                    username=self.username,
                    oauth=self.oauth)


class Chatbot:
    config = Config()
    message_re = re.compile(r'^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :')

    # Queue for incoming messages
    incoming_messages = Queue()

    # Queue for messages to send
    chat_queue = Queue()

    # Last 3 sent messages
    chat_history = deque(maxlen=3)

    def __init__(self, channel, username=None, oauth=None):
        self.config.channel = channel

        if username is not None and oauth is not None:
            self.config.username = username
            self.config.oauth = oauth

        self.socket = socket.socket()
        self.socket.connect((self.config.host, self.config.port))
        self._send('PASS {}'.format(self.config.oauth))
        self._send('NICK {}'.format(self.config.username))
        self._send('JOIN #{}'.format(self.config.channel))

        logger.debug('Chatbot initialized. Config: \n%s' %self.config)

    # Start self multi-threadedly
    def start(self):
        try:
            # ("Chatbot {} in channel {}".format(self.config.username, self.config.channel))
            t = Thread(target=self._run, name="Chatbot {} in channel {}".format(self.config.username, self.config.channel))
            t.daemon = True
            t.start()
        except:
            logger.error("Unable to start bot thread")

    # Manually run the chatbot
    def _run(self):
        while True:
            response = self.socket.recv(8192).decode('utf-8')
            if response == 'PING :tmi.twitch.tv\r\n':
                self.socket.send('PONG :tmi.twitch.tv\r\n'.encode('utf-8'))
            else:
                for line in response.split('\r\n'):
                    try:
                        username = re.search(r'\w+', line).group(0) # return the entire match
                        message = self.message_re.sub('', line)
                    except AttributeError:
                        pass
                    else:
                        self.incoming_messages.put((username, message))
                if not self.chat_queue.empty():
                    self._chat(self.chat_queue.get())
            # Sleep just long enough to prevent being 8-hour IP banned. That's 20 messages per second.
            # TODO: Implement queue or some shit to make this more efficient.
            sleep(1/(20/30))

    # Manually send socket message
    def _send(self, msg: str):
        logger.debug('SEND: %s' %msg)
        self.socket.send('{}\r\n'.format(msg).encode('utf-8'))

    # Manually send chat message
    def _chat(self, msg):
        # Prevent duplicate messages
        msg = msg[0:100 - 1 - len(self.chat_history)] + ' '
        while msg in self.chat_history:
            msg += '-'
        self.chat_history.append(msg)
        self._send('PRIVMSG #{} :{}'.format(self.config.channel, msg))

    # Check if bot has new messages to process
    def has_next_message(self):
        return not self.incoming_messages.empty()

    # Pop message
    def next_message(self) -> Tuple[str, str]:
        return self.incoming_messages.get()

    # Send chat message when ready
    def chat(self, msg):
        self.chat_queue.put(msg)
