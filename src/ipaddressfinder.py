import re, subprocess, ConfigParser

from subprocess import CalledProcessError

class IPAddressFinder():
	macAddresses = []
	mapFile = None

	@classmethod
	def parseArping(cls, inputstring):
		returnstring = None

		mac = re.findall('\[.+\]', inputstring)
		if len(mac) == 0:
			returnstring = ''
		else:
			mac = mac[0]
			mac = list(mac)
			del(mac[0])
			del(mac[-1])
			mac = ['-' if char==':' else char for char in mac]
			returnstring = "".join(mac)

		return returnstring

	@classmethod
	def ArPing(cls, ipaddress):
		try:
			returnstring = subprocess.check_output(['arping', '-s 1', ipaddress])
		except CalledProcessError:
			returnstring = -1

		return returnstring

	@classmethod
	def getIPAddresses(cls):
		ipblock ='172.16.1.'
		for n in range(100, 255):
			returnstring = cls.ArPing("%s%s" % (ipblock,n))
			macAddress = cls.parseArping(returnstring)
			#mac address for x.x.x.100 is stored aat [0]
			cls.macAddresses.append(macAddress)

	@classmethod
	def getIPMapFile(cls, configfile):
		config = ConfigParser.ConfigParser()
		config.read(configfile)

		mapfile = config.get('defaults', 'mapfile')
		return mapfile

	@classmethod
	def getIPBlock(cls, configfile):
		config = ConfigParser.ConfigParser()
		config.read(configfile)

		ipblock = config.get('defaults', 'ipblock')
		return ipblock

	@classmethod
	def createTableFile(cls):
		macfile = open(cls.getIPMapFile(), 'w')
		ipblock = cls.getIPBlock()

		#index + 100 is the IP address last 8 bits
		#made for current school subnet setup
		for n in range(155):
			macfile.write("%s%s,%s" % (ipblock,str(n+100), cls.macAddresses[n]))

		macfile.close()

	@classmethod
	def sendFileToRDP(cls):
		subprocess.call(['scp', cls.mapFile,'rdpadmin@rdpmintA.local:/var'])
		subprocess.call(['scp', cls.mapFile,'rdpadmin@rdpmintB.local:/var'])

	@classmethod
	def update(cls):

		cls.getIPAddresses()
		cls.createTableFile()
		cls.sendFileToRDP()
