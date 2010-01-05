import os
import sys
sys.path.append(os.path.join('.','commonConfig'))
sys.path.append(os.path.join('..','commonConfig'))

import rise
import openwns.node
import openwns
import openwns.evaluation.default
import openwns.Scheduler
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

    packetSize = 239.0 # Max 240 if noIPHeader = True, else 80
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
WNS.maxSimTime = 10.0 #0.07999 # seconds

# Logger settings
WNS.masterLogger.backtrace.enabled = False
WNS.masterLogger.enabled = True
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
    
    bs.dll.topTpProbe.config.windowSize = Config.probeWindowSize
    bs.dll.topTpProbe.config.sampleInterval = Config.probeWindowSize
    
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
print "BSPos:" + str(bsPos)
print "UT1Pos:" + str(userTerminals[0].mobility.mobility.getCoords())
if Config.nSSs == 2:
	userTerminals[1].mobility.mobility.setCoords(bsPos + openwns.geometry.position.Position(1700,0,0))
	print "UT2Pos:" + str(userTerminals[1].mobility.mobility.getCoords())

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

sources = [] #["wimac.top.window.incoming.bitThroughput", 
             #"wimac.top.window.aggregated.bitThroughput", 
             #"wimac.cirSDMA",
             #"wimac.top.packet.incoming.delay"]

for src in sources:
    
     node = openwns.evaluation.createSourceNode(WNS, src)
     nodeBS = node.appendChildren(openwns.evaluation.generators.Accept(
                         by = 'MAC.StationType', ifIn = [1], suffix = "BS"))
     nodeUT = node.appendChildren(openwns.evaluation.generators.Accept(
                         by = 'MAC.StationType', ifIn = [3], suffix = "UT"))
     nodeBS.appendChildren(openwns.evaluation.generators.Separate(
                         by = 'MAC.Id', forAll = [1], format = "Id%d"))                    
     nodeUT.appendChildren(openwns.evaluation.generators.Separate(
                         by = 'MAC.Id', forAll = loggingStationIDs, format = "Id%d"))
                        
     if src == "wimac.cirSDMA":
         node.getLeafs().appendChildren(openwns.evaluation.generators.PDF(
                                                     minXValue = -100,
                                                     maxXValue = 100,
                                                     resolution =  2000))
     elif "window" in src:                          
         node.getLeafs().appendChildren(openwns.evaluation.generators.PDF(
                                                     minXValue = 0.0,
                                                     maxXValue = 120.0e+6,
                                                     resolution =  1000))
                                       
     elif "packet" in src:                          
         node.getLeafs().appendChildren(openwns.evaluation.generators.PDF(
                                                     minXValue = 0.0,
                                                     maxXValue = 1.0,
                                                     resolution =  100))

wimac.evaluation.default.installDebugEvaluation(WNS, loggingStationIDs)

symbolsInFrame = Config.parametersPhy.symbolsFrame
wimac.evaluation.default.installOverFrameOffsetEvaluation(WNS, symbolsInFrame, [1], loggingStationIDs)

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
postProcessor.userTerminals = userTerminals
WNS.addPostProcessing(postProcessor)
openwns.setSimulator(WNS)
