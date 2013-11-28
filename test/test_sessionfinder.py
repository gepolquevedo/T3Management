from mock import Mock, call, patch
from twisted.internet import defer, reactor
from twisted.trial import unittest

from cloudtop.helper.sessionfinder import SessionFinder
from cloudtop.config.test import TEST




class SessionFinderTestsuite(unittest.TestCase):

	def setUp(self):
		self.sessionfinder = SessionFinder()

	def tearDown(self):
		self.sessionfinder.todaysloglist = []
		self.sessionfinder.infologslist = []
		self.sessionfinder.sessioninfolist = {}

	def testParseXRDPLog(self):
		pass
		# SessionFinder.parseXRDPLog()
		
		#use actual log file for testing? yes for now    

	def testParseIPMacTable(self):
		pass

	def testCombineData(self):
		pass

	def testWriteCombinedData(self):
		pass

	#consolidate lists for both RDPA and B!
	@patch("cloudtop.helper.sessionfinder.date")
	@patch("__builtin__.open")
	def testGetTodayLogs(self, fopen, sysdate):
		sysdate.today = Mock(return_value='2013-11-06')
		fopen().readline = Mock()
		fopen().readline.side_effect = ['[20131106-16:55:17] [INFO ] ++ reconnected session: username teacher15, display :11.0, session_pid 5657, ip 172.16.1.116:54932 - socket: 9'\
			,'[20131106-16:55:17] [INFO ] scp thread on sck 8 started successfully'\
			, '[20131105-09:07:48] [INFO ] A connection received from: 127.0.0.1 port 36409'\
			, None]

		correct = ['[20131106-16:55:17] [INFO ] ++ reconnected session: username teacher15, display :11.0, session_pid 5657, ip 172.16.1.116:54932 - socket: 9'\
			,'[20131106-16:55:17] [INFO ] scp thread on sck 8 started successfully']

		self.sessionfinder.getTodayLogs()
		lines = self.sessionfinder.todaysloglist

		self.assertEqual(lines, correct)

	def testgetInfoLogs(self):
		#TODO: read test file?
		self.sessionfinder.todaysloglist = ['[20131011-13:56:05] [INFO ] A connection received from: 127.0.0.1 port 57323'\
			,'[20131011-13:56:05] [INFO ] scp thread on sck 8 started successfully'\
			,'[20131011-13:56:05] [INFO ] ++ created session (access granted): username teacher6, ip 172.16.1.107:60391 - socket: 9'\
			,'[20131011-13:56:05] [INFO ] starting X11rdp session...'\
			,'[20131011-13:56:06] [INFO ] An established connection closed to endpoint: NULL:NULL - socket: 20'\
			,'[20131011-13:56:06] [INFO ] An established connection closed to endpoint: NULL:NULL - socket: 19'\
			,'[20131011-13:56:06] [INFO ] An established connection closed to endpoint: NULL:NULL - socket: 19'\
			,'[20131011-13:56:06] [INFO ] An established connection closed to endpoint: 127.0.0.1:57323 - socket: 8'\
			,'[20131011-13:56:06] [INFO ] An established connection closed to endpoint: NULL:NULL - socket: 7'\
			,'[20131011-13:56:06] [INFO ] An established connection closed to endpoint: 127.0.0.1:57323 - socket: 8'\
			,'[20131011-13:56:06] [INFO ] X11rdp start:X11rdp :14 -geometry 1600x900 -depth 24 -bs -ac -nolisten tcp -uds'\
			,'[20131011-13:56:06] [INFO ] starting xrdp-sessvc - xpid=6983 - wmpid=6982'\
			,'[20131011-13:57:35] [INFO ] A connection received from: 127.0.0.1 port 57337'\
			,'[20131011-13:57:35] [INFO ] scp thread on sck 8 started successfully'\
			,'[20131011-13:57:35] [INFO ] ++ created session (access granted): username teacher7, ip 172.16.1.120:54775 - socket: 9'\
			,'[20131011-13:57:35] [INFO ] starting X11rdp session...'\
			,'[20131011-13:57:35] [INFO ] An established connection closed to endpoint: NULL:NULL - socket: 21']

		correct = ['[20131011-13:56:05] [INFO ] ++ created session (access granted): username teacher6, ip 172.16.1.107:60391 - socket: 9'\
		,'[20131011-13:57:35] [INFO ] ++ created session (access granted): username teacher7, ip 172.16.1.120:54775 - socket: 9']

		self.sessionfinder.getInfoFromLogs()

		lines = self.sessionfinder.infologslist
		self.assertEqual(lines, correct)

	def testgetSessionInfo(self):
		self.sessionfinder.infologslist = ['[20131011-13:56:05] [INFO ] ++ created session (access granted): username teacher6, ip 172.16.1.107:60391 - socket: 9'\
		,'[20131011-13:57:35] [INFO ] ++ created session (access granted): username teacher7, ip 172.16.1.120:54775 - socket: 9']

		correct = {'172.16.1.107':('teacher6',60391,9),'172.16.1.120':('teacher7', 54775, 9)	}
		#key-value pair with IP-address as key?

		self.sessionfinder.getSessionInfo()

		lines = self.sessionfinder.sessioninfolist
		self.assertEqual(lines, correct)		

	@patch("__builtin__.open")
	def testAppendInfoToFile(self, fopen):
		fopen().readline = Mock()
		fopen().write = Mock()
		self.sessionfinder.sessioninfolist = {'172.16.1.107':('teacher6',60391,9),'172.16.1.120':('teacher7', 54775, 9)	}

		fopen().readline.side_effect = ['172.16.1.107,94-00-F4-35-FE-9B'
			,'172.16.1.108,94-00-F4-35-FE-9B,',]

		self.sessionfinder.appendInfoToFile()

		fopen().write.assert_called_with('172.16.1.107, 94-00-F4-35-FE-9B, teacher6, 60391, 9')


	testAppendInfoToFile.skip = "Dev request update file to power manager first"

	@patch('socket.socket')
	def testSendUpdateCommand(self, socket):
		socket.AF_INET = Mock()
		socket.SOCK_DGRAM = Mock()

		self.sessionfinder.sendUpdateCommand()

		socket.sendto.assert_called_with()

	testSendUpdateCommand.skip ="in progress"

	

	






