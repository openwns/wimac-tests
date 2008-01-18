import math
import wns
import wns.Node
import constanze.Constanze
import rise.Mobility
import ip.Component
import udp.Node

from ofdmaphy.Station import OFDMAStation, OFDMAComponent

import Stations
import wimac.Rang

from support.scenarioSupport import convertMACtoIP
from support.Transceiver import Transceiver

class SubscriberStation(wns.Node.Node):
    phy = None
    dll = None
    nl  = None
    load = None
    mobility = None

    def __init__(self, _id, _config):
        super(SubscriberStation, self).__init__("UT"+str(_id))
        transceiver = Transceiver(_config)
        self.phy = None
        # create the WIMAX DLL
        self.dll = Stations.SubscriberStation(self, _config)
        self.dll.setStationID(_id)
        phyStation = OFDMAStation([transceiver.receiver['UT']], [transceiver.transmitter['UT']],
                                  eirpLimited = _config.eirpLimited,
                                  noOfAntenna = _config.parametersSystem.numberOfAntennaUTRxTx,
                                  arrayLayout = _config.arrayLayout,
                                  positionErrorVariance = _config.positionErrorVariance)
        phyStation.txFrequency = _config.parametersSystem.centerFrequency
        phyStation.rxFrequency = _config.parametersSystem.centerFrequency
        phyStation.txPower = _config.parametersSystem.txPowerUT
        phyStation.numberOfSubCarrier = _config.parametersPhy.subchannels
        phyStation.bandwidth =  _config.parametersPhy.channelBandwidth
        phyStation.systemManagerName = 'ofdma'
        self.phy = OFDMAComponent(self, "phy", phyStation)
        self.dll.setPhyDataTransmission(self.phy.dataTransmission)
        self.dll.setPhyNotification(self.phy.notification)
        # create Network Layer and Loadgen
        domainName = "SS" + str(_id) + ".wimax.wns.org"
        self.nl = ip.Component.IPv4Component(self, domainName + ".ip", domainName)
        self.nl.addDLL(_name = "wimax",
                       # Where to get IP Adresses
                       _addressResolver = ip.AddressResolver.VirtualDHCPResolver("WIMAXRAN"),
                       # Name of ARP zone
                       _arpZone = "WIMAXRAN",
                       # We cannot deliver locally to other UTs without going to the gateway
                       _pointToPoint = True,
                       _dllDataTransmission = self.dll.dataTransmission,
                       _dllNotification = self.dll.notification)

        self.nl.addRoute("0.0.0.0", "0.0.0.0", "192.168.254.254", "wimax")

        self.load = constanze.Node.ConstanzeComponent(self, "constanze")
        self.mobility = rise.Mobility.Component(node = self,
                                                name = "mobility UT"+str(_id),
                                                mobility = rise.Mobility.No(wns.Position())
                                                )



