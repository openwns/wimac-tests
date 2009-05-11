import os
import sys
sys.path.append(os.path.join('.','commonConfig'))
sys.path.append(os.path.join('..','commonConfig'))

import rise
import openwns
import openwns.node
import constanze.traffic
import ip.IP
import ip.AddressResolver
from ip.VirtualARP import VirtualARPServer
from ip.VirtualDHCP import VirtualDHCPServer
from ip.VirtualDNS import VirtualDNSServer

import ofdmaphy.OFDMAPhy
import rise.Scenario
import rise.Mobility
from openwns import Position
from constanze.node import IPBinding, IPListenerBinding, Listener
from openwns.pyconfig import Frozen
from openwns.pyconfig import Sealed

import Nodes
import Layer2
import wimac.KeyBuilder as CIDKeyBuilder
import wimac.evaluation.default

import openwns.evaluation.default
from support.WiMACParameters import ParametersSystem, ParametersOFDM, ParametersMAC, ParametersPropagation, ParametersPropagation_NLOS
from support.scenarioSupport import setupRelayScenario
from support.scenarioSupport import calculateScenarioRadius, numberOfAccessPointsForHexagonalScenario
import support.PostProcessor as PostProcessor

import random
random.seed(7)


associations = {}

####################################################
###  Distinguished Simulation Settings             #
####################################################
class Config(Frozen):
    # Set basic WiMAX Parameters
    parametersSystem      = ParametersSystem
    parametersPhy         = ParametersOFDM
    parametersMAC         = ParametersMAC
    parametersPropagation = ParametersPropagation

    # WiMAC Layer2 forming
    beamforming = True
    maxBeams = 4
    arrayLayout = "linear"#"circular"
    positionErrorVariance = 0.0
    eirpLimited = False
    friendliness_dBm = "-85 dBm"
    maxBursts = 20

    #only considered for mapsizes not synchronized with actual scheduling strategy
    dlStrategy = "ProportionalFairDL"
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
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.maxSimTime = 0.5 # seconds
#Probe settings
WNS.masterLogger.backtrace.enabled = False
WNS.masterLogger.enabled = False
#WNS.masterLogger.loggerChain = [ wns.Logger.FormatOutputPair( openwns.logger.Console(), openwns.logger.File()) ]
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE
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
    bs.dll.logger.level = 2
    accessPoints.append(bs)
    associations[bs]=[]
    WNS.simulationModel.nodes.append(bs)

# The RANG only has one IPListenerBinding that is attached
# to the listener. The listener is the only traffic sink
# within the RANG
ipListenerBinding = IPListenerBinding(rang.nl.domainName)
listener = Listener(rang.nl.domainName + ".listener")
rang.load.addListener(ipListenerBinding, listener)

userTerminals = []
k = 0
for bs in accessPoints:
    for i in xrange(Config.nSSs):
        ss = Nodes.SubscriberStation(stationIDs.next(), Config)
        cbrDL = constanze.traffic.CBR(offset = 0.05, throughput = Config.trafficDL, packetSize = Config.packetSize)
        ipBinding = IPBinding(rang.nl.domainName, ss.nl.domainName)
        rang.load.addTraffic(ipBinding, cbrDL)

        cbrUL = constanze.traffic.CBR(offset = 0.0, throughput = Config.trafficUL, packetSize = Config.packetSize)
        ipBinding = IPBinding(ss.nl.domainName, rang.nl.domainName)
        ss.load.addTraffic(ipBinding, cbrUL)
        ipListenerBinding = IPListenerBinding(ss.nl.domainName)
        listener = Listener(ss.nl.domainName + ".listener")
        ss.load.addListener(ipListenerBinding, listener)
        ss.dll.associate(bs.dll)
        associations[bs].append(ss)
        userTerminals.append(ss)
        WNS.simulationModel.nodes.append(ss)
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
        associations[rs]=[]
        associations[bs].append(rs)
        relayStations.append(rs)
        WNS.simulationModel.nodes.append(rs)

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
            ss.dll.logger.level = 2
            cbrDL = constanze.traffic.CBR(offset = 0.05, throughput = Config.trafficDL, packetSize = Config.packetSize)
            ipBinding = IPBinding(rang.nl.domainName, ss.nl.domainName)
            rang.load.addTraffic(ipBinding, cbrDL)

            cbrUL = constanze.traffic.CBR(offset = 0.0, throughput = Config.trafficUL, packetSize = Config.packetSize)
            ipBinding = IPBinding(ss.nl.domainName, rang.nl.domainName)
            ss.load.addTraffic(ipBinding, cbrUL)
            ipListenerBinding = IPListenerBinding(ss.nl.domainName)
            listener = Listener(ss.nl.domainName + ".listener")
            ss.load.addListener(ipListenerBinding, listener)

            ss.dll.associate(rs.dll)
            # 192.168.1.254 = "nl address of RANG" = rang.nl.address ?
            associations[rs].append(ss)
            remoteStations.append(ss)
            WNS.simulationModel.nodes.append(ss)
        l += 1
    k += 1

WNS.simulationModel.nodes.append(rang)

# Positions of the stations are determined here
setupRelayScenario(Config, WNS.simulationModel.nodes, associations)

#set mobility
intracellMobility = False

if(intracellMobility):

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

wimac.evaluation.default.installEvaluation(WNS, [1], loggingStationIDs)
openwns.evaluation.default.installEvaluation(WNS)

# one Virtual ARP Zone
varp = VirtualARPServer("vARP", "WIMAXRAN")
WNS.simulationModel.nodes = [varp] + WNS.simulationModel.nodes

vdhcp = VirtualDHCPServer("vDHCP@",
                          "WIMAXRAN",
                          "192.168.0.2", "192.168.254.253",
                          "255.255.0.0")

vdns = VirtualDNSServer("vDNS", "ip.DEFAULT.GLOBAL")
WNS.simulationModel.nodes.append(vdns)

WNS.simulationModel.nodes.append(vdhcp)

### PostProcessor ###
postProcessor = PostProcessor.WiMACPostProcessor()
postProcessor.Config = Config
postProcessor.accessPoints = accessPoints
postProcessor.relayStations = relayStations
postProcessor.userTerminals = userTerminals
postProcessor.remoteStations = remoteStations
WNS.addPostProcessing(postProcessor)
openwns.setSimulator(WNS)