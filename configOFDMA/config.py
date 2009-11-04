import os
import sys
sys.path.append(os.path.join('.','commonConfig'))
sys.path.append(os.path.join('..','commonConfig'))

import rise
import openwns.node
import openwns
import openwns.evaluation.default
import constanze.traffic
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

import Nodes
import Layer2
import wimac.KeyBuilder as CIDKeyBuilder
import wimac.evaluation.default

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

    parametersPhy.subchannels = 1

    # WiMAC Layer2 forming
    beamforming = False
    maxBeams = 1
    friendliness_dBm = "-85 dBm"
    maxBursts = 20

    #only considered for mapsizes not synchronized with actual scheduling strategy
    dlStrategy = "ProportionalFairDL"
    ulStrategy = "ProportionalFairUL"

    arrayLayout = "linear" #"circular"
    eirpLimited = False
    positionErrorVariance = 0.0

    packetSize = 100 #in bit
    trafficUL = 5000000 # bit/s per station
    trafficDL = 5000000

    oldPFScheduler = False

    nSectors = 1
    nCircles = 0
    nBSs = numberOfAccessPointsForHexagonalScenario(nCircles)
    nRSs = 0
    nSSs = 2
    nRmSs = 0

    numberOfStations =  nBSs * ( nRSs + nSSs + nRmSs * nRSs + 1 )

    scenarioXSize = 2 * calculateScenarioRadius(parametersSystem.clusterOrder, nCircles, parametersSystem.cellRadius)
    scenarioYSize = scenarioXSize

    RSDistance = parametersSystem.cellRadius / 2.0

    writeOutput = True
    operationModeRelays = 'SDM' #'TDM' 'FDM'

####################################################
# General Simulation settings                      #
####################################################

assert Config.nSSs == 1 or Config.nSSs == 2, "Only 1 or 2 SSs possible"

# create an instance of the WNS configuration
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
WNS.maxSimTime = 0.1 # seconds

WNS.masterLogger.backtrace.enabled = False
WNS.masterLogger.enabled = True
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE
WNS.statusWriteInterval = 30 # in seconds
WNS.probesWriteInterval = 30 # in seconds


####################################################
### PHY (PHysical Layer) settings                  #
####################################################
riseConfig = WNS.modules.rise
riseConfig.debug.transmitter = False
riseConfig.debug.main = False
riseConfig.debug.antennas = False

ofdmaPhyConfig = WNS.modules.ofdmaPhy
ofdmaPhySystem = ofdmaphy.OFDMAPhy.OFDMASystem('ofdma')
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
        poisDL = constanze.traffic.Poisson(offset = 0.05, throughput = Config.trafficDL, packetSize = Config.packetSize)
        ipBinding = IPBinding(rang.nl.domainName, ss.nl.domainName)
        rang.load.addTraffic(ipBinding, poisDL)

        if Config.trafficUL > 0.0:
            poisUL = constanze.traffic.Poisson(offset = 0.0, 
                                            throughput = Config.trafficUL, 
                                            packetSize = Config.packetSize)
        else:
            # Send one PDU to establish connection
            poisUL = constanze.traffic.CBR0(duration = 1E-6)                                            
            
        ipBinding = IPBinding(ss.nl.domainName, rang.nl.domainName)
        ss.load.addTraffic(ipBinding, poisUL)
        ipListenerBinding = IPListenerBinding(ss.nl.domainName)
        listener = Listener(ss.nl.domainName + ".listener")
        ss.load.addListener(ipListenerBinding, listener)
        ss.dll.associate(bs.dll)
        associations[bs].append(ss)
        userTerminals.append(ss)
        WNS.simulationModel.nodes.append(ss)
    rang.dll.addAP(bs)
    k += 1

WNS.simulationModel.nodes.append(rang)

# Positions of the stations are determined here
setupRelayScenario(Config, WNS.simulationModel.nodes, associations)

bsPos =  accessPoints[0].mobility.mobility.getCoords()

userTerminals[0].mobility.mobility.setCoords(bsPos + openwns.geometry.position.Position(10,0,0))
print "BSPos:" + str(bsPos)
print "UT1Pos:" + str(userTerminals[0].mobility.mobility.getCoords())

if Config.nSSs == 2:
    userTerminals[1].mobility.mobility.setCoords(bsPos + openwns.geometry.position.Position(1600,0,0))
    print "UT2Pos:" + str(userTerminals[1].mobility.mobility.getCoords())

# Here we specify the stations we want to probe.
loggingStationIDs = []

for st in associations[accessPoints[0]]:
    if st.dll.stationType == 'FRS':
        loggingStationIDs.append(st.dll.stationID)
        for st2 in associations[st]:
            if st2.dll.stationType == 'UT':
                loggingStationIDs.append(st2.dll.stationID)

    if st.dll.stationType == 'UT':
        loggingStationIDs.append(st.dll.stationID)

sources = ["wimac.top.window.incoming.bitThroughput", 
            "wimac.top.window.aggregated.bitThroughput", 
            "wimac.cirSDMA",
            "wimac.top.packet.incoming.delay"]

for src in sources:
    
    node = openwns.evaluation.createSourceNode(WNS, src)
    nodeBS = node.appendChildren(openwns.evaluation.generators.Accept(
                        by = 'MAC.StationType', ifIn = [1], suffix = "BS"))
    #nodeRS = node.appendChildren(openwns.evaluation.generators.Accept(
    #                    by = 'MAC.StationType', ifIn = [2], suffix = "RS"))
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

openwns.evaluation.default.installEvaluation(WNS)

#Warp2Gui Probe
node = openwns.evaluation.createSourceNode(WNS, "wimac.guiProbe")
node.appendChildren(openwns.evaluation.generators.TextTrace("guiText", ""))

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

openwns.setSimulator(WNS)
