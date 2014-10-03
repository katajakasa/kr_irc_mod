# Requires twisted, unicodecsv
#
# pip install twisted unicodecsv
#

import os,sys
import argparse
import unicodecsv
from cStringIO import StringIO
from twisted.internet import reactor, protocol
from twisted.words.protocols import irc

parser = argparse.ArgumentParser(description='Kryptoradio IRC proxy')
parser.add_argument('channel', type=str, nargs=1, help='IRC channel')
parser.add_argument('netname', type=str, nargs=1, help='IRC network name')
parser.add_argument('address', type=str, nargs=1, help='IRC server address')
parser.add_argument('port', type=int, nargs=1, help='IRC server port')
parser.add_argument('nick', type=str, nargs=1, help='Bot nickname')
args = parser.parse_args()

# Helper variables
nick = args.nick[0]
netname = args.netname[0]
channel = args.channel[0]
port = args.port[0]
address = args.address[0]
sys.stderr.write("Connecting as '"+nick+"' to "+channel+"@"+netname+" / "+address+":"+str(port)+".\n")

def write_row(row):
    f = StringIO()
    w = unicodecsv.writer(f, encoding='utf-8')
    w.writerow(row)
    f.seek(0)
    sys.stdout.write(f.getvalue())
    f.close()

# Bot itself
class KryptoBot(irc.IRCClient):
    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        sys.stderr.write("Connected to "+self.factory.host+':'+str(self.factory.port)+"\n")

    def signedOn(self):
        self.join(self.factory.channel)
        sys.stderr.write("Signed on as "+self.factory.nickname+"\n")

    def joined(self, channel):
        sys.stderr.write("Joined channel "+channel+"\n")

    def userJoined(self, user, channel):
        write_row((2,self.netname,channel,user))

    def userLeft(self, user, channel):
        write_row((3,self.netname,channel,user))

    def privmsg(self, user, channel, msg):
        short_name = user.split('!', 1)[0]
        write_row((1,self.netname,channel,short_name,msg))

# Factory for bots
class KryptoBotFactory(protocol.ClientFactory):
    def __init__(self, channel, nickname, host, port, netname):
        self.channel = channel
        self.nickname = nickname
        self.host = host
        self.port = port
        self.netname = netname

    def buildProtocol(self, addr):
        bot = KryptoBot()
        bot.factory = self
        bot.nickname = self.nickname
        bot.netname = self.netname
        return bot

    def clientConnectionLost(self, connector, reason):
        sys.stderr.write("Connection lost: "+reason+"\n")
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        sys.stderr.write("Connection failed: "+reason+"\n")
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        sys.stderr.write("Could not connect: "+reason+"\n")

# Main
if __name__ == '__main__':
    try:
        botfactory = KryptoBotFactory(channel, nick, address, port, netname)
    except Exception as ex:
        sys.stderr.write(str(ex))
        exit()

    reactor.connectTCP(address, port, botfactory)
    reactor.run()