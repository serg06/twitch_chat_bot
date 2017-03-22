# EXAMPLE USAGE

import chatbot
from time import sleep

# Create the bot and kick it off (it runs on another thread)
bot = chatbot.Chatbot('ice_poseidon')
bot.start()

# Handle incoming messages
while True:
    if bot.has_next_message():
        username, message = bot.next_message()
        print("%s: %s" %(username, message))
        if message.lower().startswith("!hello"):
            bot.chat("@{username} Hello!".format(username=username))
    else:
        sleep(0.01)
