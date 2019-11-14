from slackbot.bot import Bot
from slackbot.bot import respond_to
from slackbot.bot import listen_to
import re

@respond_to('hi', re.IGNORECASE)
def hi(message):
    message.reply('Greglbot is clean and sober... not high')
    message.react('+1')

@listen_to('look good?')
def help(message):
    message.reply('LGTM')

@listen_to('leader')
def help(message):
    message.reply('Did someone mention the Fearless Leader?')


@listen_to('food')
def help(message):
    message.reply('ralphie hungry...')


@listen_to('eggtart')
def help(message):
    message.reply('eggtarts? 17 no problem')

@listen_to('XP')
def help(message):
    message.reply("That's Fearless Leader to you")


def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
