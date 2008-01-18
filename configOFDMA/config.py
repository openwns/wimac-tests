import os
import sys
sys.path.append(os.path.join('.','commonConfig'))
sys.path.append(os.path.join('..','commonConfig'))

import rise
import wns.WNS
import wns.Node
import constanze.Constanze
import ip.IP
import ip.AddressResolver
from ip.VirtualARP import VirtualARPServer
from ip.VirtualDHCP import VirtualDHCPServer
from ip.VirtualDNS import VirtualDNSServer

import ofdmaphy.OFDMAPhy
import rise.Scenario
import rise.Mobility
#import plotStations
from wns import Position
from speetcl.probes.AccessList import AccessList
from constanze.Node import IPBinding, IPListenerBinding, Listener
from wns.Frozen import Frozen
from wns.Sealed import Sealed

import Nodes
import Layer2
import wimac.KeyBuilder as CIDKeyBuilder
import wimac.Probes

from support.WiMACParameters import ParametersSystem, ParametersOFDMA, ParametersMAC, ParametersPropagation, ParametersPropagation_NLOS
from support.scenarioSupport import setupRelayScenario
from support.scenarioSupport import calculateScenarioRadius, numberOfAccessPointsForHexagonalScenario
import support.PostProcessor as PostProcessor

import random
random.seed(7)


association = {}


# glue probes are not needed here
#wns.WNS.WNS.modules.glue.probes = {}

####################################################
###  Distinguished Simulation Settings             #
####################################################
class Config(Frozen):
    # Set basic WiMAX Parameters
    parametersSystem      = ParametersSystem
    parametersPhy         = ParametersOFDMA
    parametersMAC         = ParametersMAC
    parametersPropagation = ParametersPropagation
    parametersPhy.subchannels = 8
    parametersPhy.guardSubCarriers = 100
    parametersPhy.dcSubCarrier = 1
    parametersPhy.pilotSubCarrier = 1
    parametersPhy.dataSubCarrier = 900
    parametersPhy.fch = 1

    # WiMAC Layer2 forming
    beamforming = True
    maxBeams = 4
    arrayLayout = "linear"#"circular"
    positionErrorVariance = 0.0
    eirpLimited = False
    friendliness_dBm = "-85 dBm"
    maxBursts = 20

    #only considered for mapsizes not synchronized with actual scheduling strategy
    dlStrategy = "ProportionalFair"
    ulStrategy = "ProportionalFairUL"

    parametersSystem.numberOfAntennaAPTx = 4

    packetSize = 4288 # leads to packets with MTU 576 byte with 40 byte TCP/IP overhead
    trafficUL = 10000000 # bit/s per station
    trafficDL = 10000000

    nSectors = 1
    nCircles = 0
    nBSs = numberOfAccessPointsForHexagonalScenario(nCircles)
    nRSs = 0
    nSSs = 2
    nRmSs = 0

    numberOfStations =  nBSs * ( nRSs + nSSs + nRmSs * nRSs + 1 )

    scenarioXSize = 2 * calculateScenarioRadius(parametersSystem.clusterOrder, nCircles, parametersSystem.cellRadius)
    scenarioYSize = scenarioXSize

    RSDistance = parametersSystem.cellRadius

    writeOutput = True
    operationModeRelays = 'SDM' #'TDM' 'FDM'

#config = Config()
####################################################
# General Simulation settings                      #
####################################################

# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = wns.WNS.WNS()
WNS.maxSimTime = 0.5 # seconds
#Probe settings
WNS.PDataBase.settlingTime = 0.0
WNS.masterLogger.backtrace.enabled = False
WNS.masterLogger.enabled = True
#WNS.masterLogger.loggerChain = [ wns.Logger.FormatOutputPair( wns.Logger.Console(), wns.Logger.File()) ]
WNS.outputStrategy = wns.WNS.OutputStrategy.DELETE
WNS.statusWriteInterval = 120 # in seconds
WNS.probesWriteInterval = 3600 # in seconds


####################################################
### PHY (PHysical Layer) settings                  #
####################################################
riseConfig = WNS.modules.rise
riseConfig.debug.transmitter = False
riseConfig.debug.main = False
riseConfig.debug.antennas = False

