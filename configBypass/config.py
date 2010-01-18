import os
import sys
sys.path.append(os.path.join('.','commonConfig'))
sys.path.append(os.path.join('..','commonConfig'))

import rise
import openwns.node
import openwns
import openwns.evaluation.default
import constanze.traffic
import openwns.logger
import ip.IP
import ip.AddressResolver
from ip.VirtualARP import VirtualARPServer
from ip.VirtualDHCP import VirtualDHCPServer
from ip.VirtualDNS import VirtualDNSServer

import ofdmaphy.OFDMAPhy
import rise.Scenario
import rise.Mobility
from constanze.node import IPBinding, IPListenerBinding, Listener
from openwns.pyconfig import Frozen
from openwns.pyconfig import Sealed

import wimac.support.Nodes
import wimac.KeyBuilder as CIDKeyBuilder
import wimac.evaluation.default

from wimac.support.WiMACParameters import ParametersSystem, ParametersOFDM, ParametersMAC, ParametersPropagation
from wimac.support.scenarioSupport import setupRelayScenario
from wimac.support.scenarioSupport import calculateScenarioRadius, numberOfAccessPointsForHexagonalScenario
import wimac.support.PostProcessor as PostProcessor

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

    parametersPhy.slotDuration = 3.0 *  parametersPhy.symbolDuration

    # WiMAC Layer2 forming
    beamforming = False
    maxBeams = 1
    friendliness_dBm = "-85 dBm"
    maxBursts = 20

    #only considered for mapsizes not synchronized with actual scheduling strategy
    dlStrategy = "ProportionalFairDL"
    ulStrategy = "ProportionalFairUL"

    arrayLayout = "circular" #"linear"
    eirpLimited = False
    positionErrorVariance = 0.0

    packetSize = 240.0 # Max 240 if noIPHeader = True, else 80
    trafficUL = 5E5 # bit/s per station
    trafficDL = 5E5 # bit/s per station
    noIPHeader = True #Set to true to set IP header to 0
    probeWindowSize = 0.01 # Probe per frame

    nSectors = 1
    nCircles = 0
    nBSs = numberOfAccessPointsForHexagonalScenario(nCircles)
    nRSs = 0 # Must be 0
    nSSs = 2
    nRmSs = 0 # Must be 0

    numberOfStations =  nBSs * ( nRSs + nSSs + nRmSs * nRSs + 1 )

    scenarioXSize = 2 * calculateScenarioRadius(parametersSystem.clusterOrder, nCircles, parametersSystem.cellRadius)
    scenarioYSize = scenarioXSize

    RSDistance = parametersSystem.cellRadius / 2.0

    writeOutput = True
    operationModeRelays = 'SDM' #'TDM' 'FDM'
    numberOfTimeSlots = 100

#config = Config()
####################################################
# General Simulation settings                      #
####################################################

# create an instance of the WNS configuration
# The variable must be called WNS!!!!
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.maxSimTime = 0.07999 # seconds

# Logger settings
WNS.masterLogger.backtrace.enabled = False
WNS.masterLogger.enabled = True
#format = openwns.logger.Console()
#format.colors = openwns.logger.ColorMode.Off
#WNS.masterLogger.loggerChain = [ openwns.logger.FormatOutputPair( format, openwns.logger.File()) ]
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE

# Probe settings

WNS.statusWriteInterval = 30 # in seconds
WNS.probesWriteInterval = 300 # in seconds


####################################################
### PHY (PHysical Layer) settings                  #
####################################################
riseConfig = WNS.modules.rise
riseConfig.debug.transmitter = False
riseConfig.debug.main = False
riseConfig.debug.antennas = False

