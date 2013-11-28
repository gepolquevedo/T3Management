from twisted.internet import defer
from datetime import date
from re import findall

import socket


class SessionFinder():

	def __init__(self):
		self.todaysloglist = []
		self.infologslist = []
		self.sessioninfolist = {}

	def parseXRDPLog(self):
		pass

	def getTodayLogs(self):
		logfile = open('/var/log/xrdp-sesman.log', 'r')
		sDate = str(date.today())
		sDate = sDate.replace('-','')

		#loop here
		while True:

			line = logfile.readline()
			if not line: break
			infoline = findall(sDate, line)
			if len(infoline) > 0:
				self.todaysloglist.append(line)
		logfile.close()

	def getInfoFromLogs(self):

		for line in self.todaysloglist:
			infoline = findall('created session', line)
			if len(infoline) > 0:
				self.infologslist.append(line)


	def getSessionInfo(self):
		infolist = []

		for line in self.infologslist:
			ipaddress = findall('(?:[0-9]{1,3}\.){3}[0-9]{1,3}', line)[0]
			username = findall('(?<=username\s)[a-z0-9\.]*', line)[0]
			port = findall( '(?<=:)[0-9]{5}', line)[0]
			socket = findall('(?<=socket:\s)[0-9]{1,2}', line)[0]

			infolist.append((ipaddress, (username, int(port), int(socket))))

		infolist = dict(infolist)
		self.sessioninfolist = infolist



	