# from ./modules/phy/OFDMAPhy--unstable--0.3/PyConfig/ofdmaphy/OFDMAPhy.py
ofdmaPhyConfig = WNS.modules.ofdmaPhy
ofdmaPhySystem = ofdmaphy.OFDMAPhy.OFDMASystem('ofdma')
ofdmaPhySystem.Scenario = rise.Scenario.Scenario(Config.scenarioXSize, Config.scenarioYSize)
ofdmaPhyConfig.systems.append(ofdmaPhySystem)

####################################################
### WiMAC settings                                 #
####################################################

WNS.modules.wimac.parametersPHY = Config.parametersPhy

####################################################
### Instantiating Nodes and setting Traffic        #
####################################################
# one RANG
rang = Nodes.RANG()

## Registry Proxy of the Scheduler does Space-Time-Sectorization
spaceTimeSectorization = False
if(spaceTimeSectorization):
    # you should better use a circular array layout
    wimac.Scheduler.SpaceTimeSectorizationRegistryProxy.numberOfSectors = 2
    wimac.Scheduler.SpaceTimeSectorizationRegistryProxy.numberOfSubsectors = 1
    wimac.Scheduler.Scheduler.registry = wimac.Scheduler.SpaceTimeSectorizationRegistryProxy

# BSs with some SSs each

def stationID():
    id = 1
    while (True):
        yield id
        id += 1

stationIDs = stationID()

accessPoints = []

for i in xrange(Config.nBSs):
    bs = Nodes.BaseStation(stationIDs.next(), Config)
    bs.dll.logger.level = 3
    bs.dll.centerFrequency = Config.parametersSystem.centerFrequency
    bs.dll.bandwidth = Config.parametersPhy.channelBandwidth
    bs.dll.subCarriers = Config.parametersPhy.subchannels
    accessPoints.append(bs)
    association[bs]=[]
    WNS.nodes.append(bs)

# The RANG only has one IPListenerBinding that is attached
# to the listener. The listener is the only traffic sink
# within the RANG
ipListenerBinding = IPListenerBinding(rang.nl.domainName)
listener = Listener(rang.nl.domainName + ".listener")
rang.load.addListener(ipListenerBinding, listener)

userTerminals = []
k = 0
for bs in accessPoints:
    bs.dll.ring = 0
    for i in xrange(Config.nSSs):
        ss = Nodes.SubscriberStation(stationIDs.next(), Config)
        ss.dll.ring = 1
        ss.dll.centerFrequency = bs.dll.centerFrequency
        ss.dll.bandwidth = bs.dll.bandwidth
        ss.dll.subCarriers = bs.dll.subCarriers
        cbrDL = constanze.Constanze.CBR(offset = 0.05, throughput = Config.trafficDL, packetSize = Config.packetSize)
        ipBinding = IPBinding(rang.nl.domainName, ss.nl.domainName)
        rang.load.addTraffic(ipBinding, cbrDL)

        cbrUL = constanze.Constanze.CBR(offset = 0.0, throughput = Config.trafficUL, packetSize = Config.packetSize)
        ipBinding = IPBinding(ss.nl.domainName, rang.nl.domainName)
        ss.load.addTraffic(ipBinding, cbrUL)
        ipListenerBinding = IPListenerBinding(ss.nl.domainName)
        listener = Listener(ss.nl.domainName + ".listener")
        ss.load.addListener(ipListenerBinding, listener)
        ss.dll.associate(bs.dll)
        association[bs].append(ss)
        userTerminals.append(ss)
        WNS.nodes.append(ss)
    rang.dll.addAP(bs)
    k += 1

# each access point is connected to some fixed relay stations
k = 0
relayStations = []
for bs in accessPoints:
    l = 0
    for i in xrange(Config.nRSs):
        rs = Nodes.RelayStation(stationIDs.next(), Config)
        rs.dll.associate(bs.dll)
        rs.dll.ring = 2
        rs.dll.centerFrequency = bs.dll.centerFrequency
        rs.dll.bandwidth = bs.dll.bandwidth
        rs.dll.subCarriers = bs.dll.subCarriers
        association[rs]=[]
        association[bs].append(rs)
        relayStations.append(rs)
        WNS.nodes.append(rs)

        l += 1
    k += 1

