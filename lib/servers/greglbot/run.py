from slackbot.bot import Bot, respond_to, listen_to, default_reply

import re
import urllib2
import wolframalpha
import labrad

try:
    cxn = labrad.connect(name = 'Greglbot')
    wmcxn = labrad.connect('10.97.112.2', name = 'Greglbot', password = 'lab')
    camcxn = labrad.connect('10.97.112.46', name = 'Greglbot', password = 'lab')
    ev = cxn.evpump
    wavemeter = wmcxn.multiplexerserver
    ixon = camcxn.andor_server
except:
    pass

@respond_to('hi', re.IGNORECASE)
def hi(message):
    message.reply('Greglbot is clean and sober... not high')
    message.react('+1')

@listen_to('look good?', re.IGNORECASE)
def help(message):
    message.reply('LGTM')

@listen_to('leader', re.IGNORECASE)
def help(message):
    message.reply('Did someone mention the Fearless Leader?')

@listen_to('food', re.IGNORECASE)
def help(message):
    message.reply('ralphie hungry...')

@listen_to('eggtart', re.IGNORECASE)
def help(message):
    message.reply('eggtarts? 17 no problem')

@listen_to('XP', re.IGNORECASE)
def help(message):
    message.reply("That's Fearless Leader to you")

@listen_to('temperature', re.IGNORECASE)
def help(message):
    response = urllib2.urlopen('http://10.97.112.15/data')
    html = response.read()
    templist = html.split('|')
    duckbergtemp = templist[1]
    acinlettemp = templist[7]
    moleculestemp = templist[10]
    message.reply('The current lab temperatures are: \n Duckberg - ' + str(duckbergtemp) + '\n AC inlet - ' + str(acinlettemp) + '\n Molecules Table - ' + str(moleculestemp))

@listen_to('Qsim status', re.IGNORECASE)
def help(message):
	MLshutter = ev.get_shutter_status()
        diode_current = ev.get_current()
	wmoutput = wavemeter.get_wlm_output()
        camshutter = ixon.get_shutter_mode()
	emgain = ixon.get_emccd_gain()
	message.reply('*Qsim Xion Camera Status: *')

        message.reply('Qsim Xion shutter ' + camshutter)
	message.reply('Qsim emccd gain:' + str(emgain))

	message.reply('*Qsim Wavemeter Status: *')
	if wmoutput:
            message.reply('Wavemeter is ON')
        else:
            message.reply('Wavemeter is OFF')

	message.reply('*Qsim Mode Locked Laser Status: *')

        if MLshutter:
            message.reply('Mode Locked Shutter Open')
        else:
            message.reply('Mode Locked Shutter Closed')

        if diode_current['A'] <= 0.1:
            message.reply('Mode Locked Laser off')
        else:
            message.reply('Mode Locked Laser ON: diode current ' + str(diode_current['A']) + 'A')






@respond_to('(.*)')
def help(message, query):
    message.reply('gregl thinking...')
    client = wolframalpha.Client('T2P2LH-AUTR4AXREV')
    try:
        res = client.query(query)
        ans = next(res.results).text
        message.reply(ans)
    except:
        message.reply('Gregl too tired for silly questions')

def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