class RemoteStation(wns.Node.Node):
    phy = None
    dll = None
    nl  = None
    load = None
    mobility = None

    def __init__(self, _id, _config):
        super(RemoteStation, self).__init__("UT"+str(_id))
        transceiver = Transceiver(_config)
        self.phy = None
        # create the WIMAX DLL
        self.dll = Stations.RemoteStation(self, _config)
        self.dll.setStationID(_id)
        phyStation = OFDMAStation([transceiver.receiver['UT']], [transceiver.transmitter['UT']],
                                  eirpLimited = _config.eirpLimited,
                                  noOfAntenna = _config.parametersSystem.numberOfAntennaUTRxTx,
                                  arrayLayout = _config.arrayLayout,
                                  positionErrorVariance = _config.positionErrorVariance)
        phyStation.txFrequency = _config.parametersSystem.centerFrequency
        phyStation.rxFrequency = _config.parametersSystem.centerFrequency
        phyStation.txPower = _config.parametersSystem.txPowerUT
        phyStation.numberOfSubCarrier = _config.parametersPhy.subchannels
        phyStation.bandwidth =  _config.parametersPhy.channelBandwidth
        phyStation.systemManagerName = 'ofdma'
        self.phy = OFDMAComponent(self, "phy", phyStation)
        self.dll.setPhyDataTransmission(self.phy.dataTransmission)
        self.dll.setPhyNotification(self.phy.notification)
        # create Network Layer and Loadgen
        domainName = "RS" + str(_id) + ".wimax.wns.org"
        self.nl = ip.Component.IPv4Component(self, domainName + ".ip", domainName)
        self.nl.addDLL(_name = "wimax",
                       # Where to get IP Adresses
                       _addressResolver = ip.AddressResolver.VirtualDHCPResolver("WIMAXRAN"),
                       # Name of ARP zone
                       _arpZone = "WIMAXRAN",
                       # We cannot deliver locally to other UTs without going to the gateway
                       _pointToPoint = True,
                       _dllDataTransmission = self.dll.dataTransmission,
                       _dllNotification = self.dll.notification)

        self.nl.addRoute("0.0.0.0", "0.0.0.0", "192.168.254.254", "wimax")

        self.load = constanze.Node.ConstanzeComponent(self, "constanze")
        self.mobility = rise.Mobility.Component(node = self,
                                                name = "mobility UT"+str(_id),
                                                mobility = rise.Mobility.No(wns.Position()))



class RelayStation(wns.Node.Node):
    phy = None
    dll = None
    mobility = None

    def __init__(self, _id, _config):
        super(RelayStation, self).__init__("FRS"+str(_id))
        transceiver = Transceiver(_config)
        self.phy = None
        # create the WIMAX DLL
        self.dll = Stations.RelayStation(self, _config)
        self.dll.setStationID(_id)
        phyStation = OFDMAStation([transceiver.receiver['FRS']], [transceiver.transmitter['FRS']],
                                  eirpLimited = _config.eirpLimited,
                                  noOfAntenna = _config.parametersSystem.numberOfAntennaFRSRxTx,
                                  arrayLayout = _config.arrayLayout,
                                  positionErrorVariance = _config.positionErrorVariance)
        phyStation.txFrequency = _config.parametersSystem.centerFrequency
        phyStation.rxFrequency = _config.parametersSystem.centerFrequency
        phyStation.txPower = _config.parametersSystem.txPowerFRS
        phyStation.numberOfSubCarrier = _config.parametersPhy.subchannels
        phyStation.bandwidth =  _config.parametersPhy.channelBandwidth
        phyStation.systemManagerName = 'ofdma'
        self.phy = OFDMAComponent(self, "phy", phyStation)
        self.dll.setPhyDataTransmission(self.phy.dataTransmission)
        self.dll.setPhyNotification(self.phy.notification)
        # create PHY
        self.mobility = rise.Mobility.Component(node = self,
                                                name = "mobility FRS"+str(_id),
                                                mobility = rise.Mobility.No(wns.Position()))



class BaseStation(wns.Node.Node):
    phy = None
    dll = None
    mobility = None

    def __init__(self, _id, _config):
        super(BaseStation, self).__init__("AP"+str(_id))
        transceiver = Transceiver(_config)
        #self.phy = OFDMAComponent(self, "phy", phyStation)
        # create the WIMAC DLL
        self.dll = Stations.BaseStation(self, _config)
        self.dll.setStationID(_id)
        phyStation = OFDMAStation([transceiver.receiver['AP']], [transceiver.transmitter['AP']],
                                  eirpLimited = _config.eirpLimited,
                                  noOfAntenna = _config.parametersSystem.numberOfAntennaAPRxTx,
                                  arrayLayout = _config.arrayLayout,
                                  positionErrorVariance = _config.positionErrorVariance)
        phyStation.txPower = _config.parametersSystem.txPowerAP
        phyStation.txFrequency = _config.parametersSystem.centerFrequency
        phyStation.rxFrequency = _config.parametersSystem.centerFrequency
        phyStation.bandwidth =  _config.parametersPhy.channelBandwidth
        phyStation.numberOfSubCarrier = _config.parametersPhy.subchannels
        phyStation.systemManagerName = 'ofdma'
        self.phy = OFDMAComponent(self, "phy", phyStation)
        self.dll.setPhyDataTransmission(self.phy.dataTransmission)
        self.dll.setPhyNotification(self.phy.notification)
        self.mobility = rise.Mobility.Component(node = self,
                                                name = "mobility AP"+str(_id),
                                                mobility = rise.Mobility.No(wns.Position()))



