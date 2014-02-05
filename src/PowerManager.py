#!/usr/bin/python


#Power Management Daemon
#Description: Communicates with the Switch and ThinClients for shutdown 
#requests, immediate shutdown and reduced-power operations.
#Author: Gene Paul Quevedo




import logging, os, signal, re
import time as timer
import ConfigParser

from twisted.internet import reactor, utils, task, defer
from twisted.internet import protocol
from twisted.internet.protocol import DatagramProtocol
from twisted.protocols import basic

from Crypto.Cipher import AES
from datetime import datetime, time, date, timedelta

from ipaddressfinder import IPAddressFinder
from powermodels import Conf, NodeA, NodeB, Switch, ThinClient, Power, MasterTC
from powermodels import ServerState, PowerState, SwitchState

#change on deployment
#from cloudtop.helper.configreader import fillAllDefaults

class IPMISecurity():
    #IPMI passwords are 16 Bytes long.
    def __init__(self):
        self.BlockSize = 16
        self.Padding = '}'
        self.secretKey = 'Pa$sW0rD'
        self.secretFile = '/var/lib/power_daemon/secret'
        self.passPhrase = None
        self.password = None


    def decrypt(self, passphrase, IV, encrypted):
        aes = AES.new(passphrase, AES.MODE_CFB, IV)
        return aes.decrypt(encrypted)   

    def encrypt(self, passphrase, IV, message):
        aes = AES.new(passphrase, AES.MODE_CFB, IV)
        return aes.encrypt(message) 

    def getIPMIPassword(self):
        IPMIpasswdfile = open(self.secretFile)
        IV = IPMIpasswdfile.readline()
        ciphertext = IPMIpasswdfile.readline()
        self.password = self.decrypt( self.secretKey, IV, ciphertext)

    def storeIPMIPassword(self):
        IV = os.urandom(self.BlockSize)
        ciphertext = self.encrypt(self.secretKey , IV, self.password)
        IPMIpasswdfile = open(self.secretFile)
        IPMIpasswdfile.write(IV)
        IPMIpasswdfile.write(ciphertext)
        IPMIpasswdfile.close()
        
#Power Conf class

class Command():
    #switch commands & notifications
    SHUTDOWN_IMMEDIATE = '\x05'
    AC_RESTORED = '\x02'
    
    #thinclient commands & notifications
    SHUTDOWN_CANCEL = '\x07'
    SHUTDOWN_NORMAL = '\x06'
    SHUTDOWN_REQUEST = '\x08'
    REDUCE_POWER = '\x03'
    POSTPONE = '1'

    #from RDP
    UPDATE = '\x0A'

class ServerNotifs():
    #notifications to ThinClients/RDP Server
    NORMAL_SHUTDOWN_START_COUNTDOWN = 0x1100000


