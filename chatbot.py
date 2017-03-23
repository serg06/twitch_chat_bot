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
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
one_second = timedelta(seconds=1)
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
        except:
            logger.error('Unable to open config file %s. Did you follow instructions in README.md?' % config_file)

        try:
            self.username = config['username']
            self.oauth = config['oauth_token']
        except KeyError as err:
            logger.error('Could not extract %s from config file %s.' % (err.message, config_file))

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


# history of max. last 20 sent messages in max. last 30 seconds
class ChatHistory(deque):
    class ChatMessage:
        def __init__(self, msg: str):
            self.message = msg
            self.timestamp = datetime.now()

    now = datetime.now()
    thirty_seconds = one_second*30

    def __init__(self):
        super().__init__(maxlen=20)

    def append(self, msg):
        super().append(self.ChatMessage(msg))

    # Check if self is full
    def full(self):
        # If we haven't sent 20 messages yet, we're clearly not full
        if len(self) < self.maxlen:
            return False
        # Otherwise, we can update the full function to check if our messages are older than 30 seconds
        else:
            self.full = self._full
            return self.full()

    # Check if self is full of messages no older than 30 seconds
    def _full(self):
        # Get oldest message
        thirty_seconds_ago = datetime.now() - self.thirty_seconds
        msg = self.popleft()

        # If it's less than thirty seconds old, put it back and let 'em know we're still full
        if msg.timestamp > thirty_seconds_ago:
            self.appendleft(msg)
            return True

        return False


class Chatbot:
    config = Config()
    message_re = re.compile(r'^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :')
    running_thread = None

    # Whether to stop the running thread
    should_stop = False

    # Queue for incoming messages
    incoming_messages = Queue()

    # Queue for messages to send
    chat_queue = Queue()

    # Last 20 sent messages in last 30 seconds
    chat_history = ChatHistory()

    # Last 3 sent messages
    last_3_messages = deque(maxlen=3)

    # Last sent message time
    last_sent = datetime.now()

    # Minimum delay between messages
    min_delay = one_second * 1.1

    # Create socket connection to given channel
    def __init__(self, channel, username=None, oauth=None):
        self.config.channel = channel

        if username is not None and oauth is not None:
            self.config.username = username
            self.config.oauth = oauth

        self.socket = socket.socket()
        self.socket.connect((self.config.host, self.config.port))
        self.socket.setblocking(False)

        self._send('PASS {}'.format(self.config.oauth))
        self._send('NICK {}'.format(self.config.username))
        self._send('JOIN #{}'.format(self.config.channel))

        logger.debug('Chatbot initialized. Config: \n%s' % self.config)

    # Run on another thread.
    def start(self):
        if self.running_thread is not None:
            logger.error('Fam this guy is already started. If you want another chatbot, create another chatbot.')

        try:
            self.running_thread = Thread(target=self._run, name="Chatbot {} in channel {}".format(self.config.username, self.config.channel))
            self.running_thread.daemon = True
            self.running_thread.start()
        except:
            logger.error("Unable to start bot running thread")

    # Stop the bot's thread.
    def stop(self):
        if not self.running_thread:
            logger.error('Who you tryina stop? I\'m not running!')
        self.should_stop = True
        self.running_thread.join()
        self.running_thread = None

    # Run the chatbot on this thread
    def _run(self):
        self.should_stop = False
        while not self.should_stop:
            # Wait a bit each loop
            sleep(0.1)

            # Receive response if there is one
            response = None
            try:
                response = self.socket.recv(8192).decode('utf-8')
            except BlockingIOError:
                pass

            # Handle response if exists
            if response is not None:
                # Respond to ping if needed
                if response == 'PING :tmi.twitch.tv\r\n':
                    self._send('PONG :tmi.twitch.tv\r\n')

                for line in response.split('\r\n'):
                    try:
                        username = re.search(r'\w+', line).group(0) # return the entire match
                        message = self.message_re.sub('', line)
                    except AttributeError:
                        pass
                    else:
                        self.incoming_messages.put((username, message))

            # Send any queued chats
            if self.last_sent + self.min_delay <= datetime.now() and \
                    not self.chat_queue.empty() and \
                    not self.chat_history.full():
                self._chat(self.chat_queue.get())
                self.last_sent = datetime.now()

        # Exit this thread
        exit()

    # Manually send socket message
    def _send(self, msg: str):
        logger.debug('SEND: %s' % msg)
        self.socket.send('{}\r\n'.format(msg).encode('utf-8'))

    # Manually send chat message
    def _chat(self, msg: str):
        # Prevent duplicate messages
        msg = msg[0:100 - 1 - len(self.last_3_messages)] + ' '
        while msg in self.last_3_messages:
            msg += '-'
        self.last_3_messages.append(msg)
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
        logger.debug('QUEUE: %s' % msg)
        self.chat_queue.put(msg)
