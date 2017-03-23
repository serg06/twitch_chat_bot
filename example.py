# EXAMPLE USAGE

import chatbot
from time import sleep

# Create the bot and kick it off (it runs on another thread)
bot = chatbot.Chatbot('ice_poseidon')
bot.start()

# Add a list of admin chatters so you can control the bot remotely
admin_usernames = ['example_admin']

# Handle incoming messages
while True:
    if bot.has_next_message():
        username, message = bot.next_message()
        print("%s: %s" %(username, message))

        # normal commands
        if message.lower().startswith('!hello'):
            bot.chat("Hello @{}!".format(username))
        elif message.lower().startswith('!bye'):
            bot.chat("Bye @{}!".format(username))

        # admin-only commands
        elif username in admin_usernames:
            # stop the bot until it's manually restarted, as it can't
            #   receive messages while it's stopped
            if message == '!stop':
                bot.stop()
                break
            # restart the bot
            elif message == '!restart':
                bot.stop()
                bot.start()

    else:
        # Wait a bit to not over-work the poor bot
        sleep(0.1)

print("Finished running.")