class SubscriberStationTLAppl(wns.Node.Node):
    phy = None
    dll = None
    nl  = None
    tl = None
    load = None
    mobility = None

    def __init__(self, _id, _config, _qos = "UGS"):
        super(SubscriberStationTLAppl, self).__init__("UT"+str(_id))
        transceiver = Transceiver(_config)
        #self.phy = None
        # create the WIMAX DLL
        self.dll = Stations.SubscriberStation(self, _config)#, ring = 2)
        self.dll.setStationID(_id)
        phyStation = OFDMAStation([transceiver.receiver['UT']], [transceiver.transmitter['UT']],
                                  eirpLimited = _config.eirpLimited,
                                  noOfAntenna = _config.parametersSystem.numberOfAntennaUTRxTx,
                                  arrayLayout = _config.arrayLayout,
                                  positionErrorVariance = _config.positionErrorVariance)
        phyStation.txFrequency = _config.parametersSystem.centerFrequency
        phyStation.rxFrequency = _config.parametersSystem.centerFrequency
        phyStation.txPower = _config.parametersSystem.txPowerUT
        phyStation.numberOfSubCarrier = _config.parametersPhy.subchannels
        phyStation.bandwidth =  _config.parametersPhy.channelBandwidth
        phyStation.systemManagerName = 'ofdma'
        self.phy = OFDMAComponent(self, "phy", phyStation)
        self.dll.setPhyDataTransmission(self.phy.dataTransmission)
        self.dll.setPhyNotification(self.phy.notification)
        # create Network Layer and Loadgen
        domainName = "SS" + str(_id) + ".wimaxt.wns.org"
        self.nl = ip.Component.IPv4Component(self, domainName + ".ip", domainName)
        self.nl.addDLL(_name = "wimax",
                       # Where to get IP Adresses
                       _addressResolver = ip.AddressResolver.VirtualDHCPResolver("WIMAXRAN"),
                       # Name of ARP zone
                       _arpZone = "WIMAXRAN",
                       # We cannot deliver locally to other UTs without going to the gateway
                       _pointToPoint = True,
                       _dllDataTransmission = self.dll.dataTransmission,
                       _dllNotification = self.dll.notification)

        self.nl.addRoute("0.0.0.0", "0.0.0.0", "192.168.254.254", "wimax")

        self.tl = udp.Node.UDPComponent(self, "UDP."+str(_id), self.nl.dataTransmission, self.nl.notification);

        self.load = constanze.Node.ConstanzeComponent(self, "constanze")
        self.mobility = rise.Mobility.Component(node = self, name = "mobility UT"+str(_id), mobility = _config.riseMobility)