# each relay station is connected to some remote stations
remoteStations = []
k = 0
for bs in accessPoints:
    l = 0
    for rs in associations[bs]:
        if rs.dll.stationType != 'FRS':
            continue
        i = 0
        for i in xrange(Config.nRmSs):
            ss = Nodes.SubscriberStation(stationIDs.next(), Config)
            ss.dll.logger.level = 3
            ss.dll.ring = rs.dll.ring + 1
            ss.dll.centerFrequency = rs.dll.centerFrequency
            ss.dll.bandwidth = rs.dll.bandwidth
            ss.dll.subCarriers = rs.dll.subCarriers
            cbrDL = constanze.Constanze.CBR(offset = 0.05, throughput = Config.trafficDL, packetSize = Config.packetSize)
            ipBinding = IPBinding(rang.nl.domainName, ss.nl.domainName)
            rang.load.addTraffic(ipBinding, cbrDL)

            cbrUL = constanze.Constanze.CBR(offset = 0.0, throughput = Config.trafficUL, packetSize = Config.packetSize)
            ipBinding = IPBinding(ss.nl.domainName, rang.nl.domainName)
            ss.load.addTraffic(ipBinding, cbrUL)
            ipListenerBinding = IPListenerBinding(ss.nl.domainName)
            listener = Listener(ss.nl.domainName + ".listener")
            ss.load.addListener(ipListenerBinding, listener)

            ss.dll.associate(rs.dll)
            # 192.168.1.254 = "nl address of RANG" = rang.nl.address ?
            association[rs].append(ss)
            remoteStations.append(ss)
            WNS.nodes.append(ss)
        l += 1
    k += 1

WNS.nodes.append(rang)

# Positions of the stations are determined here
setupRelayScenario(Config, WNS.nodes, association)

#set mobility
intracellMobility = False

if(intracellMobility):
    utfile = open("posSS.junk","w")

    for ss in userTerminals:
        associatedBS = None
        for bs in accessPoints:
            if bs.dll.stationID == ss.dll.associateTo:
                associatedBS = bs
                bsPos = associatedBS.mobility.mobility.getCoords()
                break
        if associatedBS == None:
            print 'no associated BS found'
            exit(1)

        # too large, SS might be outside the hexagon
        maxDistance_ = Config.parametersSystem.cellRadius
        # too small, corners are not filled
        # maxDistance_ = (math.sqrt(3.0)/2.0) * Config.parametersSystem.cellRadius
        # equal area
        # maxDistance_ = math.sqrt( 3.0/2.0/math.pi*math.sqrt(3.0)) * Config.parametersSystem.cellRadius
        ss.mobility.mobility = rise.Mobility.BrownianCirc(center=bsPos,
                                                          maxDistance = maxDistance_ )
        utfile.write(str(ss.dll.stationID)+"\t" +
                     str(ss.mobility.mobility.getCoords().x)+"\t"+str(ss.mobility.mobility.getCoords().y)+"\t" +
                     str(math.hypot(ss.mobility.mobility.getCoords().x - bsPos.x ,ss.mobility.mobility.getCoords().y - bsPos.y)) +
                     "\n")

# TODO: for multihop simulations: replicate the code for remote stations

#plotStations.plot()


# Here we specify the stations we want to probe.
# This is usually only the center cell with the BS and its associated stations.
loggingStationIDs = []

for st in associations[accessPoints[0]]:
    if st.dll.stationType == 'FRS':
        loggingStationIDs.append(st.dll.stationID)
        for st2 in associations[st]:
            if st2.dll.stationType == 'UT':
                loggingStationIDs.append(st2.dll.stationID)

    if st.dll.stationType == 'UT':
        loggingStationIDs.append(st.dll.stationID)

WNS.modules.wimac.probes = wimac.Probes.getProbesDict([1], loggingStationIDs)


# one Virtual ARP Zone
varp = VirtualARPServer("vARP", "WIMAXRAN")
WNS.nodes = [varp] + WNS.nodes

vdhcp = VirtualDHCPServer("vDHCP@",
                          "WIMAXRAN",
                          "192.168.0.2", "192.168.254.253",
                          "255.255.0.0")

vdns = VirtualDNSServer("vDNS", "ip.DEFAULT.GLOBAL")
WNS.nodes.append(vdns)

WNS.nodes.append(vdhcp)

### PostProcessor ###
postProcessor = PostProcessor.WiMACPostProcessor()
postProcessor.Config = Config
postProcessor.accessPoints = accessPoints
postProcessor.relayStations = relayStations
postProcessor.userTerminals = userTerminals
postProcessor.remoteStations = remoteStations
WNS.addPostProcessing(postProcessor)