# from ./modules/phy/OFDMAPhy--unstable--0.3/PyConfig/ofdmaphy/OFDMAPhy.py
#scenario = rise.scenario.Hexagonal.Hexagonal(config.clusterSize, config.center, config.numOfCircles, config.cellRadius, config.numRN, nUT, config.distanceBetweenBSs, config.distanceBetweenBSandRN, nSectorsBS=1, corrAngle=0.0, rnShiftAngle=config.RN_Shift_Angle, useWraparound = config.useWraparound)
ofdmaPhyConfig = WNS.modules.ofdmaPhy
ofdmaPhySystem = ofdmaphy.OFDMAPhy.OFDMASystem('ofdma')
#ofdmaPhySystem.Scenario = rise.Scenario.Scenario(Config.scenarioXSize, Config.scenarioYSize)
ofdmaPhySystem.Scenario = rise.Scenario.Scenario()
ofdmaPhyConfig.systems.append(ofdmaPhySystem)

####################################################
### WiMAC settings                                 #
####################################################

WNS.modules.wimac.parametersPHY = Config.parametersPhy

####################################################
### Instantiating Nodes and setting Traffic        #
####################################################
# one RANG
rang = wimac.support.Nodes.RANG()
rang.nl.logger.level = 1
                                        
if Config.noIPHeader:
    rang.nl.ipHeader.config.headerSize = 0

# BSs with some SSs each

def stationID():
    id = 1
    while (True):
        yield id
        id += 1

stationIDs = stationID()

accessPoints = []

for i in xrange(Config.nBSs):
    bs = wimac.support.Nodes.BaseStation(stationIDs.next(), Config)
                
    # Use the Bypass Queue
    # DL Master
    bs.dll.dlscheduler.config.txScheduler.queue = wimac.Scheduler.BypassQueue()
    bs.dll.dlscheduler.config.txScheduler.alwaysAcceptIfQueueAccepts = True

    # Use the Simple Queue
    # UL Master
    bs.dll.ulscheduler.config.rxScheduler.queue = openwns.Scheduler.SimpleQueue()
    bs.dll.ulscheduler.config.rxScheduler.alwaysAcceptIfQueueAccepts = True        

    bs.dll.subFUN.connects.pop(0)
    bs.dll.group.bottom = "buffer"

    bs.dll.topTpProbe.config.windowSize = Config.probeWindowSize
    bs.dll.topTpProbe.config.sampleInterval = Config.probeWindowSize
    
    # We need PseudeBWRequests with the Bypass Queue
    bs.dll.ulscheduler.config.rxScheduler.pseudoGenerator = wimac.Scheduler.PseudoBWRequestGenerator(
                'connectionManager',
                'ulscheduler',
                _packetSize = Config.packetSize,
                _pduOverhead = Config.parametersMAC.pduOverhead)

    if Config.noIPHeader:
        bs.dll.ulscheduler.config.rxScheduler.pseudoGenerator.pduOverhead -= 160
    
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
        ss = wimac.support.Nodes.SubscriberStation(stationIDs.next(), Config)
        
        # Use the Bypass Queue
        # UL Slave
        ss.dll.ulscheduler.config.txScheduler.queue = wimac.Scheduler.BypassQueue()
	ss.dll.ulscheduler.config.txScheduler.alwaysAcceptIfQueueAccepts = True
        
        
        ss.dll.subFUN.connects.pop(0)
        ss.dll.group.bottom = "buffer"

        
        ss.dll.topTpProbe.config.windowSize = Config.probeWindowSize
        ss.dll.topTpProbe.config.sampleInterval = Config.probeWindowSize
        
        if Config.trafficDL > 0.0:
            poisDL = constanze.traffic.Poisson(offset = 0.05, 
                throughput = Config.trafficDL, 
                packetSize = Config.packetSize)
            ipBinding = IPBinding(rang.nl.domainName, ss.nl.domainName)
            rang.load.addTraffic(ipBinding, poisDL)

        if Config.trafficUL > 0.0:
            poisUL = constanze.traffic.Poisson(offset = 0.0, 
                                            throughput = Config.trafficUL, 
                                            packetSize = Config.packetSize)
        else:
            # Send one PDU to establish connection
            poisUL = constanze.traffic.CBR0(duration = 15E-3, 
                                            packetSize = Config.packetSize, 
                                            throughput = 1.0)
            
        ipBinding = IPBinding(ss.nl.domainName, rang.nl.domainName)
        ss.load.addTraffic(ipBinding, poisUL)
        ipListenerBinding = IPListenerBinding(ss.nl.domainName)
        listener = Listener(ss.nl.domainName + ".listener")
        ss.load.addListener(ipListenerBinding, listener)
        
        if Config.noIPHeader:
            ss.nl.ipHeader.config.headerSize = 0
        
        ss.nl.logger.level = 1
            
        ss.dll.associate(bs.dll)
        associations[bs].append(ss)
        userTerminals.append(ss)
        WNS.simulationModel.nodes.append(ss)
    rang.dll.addAP(bs)
    k += 1

