from mock import Mock, call, patch
from twisted.internet import defer, reactor
from twisted.trial import unittest

from cloudtop.helper.ipaddressfinder import IPAddressFinder
from subprocess import CalledProcessError

class IPAddressFinderTestsuite(unittest.TestCase):
    
    def setUp(self):    
        pass

    def tearDown(self):
        IPAddressFinder.macAddresses = []


    def testParseArping(self):
        inputstring = 'Unicast reply from 192.168.1.1 [94:00:F4:35:FE:9B]  2.232ms'

        macAddress = IPAddressFinder.parseArping(inputstring)

        self.assertEqual('94-00-F4-35-FE-9B',macAddress)

    def testParseArping_noStringFound(self):
        inputstring = 'Received 0 response(s)'

        macAddress = IPAddressFinder.parseArping(inputstring)

        self.assertEqual('', macAddress)



    @patch('cloudtop.helper.ipaddressfinder.subprocess')
    def testArPing(self, subprocess):
        subprocess.check_output = Mock(return_value ="samplestring")
        ipaddress = '172.16.1.101'

        arpstring = IPAddressFinder.ArPing(ipaddress)

        self.assertEqual("samplestring", arpstring)

    @patch('cloudtop.helper.ipaddressfinder.subprocess')
    def testArPing_CalledProcessError(self, subprocess):
        subprocess.check_output = Mock(side_effect=CalledProcessError(1, 'arping'))
        ipaddress = '172.16.1.101'

        arpstring = IPAddressFinder.ArPing(ipaddress)

        self.assertEqual(-1, arpstring)

    @patch('cloudtop.helper.ipaddressfinder.IPAddressFinder.ArPing')
    @patch('cloudtop.helper.ipaddressfinder.IPAddressFinder.parseArping')
    def testGetIPAddresses(self, parse, arping):
        arping.return_value = "test string"
        parse.return_value = "test string 2" 

        IPAddressFinder.getIPAddresses()

        arping.assert_called_with('172.16.1.254')
        parse.assert_called_with('test string')
        self.assertEqual(IPAddressFinder.macAddresses[154], "test string 2")

    @patch('cloudtop.helper.ipaddressfinder.ConfigParser.ConfigParser')
    def testGetIPBlock(self, parser):
        ipblock = '172.16.1.'
        configfile = 'test'
        parser.read = Mock()
        parser().get = Mock(return_value=ipblock)
        
        retval = IPAddressFinder.getIPBlock(configfile)

        parser().read.assert_called_with(configfile)
        parser().get.assert_called_with('defaults', 'ipblock')
        self.assertEqual(ipblock, retval)

    @patch('cloudtop.helper.ipaddressfinder.ConfigParser.ConfigParser')
    def testGetIPMapFile(self, parser):
        mapfile = '/var/ipmapfile'
        configfile = 'test'
        parser.read = Mock()
        parser().get = Mock(return_value=mapfile)

        retval = IPAddressFinder.getIPMapFile(configfile)

        parser().read.assert_called_with(configfile)
        parser().get.assert_called_with('defaults', 'mapfile')
        self.assertEqual(retval, mapfile)

    @patch("cloudtop.helper.ipaddressfinder.IPAddressFinder.getIPBlock")
    @patch("cloudtop.helper.ipaddressfinder.IPAddressFinder.getIPMapFile")
    @patch("__builtin__.open")
    def testCreateTableFile(self, fileopen, getmap, getblock):
        getmap.return_value = 'filename'
        getblock.return_value = '172.16.1.'
        fileopen().write = Mock()
        ipaddress = '172.16.1.254'
        mac = ' '
        IPAddressFinder.macAddresses = []
        for n in range(153):
            IPAddressFinder.macAddresses.append(' ')
        IPAddressFinder.macAddresses.append('94-00-F4-35-FE-9B')
        IPAddressFinder.macAddresses.append(' ')

        IPAddressFinder.createTableFile()

        fileopen().write.assert_called_with("%s,%s" % (ipaddress,mac))

    @patch("cloudtop.helper.ipaddressfinder.subprocess")
    def testSendFileToRDP(self, subprocess):
        subprocess.call = Mock(return_value=0)
        mintA = 'rdpmintA.local'
        mintB = 'rdpmintB.local'

        calls = []
        calls.append(call(['scp',IPAddressFinder.mapFile,'rdpadmin@%s:/var' % mintA]))
        calls.append(call(['scp',IPAddressFinder.mapFile,'rdpadmin@%s:/var' % mintB]))

        IPAddressFinder.sendFileToRDP()

        subprocess.call.assert_has_calls(calls, any_order=True)


    @patch("__builtin__.open")
    def testGetRDPHostnames(self, openfile):
        #read /etc/hosts
        openfile.readlines = Mock(return_value=['calhost localhost.localdomain localhost4 localhost4.localdomain4 sa.local\n'\
                , '::1         localhost localhost.localdomain localhost6 localhost6.localdomain6\n'\
                , '\n', '10.18.221.11\t\tsa.105134.cloudtop.ph\n'\
                , '10.18.221.12\t\tsb.105134.cloudtop.ph\n'\
                , '10.18.221.111\t\tipmi.sa.105134.cloudtop.ph\n'\
                , '10.18.221.112\t\tipmi.sb.105134.cloudtop.ph\n'\
                , '10.18.221.20\t\tldap.105134.cloudtop.ph\n'\
                , '\n', '#For munin\n'\
                , '\n', '10.18.221.20\t\tldap.local\n'\
                , '10.18.221.21\t\tlms.local\n'\
                , '10.18.221.24\t\trdpminta.local\n'\
                , '10.18.221.25\t\trdpmintb.local\n'\
                , '\n', '#For puppet\n'\
                , '10.225.1.215\t\tpuppetmaster.cloudtop.ph\n'\
                , '\n'])
        hostnames = ['','']

        IPAddressFinder.getRDPHostnames()

    testGetRDPHostnames.skip = 'pending'

    @patch("cloudtop.helper.ipaddressfinder.IPAddressFinder.socket")
    def testGetOwnHostname(self, socket):
        #use socket
        socket.gethostname = Mock(return_value='rdphostname')

    testGetOwnHostname.skip = 'pending'

    # testArPing_CalledProcessError.skip = "TBA"

    def testUpdate(self):

        IPAddressFinder.createTableFile = Mock()
        IPAddressFinder.sendFileToRDP = Mock()
        IPAddressFinder.getIPAddresses = Mock()

        IPAddressFinder.update()

        assert IPAddressFinder.createTableFile.called
        assert IPAddressFinder.sendFileToRDP.called
        assert IPAddressFinder.getIPAddresses.called
