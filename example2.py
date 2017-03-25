# This is a more complicated example

import chatbot
from time import sleep


def main():
    bot = chatbot.Chatbot('ice_poseidon')
    bot.start()

    # list of bot admins
    bot_admins = ['your_username', 'your_friends_username']

    # Handle incoming messages
    while True:
        if bot.has_next_message():
            username, message = bot.next_message()
            print("%s: %s" %(username, message))

            # Normie commands
            if message.lower().startswith('!pyramid'):
                args = dict(enumerate(message.split(' ')[1:]))
                try:
                    size = int(args.get(0, 3))
                    if size > 6:
                        bot.chat('Limit is 6 @{} cmonBruh'.format(username))
                    elif size > 0:
                        build_pyramid(bot, size)
                except:
                    print("Failed to make pyramid.")

            # Admin-only commands
            if username in bot_admins:
                # Kill the bot until it is manually restarted
                if message == '!stop':
                    bot.stop()
                elif message == '!restart':
                    bot.stop()
                    bot.start()

        else:
            # Wait a bit to not over-work the poor bot
            sleep(0.1)


def build_pyramid(bot, size):
    for i in range(1, size * 2):
        bot.chat('TriHard '*min(i, size*2-i))

if __name__ == "__main__":
    main()
    print('Finished running. Exiting.')