class RemoteStationTLAppl(wns.Node.Node):
    phy = None
    dll = None
    nl  = None
    tl = None
    load = None
    mobility = None

    def __init__(self, _id, _config):
        super(RemoteStationTLAppl, self).__init__("UT"+str(_id))
        transceiver = Transceiver(_config)
        #self.phy = None
        # create the WIMAX DLL
        self.dll = Stations.RemoteStation(self, _config)#, ring = 4)
        self.dll.setStationID(_id)
        phyStation = OFDMAStation([transceiver.receiver['UT']], [transceiver.transmitter['UT']],
                                  eirpLimited = _config.eirpLimited,
                                  noOfAntenna = _config.parametersSystem.numberOfAntennaUTRxTx,
                                  arrayLayout = _config.arrayLayout,
                                  positionErrorVariance = _config.positionErrorVariance)
        phyStation.txFrequency = _config.parametersSystem.centerFrequency
        phyStation.rxFrequency = _config.parametersSystem.centerFrequency
        phyStation.txPower = _config.parametersSystem.txPowerUT
        phyStation.numberOfSubCarrier = _config.parametersPhy.subchannels
        phyStation.bandwidth = _config.parametersPhy.channelBandwidth
        phyStation.systemManagerName = 'ofdma'
        self.phy = OFDMAComponent(self, "phy", phyStation)
        self.dll.setPhyDataTransmission(self.phy.dataTransmission)
        self.dll.setPhyNotification(self.phy.notification)
        # create Network Layer and Loadgen
        domainName = "RS" + str(_id) + ".wimax.wns.org"
        self.nl = ip.Component.IPv4Component(self, domainName + ".ip", domainName)
        self.nl.addDLL(_name = "wimax",
                       # Where to get IP Adresses
                       _addressResolver = ip.AddressResolver.VirtualDHCPResolver("WIMAXRAN"),
                       # Name of ARP zone
                       _arpZone = "WIMAXRAN",
                       # We cannot deliver locally to other UTs without going to the gateway
                       _pointToPoint = True,
                       _dllDataTransmission = self.dll.dataTransmission,
                       _dllNotification = self.dll.notification)

        self.nl.addRoute("0.0.0.0", "0.0.0.0", "192.168.254.254", "wimax")

        self.tl = udp.Node.UDPComponent(self, "UDP."+str(_id), self.nl.dataTransmission, self.nl.notification);

        self.load = constanze.Node.ConstanzeComponent(self, "constanze")
        self.mobility = rise.Mobility.Component(node = self, name = "mobility UT"+str(_id), mobility = _config.riseMobility)



class RANG(wns.Node.Node):
    dll = None
    nl  = None
    load = None

    def __init__(self):
        super(RANG, self).__init__("RANG")
        # create dll for Rang
        self.dll = wimac.Rang.RANG(self)
        self.dll.setStationID((256*255)-1)

        # create Network Layer and Loadgen
        domainName = "RANG.wimax.wns.org"
        self.nl = ip.Component.IPv4Component(self, domainName + ".ip",domainName)

        self.nl.addDLL(_name = "tun",
                       # Where to get my IP Address
                       _addressResolver = ip.AddressResolver.FixedAddressResolver("192.168.254.254", "255.255.0.0"),
                       # ARP zone
                       _arpZone = "WIMAXRAN",
                       # We can deliver locally
                       _pointToPoint = False,
                       # DLL service names
                       _dllDataTransmission = self.dll.dataTransmission,
                       _dllNotification = self.dll.notification)

        self.load = constanze.Node.ConstanzeComponent(self, "constanze")



class RANGTLAppl(wns.Node.Node):
    dll = None
    nl  = None
    tl = None
    load = None

    def __init__(self):
        super(RANGTLAppl, self).__init__("RANG")
        # create Tunnel to reach the APs
        #self.tunnel = wimac.Tunnel.RANG(self)
        self.dll = wimac.Rang.RANG(self)
        self.dll.setStationID((256*255)-1)
        # create Network Layer and Loadgen

        self.nl = ip.Component.IPv4Component(self, "192.168.255.254", "192.168.255.254")
        self.nl.addDLL("192.168.255.254", self.dll.dataTransmission, self.dll.notification)

        self.tl = udp.Node.UDPComponent(self, "UDP.RANG", self.nl.dataTransmission, self.nl.notification);

        self.load = constanze.Node.ConstanzeComponent(self, "constanze")
