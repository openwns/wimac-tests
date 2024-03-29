import openwns
from openwns.pyconfig import Frozen
import openwns.evaluation.default

import scenarios
import scenarios.builders
import scenarios.placer
import scenarios.antenna
import scenarios.channelmodel

import ip
import ip.BackboneHelpers

import wimac.support.nodecreators
import wimac.support.helper
import wimac.evaluation.default
import wimac.support.PostProcessor as PostProcessor

from wimac.support.WiMACParameters import ParametersOFDM, ParametersMAC

import random
random.seed(7)

# Global station id generator
def stationID():
    id = 1
    while (True):
        yield id
        id += 1
        
stationIDs = stationID()

associations = {}

####################################################
###  Distinguished Simulation Settings             #
####################################################
class Config(Frozen):
    # Set basic WiMAX Parameters
    parametersPhy         = ParametersOFDM
    parametersMAC         = ParametersMAC
    
    parametersPhy.slotDuration = 3.0 *  parametersPhy.symbolDuration
    centerFrequency = 5470
    numberOfTimeSlots = 100

    packetSize = 2400.0 
    trafficUL = 5E5 # bit/s per station
    trafficDL = 5E5 # bit/s per station
    
    noIPHeader = True #Set to true to set IP header to 0
    probeWindowSize = 0.01 # Probe per frame
    scheduler = "PropFair" # "PropFair"
    
    settlingTime = 0.0

# General Setup
WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
openwns.setSimulator(WNS)
WNS.maxSimTime = 0.07999 # seconds
WNS.masterLogger.backtrace.enabled = False
WNS.masterLogger.enabled = True
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE
WNS.statusWriteInterval = 30 # in seconds
WNS.probesWriteInterval = 300 # in seconds
        
# Pass WiMAX Phy parameters to wimac::parameter::PHY singleton
WNS.modules.wimac.parametersPHY = Config.parametersPhy
                
WNS.modules.rise.debug.antennas = True                
                
# Create and place the nodes:
# One BS (25m omnidirectional antenna height) with two nodes, one near, one far

bsPlacer = scenarios.placer.HexagonalPlacer(numberOfCircles = 0, interSiteDistance = 100.0, rotate=0.0)
uePlacer = scenarios.placer.LinearPlacer(numberOfNodes = 2, positionsList = [10, 4000])
bsAntenna = scenarios.antenna.IsotropicAntennaCreator([0.0, 0.0, 5.0])
bsCreator = wimac.support.nodecreators.WiMAXBSCreator(stationIDs, Config)
ueCreator = wimac.support.nodecreators.WiMAXUECreator(stationIDs, Config)
channelmodelcreator = scenarios.channelmodel.TestChannelModelCreator()
scenarios.builders.CreatorPlacerBuilder(bsCreator, bsPlacer, bsAntenna, ueCreator, uePlacer, channelmodelcreator)

wimac.support.helper.setupPhy(WNS, Config, "LoS_Test")

# Set the scheduler
wimac.support.helper.setupScheduler(WNS, Config.scheduler)

# Set IP Header to 0 (else it is 20 byte)
if Config.noIPHeader:
    wimac.support.helper.disableIPHeader(WNS)

# Always create uplink traffic, if traffic UL is 0 we sent exacly 
# one packet for initialization
wimac.support.helper.createULPoissonTraffic(WNS, Config.trafficUL, Config.packetSize)

# Only create downlink traffic if we have any
if Config.trafficDL > 0.0:
    wimac.support.helper.createDLPoissonTraffic(WNS, Config.trafficDL, Config.packetSize)

# Configure the window probes
wimac.support.helper.setL2ProbeWindowSize(WNS, Config.probeWindowSize)

# DHCP, ARP, DNS for IP
ip.BackboneHelpers.createIPInfrastructure(WNS, "WIMAXRAN")

utNodes = WNS.simulationModel.getNodesByProperty("Type", "UE")
bsNodes = WNS.simulationModel.getNodesByProperty("Type", "BS")


# Probe configuration
loggingStationIDs = []

for node in utNodes + bsNodes:    
    loggingStationIDs.append(node.dll.stationID)

wimac.evaluation.default.installDebugEvaluation(WNS, loggingStationIDs, Config.settlingTime, "Moments")

#wimac.evaluation.default.installOverFrameOffsetEvaluation(WNS, 
#                                                          Config.parametersPhy.symbolsFrame, 
#                                                          [1], 
#                                                          loggingStationIDs)

# Enable probe showing when which user starts and stops transmitting.
# Produces a lot of output and should only be used for short runs

#wimac.evaluation.default.installScheduleEvaluation(WNS, loggingStationIDs)

openwns.evaluation.default.installEvaluation(WNS)
