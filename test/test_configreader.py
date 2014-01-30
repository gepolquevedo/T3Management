from mock import Mock, call, patch
from twisted.internet import defer, reactor
from twisted.trial import unittest

# from cloudtop.daemon.PowerManager import NodeA, NodeB, Conf, Switch, ThinClient
from powermodels import NodeA, NodeB, Conf, Switch, ThinClient
import configreader

#from cloudtop.config.test import TEST

import ConfigParser

class ConfigreaderTestSuite(unittest.TestCase):
    
    def setUp(self):
        #hardcoded for now
        self.testFile = "/Users/gepol/T3Management/power_mgmt.cfg"
        switch = {}
        nodeA = {}
        nodeB = {}
        thinclient = {}
        defaults = {}
        self.configset = {}

        switch['id'] = 0x300000
        switch['ipaddress'] = '10.225.3.71'
        switch['username'] = 'Admin'
        switch['password'] = 'Admin'

        nodeA['ip'] = '10.225.3.61'
        nodeA['ipmihost'] = '10.225.3.63'
        nodeA['ipmiuser'] = 'ADMIN'
        nodeA['ipmipassword'] = 'ADMIN'

        nodeB['ip'] = '10.225.3.62'
        nodeB['ipmihost'] = '10.225.3.64'
        nodeB['ipmiuser'] = 'ADMIN'
        nodeB['ipmipassword'] = 'ADMIN'

        thinclient['default_addr'] = '10.225.3.73'
        thinclient['serverA_addr'] = '10.225.3.73'
        thinclient['serverB_addr'] = '10.225.3.74'

        defaults['shutdownhour'] = 20
        defaults['shutdownminute'] = 0
        defaults['wakeuphour'] = 5
        defaults['wakeupminute'] = 0

        self.configset['switch'] = switch
        self.configset['nodeA'] = nodeA
        self.configset['nodeB'] = nodeB
        self.configset['thinclient'] = thinclient
        self.configset['defaults'] = defaults

    def tearDown(self):
        pass

    def testFillSwitchDefaults(self):
        configreader._fillSwitchDefaults(self.testFile)

        #checks
        self.assertEqual(Switch.ID, self.configset['switch']['id'])
        self.assertEqual(Switch.IPADDRESS, self.configset['switch']['ipaddress'])
        self.assertEqual(Switch.PASSWORD, self.configset['switch']['password'])

    def testFillConfigDefaults(self):
        configreader._fillConfigDefaults(self.testFile)

        #checks
        self.assertEqual(Conf.SHUTDOWNHOUR, self.configset['defaults']['shutdownhour'])
        self.assertEqual(Conf.SHUTDOWNMINUTE, self.configset['defaults']['shutdownminute'])
        self.assertEqual(Conf.WAKEUPHOUR, self.configset['defaults']['wakeuphour'])
        self.assertEqual(Conf.WAKEUPMINUTE, self.configset['defaults']['wakeupminute'])

    def testFillNodeDefaults(self):
        configreader._fillNodeDefaults(self.testFile)

        #checks
        self.assertEqual(NodeA.IP, self.configset['nodeA']['ip'])
        self.assertEqual(NodeA.IPMIHOST, self.configset['nodeA']['ipmihost'])
        self.assertEqual(NodeA.IPMIUSER, self.configset['nodeA']['ipmiuser'])
        self.assertEqual(NodeA.IPMIPASSWORD, self.configset['nodeA']['ipmipassword'])

        self.assertEqual(NodeB.IP, self.configset['nodeB']['ip'])
        self.assertEqual(NodeB.IPMIHOST, self.configset['nodeB']['ipmihost'])
        self.assertEqual(NodeB.IPMIUSER, self.configset['nodeB']['ipmiuser'])
        self.assertEqual(NodeB.IPMIPASSWORD, self.configset['nodeB']['ipmipassword'])
        
    def testFillThinclientDefaults(self):
        configreader._fillThinclientDefaults(self.testFile)

        self.assertEqual(ThinClient.DEFAULT_ADDR, (self.configset['thinclient']['default_addr'], 8880))
        self.assertEqual(ThinClient.SERVERA_ADDR, (self.configset['thinclient']['serverA_addr'], 8880))
        self.assertEqual(ThinClient.SERVERB_ADDR, (self.configset['thinclient']['serverB_addr'], 8880))

    @patch('configreader._fillSwitchDefaults')
    @patch('configreader._fillNodeDefaults')
    @patch('configreader._fillThinclientDefaults')
    @patch('configreader._fillConfigDefaults')
    def testFillAllDefaults(self, config, thinclient, node, switch):
        configreader.fillAllDefaults(self.testFile)

        configreader._fillSwitchDefaults.assert_called_with(self.testFile)
        configreader._fillConfigDefaults.assert_called_with(self.testFile)
        configreader._fillNodeDefaults.assert_called_with(self.testFile)
        configreader._fillThinclientDefaults.assert_called_with(self.testFile)       