#power manager class
class PowerManager(DatagramProtocol):
    #top-level manager class for handling power monitoring and shutdown 
    #singleton design pattern (?)
    def __init__(self):
        self.shutdownDelay = Conf.DEFAULTSCHEDULEDSHUTDOWNWAITTIME
        self.postponeToggle = False

    def _logExitValue(self, exitValue):
        logging.info("exit value of last command:%s" % exitValue)

    def sendIPMICommand(self, value, params):
        logging.debug("now sending IPMI command")  
        cmd = '/usr/bin/ipmitool'

        d = utils.getProcessOutput(cmd, params)
        return d

    def sendPowerOffSwitchPort(self, portnum):
        params = ['-H', Switch.IPADDRESS, '-U', Switch.USERNAME\
            , '-P', Switch.PASSWORD, 'raw', '0x32', '0x38'\
                , portnum, '0x0']

        d = self.sendIPMICommand(params) 
        return d

    def getPortNumberFromMac(self, mac):
        config = ConfigParser.ConfigParser()
        config.read(Conf.MACFILE)
        port = None
        for n in range(16):
            storedmac = config.get('mac', str(n))
            if mac == storedmac:
                port = n
                break
        return hex(port)

    def getCurrentTime(self):
        return datetime.today()

    def sendPowerONStatusToSwitch(self):
        params = []
        params.append('-H')
        params.append(Switch.IPADDRESS)
        params.append('-U')
        params.append(Switch.USERNAME)
        params.append('-P')
        params.append(Switch.PASSWORD)
        params.append('raw')
        params.append(Switch.OEMCMD)
        params.append(Switch.POWERONCMD)
        params = tuple(params)

        d = self.sendIPMICommand(None, params)
        return d

    def sendWakeUpTime(self):
        params = []
        params.append('-H')
        params.append(Switch.IPADDRESS)
        params.append('-U')
        params.append(Switch.USERNAME)
        params.append('-P')
        params.append(Switch.PASSWORD)
        params.append('raw')
        params.append('0x30')
        params.append('0x38')

        datetom = self.getNextDayDate()
        #format date
        if datetom.month <= 9:
            params.append('0'+str(datetom.month))
        else:
            params.append(str(datetom.month))
        if datetom.day <= 9:
            params.append('0'+str(datetom.day))
        else:
            params.append(str(datetom.day))

        year1 = str(datetom.year)[0:2]
        year2 = str(datetom.year)[2:4]
        params.append(year1)
        params.append(year2)

        #format time
        if Conf.WAKEUPHOUR <= 9:
            params.append('0'+str(Conf.WAKEUPHOUR))
        else:
            params.append(str(Conf.WAKEUPHOUR))
        if Conf.WAKEUPMINUTE <= 9:
            params.append('0'+str(Conf.WAKEUPMINUTE))
        else:
            params.append(str(Conf.WAKEUPMINUTE))

        d = self.sendIPMICommand(params)
        return d

    def sendSyncTime(self):
        params = []
        params.append('-H')
        params.append(Switch.IPADDRESS)
        params.append('-U')
        params.append(Switch.USERNAME)
        params.append('-P')
        params.append(Switch.PASSWORD)
        params.append('raw')
        params.append('0x30')
        params.append('0x3c')

        currentTime = self.getCurrentTime()

        #format date
        if currentTime.month <= 9:
            params.append('0'+str(currentTime.month))
        else:
            params.append(str(currentTime.month))
        if currentTime.day <= 9:
            params.append('0'+str(currentTime.day))
        else:
            params.append(str(currentTime.day))

        year1 = str(currentTime.year)[0:2]
        year2 = str(currentTime.year)[2:4]
        params.append(year1)
        params.append(year2)

        #format time
        if currentTime.hour <= 9:
            params.append('0'+str(currentTime.hour))
        else:
            params.append(str(currentTime.hour))
        if currentTime.minute <= 9:
            params.append('0'+str(currentTime.minute))
        else:
            params.append(str(currentTime.minute))

        d = self.sendIPMICommand(params)
        return d

    def sendIPMIAck(self):
        params = []
        params.append('-H')
        params.append(Switch.IPADDRESS)
        params.append('-U')
        params.append(Switch.USERNAME)
        params.append('-P')
        params.append(Switch.PASSWORD)
        params.append('raw')
        params.append(Switch.POWERONCMD)
        params.append(Switch.ACK)
        params = tuple(params)

        d = self.sendIPMICommand(None, params)
        return d

    def parseClustat(self, line):
            line = line.split()
            LocalWordIndex = line.index('Local,')
            HostName = line[LocalWordIndex - 3]
            logging.debug("local hostname: %s" % HostName)
            return HostName

    def getVirtualIP(self):
        hostfile = open("/etc/hosts", "r")
        lines = hostfile.readlines()
        ipaddress = ""
        for line in lines:
            if "virtual" in line:
                ipaddress = re.findall("(?:[0-9]{1,3}\.){3}[0-9]{1,3}" , line)[0]
                break

        hostfile.close()
        return ipaddress

    #NodeChecker
    def checkWhichNode(self, value):
        cmd = '/usr/sbin/clustat'
        d = utils.getProcessOutput(cmd)
        d.addCallback(self.parseClustat)
        return d
    
    def _powerOff(self, buffer):
        cmd = '/sbin/poweroff'
        d = utils.getProcessOutput(cmd)
        return d

    def startShutdown(self):
        returnValue = None
        if NodeA.shuttingDownCancelled == True or NodeB.shuttingDownCancelled == True:
            NodeA.shuttingDownCancelled = False
            NodeB.shuttingDownCancelled = False
            NodeA.serverState = ServerState.ON
            NodeB.serverState = ServerState.ON
            logging.info("Shutdown was cancelled")
            returnValue = None
        elif NodeA.shuttingDownPostponed == True or NodeB.shuttingDownPostponed == True:
            logging.info("Shutdown postponed. Server state set to countdown_in_progress")
            NodeA.shuttingDownPostponed = False
            NodeB.shuttingDownPostponed = False
            NodeA.serverState = ServerState.COUNTDOWN_IN_PROGRESS
            NodeB.serverState = ServerState.COUNTDOWN_IN_PROGRESS
            self.postponeToggle = True
            self.normalShutdown()
        else:
            logging.info("Immediate shutdown request granted")
            NodeA.serverState = ServerState.SHUTDOWN_IN_PROGRESS
            NodeB.serverState = ServerState.SHUTDOWN_IN_PROGRESS
            cmd = '/sbin/poweroff'
            #Todo: simplify this for Mgmt Vm based operation
            d = self.powerDownThinClients()
            d.addCallback(self.checkWhichNode) 
            d.addCallback(self.shutdownNeighbor)
            d.addCallback(self._powerOff)
            d.addCallback(self._logExitValue)
            returnValue = d
        #remove return?
        return returnValue

    def shutdownNeighbor(self, hostname):
        logging.debug("shutting down neighbor  of %s" % hostname)
        node = hostname.split('.')[0]
        schoolID = hostname.split('.')[1]
        cmd = '/usr/bin/ssh'
        params = []
        params.append('-o')
        params.append('StrictHostKeyChecking no')
        if node == 'sa':
            params.append('root@sb.%s.cloudtop.ph' % (schoolID))
        else:
            params.append('root@sa.%s.cloudtop.ph' % (schoolID))
        params.append('"/sbin/poweroff"')
        params = tuple(params)
        d = utils.getProcessOutput(cmd, params)
        d.addCallback(self._logExitValue)
        return d

    def setPowerUpCmd(self, hostname):
        neigbor = None
        nodeA = 'sa'
        nodeB = 'sb'
        if nodeA in hostname:
            neighbor = hostname.replace(nodeA, nodeB)
        else:
            neighbor = hostname.replace(nodeB, nodeA)

        params = []
        params.append('-H')
        params.append(neighbor)
        params.append('-U')
        params.append(NodeB.IPMIUSER)
        params.append('-P')
        params.append(NodeB.IPMIPASS)
        params.append('chassis')
        params.append('power')
        params.append('on')

        return params
    
    def powerUpNeighbor(self):
        d = self.checkWhichNode()
        d.addCallback(self.setPowerUpCmd)
        d.addCallback(self.sendIPMICommand)
        return d

    def shutdownBothBaremetals(self):
        cmd = 'ssh'
        params1 = []
        params2 = []
        params1.append('root@%s' % NodeA.IPADDRESS)
        params2.append('root@%s' % NodeB.IPADDRESS)
        params1.append('\"poweroff\"')
        params2.append('\"poweroff\"')

        d = utils.getProcessOutput(cmd, params1)
        d.addCallback(utils.getProcessOutput, cmd, params2)
        return d

    def normalShutdown(self):
        cmd = ServerNotifs.NORMAL_SHUTDOWN_START_COUNTDOWN | Conf.DEFAULTSCHEDULEDSHUTDOWNWAITTIME

        self.transport.write(hex(cmd), (ThinClient.DEFAULT_ADDR[0],ThinClient.DEFAULT_ADDR[1]))
        if self.postponeToggle == False:
            NodeA.serverState = ServerState.COUNTDOWN_IN_PROGRESS
            NodeB.serverState = ServerState.COUNTDOWN_IN_PROGRESS
            d = task.deferLater(reactor, self.shutdownDelay, self.startShutdown)
        else:
            d = task.deferLater(reactor, self.shutdownDelay, self.normalShutdown)
            self.postponeToggle = False
        self.schedulePowerUp()
        self.shutdownDelay = Conf.DEFAULTSCHEDULEDSHUTDOWNWAITTIME
        return d

    def schedulePowerUp(self):
        logging.info("Scheduling powerup using IPMI")
        params = []
        params.append('-H')
        params.append(NodeA.IPMIHOST)
        params.append('-U')
        params.append(NodeA.IPMIUSER)
        params.append('-P')
        params.append(NodeA.IPMIPASS)
        params.append('chassis')
        params.append('power')
        params.append('up')
        params = tuple(params)
        

        d = task.deferLater(reactor, self._timeFromPowerUp(), self.sendIPMICommand, params)

    def postponeShutdown(self, delay):
        if Power.state == PowerState.AC:
            logging.info("postpone shutdown request accepted")
            NodeA.shuttingDownPostponed = True
            NodeB.shuttingDownPostponed = True
            self.shutdownDelay = int(delay, 16)
        elif Power.state == PowerState.BATTERYMODE:
            logging.debug("postpone shutdown command not accepted. System is using Battery")

    def cancelShutdown(self):
        NodeA.shuttingDownCancelled = True
        NodeB.shuttingDownCancelled = True

    def executeReducedPowerMode(self):
        NodeB.serverState = ServerState.SHUTDOWN_IN_PROGRESS
        cmd = 'singleservermode'
        location = '/usr/sbin/'
       
        d = utils.getProcessOutput("%s%s" % (location, cmd))
        return d

    def ACRestoredFromHighPower(self):
        Power.state = PowerState.AC

    def ACRestoredFromLowPower(self):
        pass

    def grantShutdownRequest(self):
        pass        

    def processCommand(self, command):
        #check status of CPU
        logging.debug("processing datagram %s" % command)
        payload = None
        if len(command) > 1:
            if command[1] == 'x':
                #command came from the thinclient, postprocess
                payload = command[4:9]
                command = command[2]
        else:
            command = command[0]
        if command == Command.SHUTDOWN_IMMEDIATE:
            if NodeA.serverState == ServerState.ON or NodeB.serverState.ServerState.ON:
                self.sendIPMIAck()
                self.startShutdown()
            elif NodeA.serverState == ServerState.SHUTDOWN_IN_PROGRESS and\
                NodeB.serverState == ServerState.SHUTDOWN_IN_PROGRESS:
                pass
        elif command == Command.REDUCE_POWER:
            if NodeA.serverState == ServerState.ON and NodeB.serverState == ServerState.ON:
                self.executeReducedPowerMode()
            elif NodeB.serverState == ServerState.SHUTDOWN_IN_PROGRESS:
                #need handling here?
                logging.debug("ignoring Singe Server Mode request because 1 node is shutting down")
            elif NodeB.serverSate == ServerState.OFF:
                logging.debug("ignoring Singe Server Mode request because 1 node is already down")
        elif command == Command.SHUTDOWN_CANCEL:
            if NodeA.serverState == ServerState.COUNTDOWN_IN_PROGRESS and\
                NodeB.serverState == ServerState.COUNTDOWN_IN_PROGRESS:
                self.cancelShutdown()
        elif command == Command.AC_RESTORED:
            if NodeA.serverState == ServerState.SHUTDOWN_IN_PROGRESS and\
                NodeB.serverState == ServerState.SHUTDOWN_IN_PROGRESS:
                #can't do anything anymore
                pass
            elif Power.state == PowerState.BATTERYMODE:
                #nothing to do
                pass
            elif Power.state == PowerState.LOWBATTERY:
                self.ACRestoredFromLowPower()
        elif command == Command.POSTPONE:
            if NodeA.serverState == ServerState.COUNTDOWN_IN_PROGRESS and\
                NodeB.serverState ==ServerState.COUNTDOWN_IN_PROGRESS:
                self.postponeShutdown(payload)
        elif command == Command.UPDATE:
            self.updateTCDatabase()
        elif command == Command.SHUTDOWN_REQUEST:
            if NodeA.serverState == ServerState.COUNTDOWN_IN_PROGRESS:
                pass
            if NodeB.serverState == ServerState.COUNTDOWN_IN_PROGRESS:
                pass
            else:
                self.grantShutdownRequest() 
        elif command == Command.SHUTDOWN_NORMAL:
            if NodeA.serverState == ServerState.COUNTDOWN_IN_PROGRESS:
                print "hello"
                pass
            if NodeB.serverState == ServerState.COUNTDOWN_IN_PROGRESS:
                print "world"
                pass
            else:
                self.normalShutdown() 

    def startProtocol(self):
        self.address = ThinClient.DEFAULT_ADDR
        if Conf.DAILYSHUTDOWN:
            d = task.deferLater(reactor, self._timeFromShutdown(), self.normalShutdown)
        self.powerUpThinClients()

    def powerUpThinClients(self):
        params = []
        params.append('-H')
        params.append(Switch.IPADDRESS)
        params.append('-U')
        params.append(Switch.USERNAME)
        params.append('-P')
        params.append(Switch.PASSWORD)
        params.append('raw')
        params.append(Switch.TCPOWERCMD1)
        params.append(Switch.TCPOWERCMD2)
        params.append(hex(0))
        params.append(Switch.ON)
        d = self.sendIPMICommand(None, params)
        for tcnum in range(1, 15):
            params = []
            params.append('-H')
            params.append(Switch.IPADDRESS)
            params.append('-U')
            params.append(Switch.USERNAME)
            params.append('-P')
            params.append(Switch.PASSWORD)
            params.append('raw')
            params.append(Switch.TCPOWERCMD1)
            params.append(Switch.TCPOWERCMD2)
            params.append(hex(tcnum))
            params.append(Switch.ON)

            #timer.sleep(2)
            d.addCallback(self.sendIPMICommand,params)
        return d

    def powerDownThinClients(self):
        params = []
        params.append('-H')
        params.append(Switch.IPADDRESS)
        params.append('-U')
        params.append(Switch.USERNAME)
        params.append('-P')
        params.append(Switch.PASSWORD)
        params.append('raw')
        params.append(Switch.TCALLPOWER1)
        params.append(Switch.TCALLPOWER2)
        params.append(Switch.OFF)

        d = self.sendIPMICommand(None,params)
        return d

    def getNextDayDate(self):
        oneDay = timedelta(days=1)
        tomorrow = date.today() + oneDay
        return (tomorrow.year, tomorrow.month, tomorrow.day)

    def _timeFromPowerUp(self):
        currentTime = datetime.now()
        oneDay = timedelta(days=1)
        tomorrow = date.today() + oneDay
        shutdownTime = datetime.combine(tomorrow, time(Conf.WAKEUPHOUR,Conf.WAKEUPMINUTE))
        timeDiff = shutdownTime - currentTime
        return timeDiff.seconds

    def _timeFromShutdown(self):
        #wont work after 6pm (negative time!)
        currentTime = datetime.now()
        shutdownTime = datetime.combine(date.today(), time(Conf.SHUTDOWNHOUR,Conf.SHUTDOWNMINUTE))    
        timeDiff = shutdownTime - currentTime
        return timeDiff.seconds

    def datagramReceived(self, data, (host, port)):
        self.address = (host, port)
        self.processCommand(data)
        logging.info("datagram received")

    def updateTCDatabase(self):
        
        IPAddressFinder.update()
        

#power manager factory class
class PowerManagerFactory(protocol.ServerFactory):
    protocol = None
    #instantiates a power Manager class on 
    def buildProtocol(self, addr):
        self.protocol = PowerManager()
        return self.protocol

def SIGTERMHandler():
    logging.debug('Power manager received SIGTERM. Exiting...')
    reactor.stop()
    exit()

#main function
if __name__ == "__main__":
    signal.signal(signal.SIGTERM, SIGTERMHandler)
    fillAllDefaults("/etc/power_mgmt.cfg")
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(filename=Conf.LOGFILE,level=Conf.LOGLEVEL, format=FORMAT)
    #run reactor
    powerManager = PowerManager()
    virtualIP = powerManager.getVirtualIP()
    reactor.listenUDP(8880, powerManager)
    reactor.run()