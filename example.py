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

        # commands people can execute
        if message.lower().startswith('!hello'):
            bot.chat("Hello @{}!".format(username))
        if message.lower().startswith('!bye'):
            bot.chat("Bye @{}!".format(username))
    else:
        # Wait a bit to not over-work the poor bot
        sleep(0.1)

print("Finished running.")
