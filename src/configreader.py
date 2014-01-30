import ConfigParser
from powermodels import NodeA, NodeB, Conf, Switch, ThinClient

def _fillSwitchDefaults(configfile):
	config = ConfigParser.ConfigParser()
	config.read(configfile)

	Switch.ID = int(config.get('switch', 'id'), 16)
	Switch.IPADDRESS = config.get('switch', 'ipaddress')
	Switch.USERNAME = config.get('switch', 'username')
	Switch.PASSWORD = config.get('switch', 'password')

def _fillConfigDefaults(configfile):
	config = ConfigParser.ConfigParser()
	config.read(configfile)

	Conf.SHUTDOWNHOUR = int(config.get('defaults', 'shutdownhour'))
	Conf.SHUTDOWNMINUTE = int(config.get('defaults', 'shutdownminute'))
	Conf.WAKEUPHOUR = int(config.get('defaults', 'wakeuphour'))
	Conf.WAKEUPMINUTE = int(config.get('defaults', 'wakeupminute'))

def _fillNodeDefaults(configfile):
	config = ConfigParser.ConfigParser()
	config.read(configfile)
	
	NodeA.IP = config.get('nodeA', 'ip')
	NodeA.IPMIHOST = config.get('nodeA', 'ipmihost')
	NodeA.IPMIUSER = config.get('nodeA', 'ipmiuser')
	NodeA.IPMIPASSWORD = config.get('nodeA', 'ipmipassword')

	NodeB.IP = config.get('nodeB', 'ip')
	NodeB.IPMIHOST = config.get('nodeB', 'ipmihost')
	NodeB.IPMIUSER = config.get('nodeB', 'ipmiuser')
	NodeB.IPMIPASSWORD = config.get('nodeB', 'ipmipassword')

def _fillThinclientDefaults(configfile):
	config = ConfigParser.ConfigParser()
	config.read(configfile)
	
	ThinClient.DEFAULT_ADDR = (config.get('thinclient', 'default_addr'), 8880)
	ThinClient.SERVERA_ADDR = (config.get('thinclient', 'serverA_addr'), 8880)
	ThinClient.SERVERB_ADDR = (config.get('thinclient', 'serverB_addr'), 8880)

def fillAllDefaults(configfile):
	_fillSwitchDefaults(configfile)
	_fillNodeDefaults(configfile)
	_fillConfigDefaults(configfile)
	_fillThinclientDefaults(configfile)