# TODO Reenable relays

# each access point is connected to some fixed relay stations
#k = 0
#relayStations = []
#for bs in accessPoints:
    #l = 0
    #for i in xrange(Config.nRSs):
        #rs = wimac.support.Nodes.RelayStation(stationIDs.next(), Config)
        #rs.dll.associate(bs.dll)
        #associations[rs]=[]
        #associations[bs].append(rs)
        #relayStations.append(rs)
        #WNS.simulationModel.nodes.append(rs)

        #l += 1
    #k += 1

# each relay station is connected to some remote stations
#remoteStations = []
#k = 0
#for bs in accessPoints:
    #l = 0
    #for rs in associations[bs]:
        #if rs.dll.stationType != 'FRS':
            #continue
        #i = 0
        #for i in xrange(Config.nRmSs):
            #ss = wimac.support.Nodes.SubscriberStation(stationIDs.next(), Config)
            #ss.dll.logger.level = 2
            #cbrDL = constanze.traffic.CBR(offset = 0.05, throughput = Config.trafficDL, packetSize = Config.packetSize)
            #ipBinding = IPBinding(rang.nl.domainName, ss.nl.domainName)
            #rang.load.addTraffic(ipBinding, cbrDL)

            #cbrUL = constanze.traffic.CBR(offset = 0.0, throughput = Config.trafficUL, packetSize = Config.packetSize)
            #ipBinding = IPBinding(ss.nl.domainName, rang.nl.domainName)
            #ss.load.addTraffic(ipBinding, cbrUL)
            #ipListenerBinding = IPListenerBinding(ss.nl.domainName)
            #listener = Listener(ss.nl.domainName + ".listener")
            #ss.load.addListener(ipListenerBinding, listener)

            #ss.dll.associate(rs.dll)
            ## 192.168.1.254 = "nl address of RANG" = rang.nl.address ?
            #associations[rs].append(ss)
            #remoteStations.append(ss)
            #WNS.simulationModel.nodes.append(ss)
        #l += 1
    #k += 1

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

bsPos =  accessPoints[0].mobility.mobility.getCoords()

userTerminals[0].mobility.mobility.setCoords(bsPos + openwns.geometry.position.Position(10,0,0))
if Config.nSSs == 2:
    userTerminals[1].mobility.mobility.setCoords(bsPos + openwns.geometry.position.Position(1700,0,0))

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

wimac.evaluation.default.installDebugEvaluation(WNS, loggingStationIDs)
#wimac.evaluation.default.installEvaluation(WNS, [1], loggingStationIDs)

symbolsInFrame = Config.parametersPhy.symbolsFrame
wimac.evaluation.default.installOverFrameOffsetEvaluation(WNS, symbolsInFrame, [accessPoints[0].dll.stationID], loggingStationIDs)

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
WNS.environment.probeBusRegistry.removeMeasurementSource("wimac.schedulerQueue.delay")

### PostProcessor ###
postProcessor = PostProcessor.WiMACPostProcessor()
postProcessor.Config = Config
postProcessor.accessPoints = accessPoints
#postProcessor.relayStations = relayStations
postProcessor.userTerminals = userTerminals
#postProcessor.remoteStations = remoteStations
WNS.addPostProcessing(postProcessor)
openwns.setSimulator(WNS)
