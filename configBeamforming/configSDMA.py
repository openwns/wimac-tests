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

from wimac.support.Parameters16m import ParametersOFDMA, ParametersMAC, ParametersSystem

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
    parametersPhy    = ParametersOFDMA(bandwidth = 5)
    parametersMAC    = ParametersMAC
    
    parametersPhy.slotDuration = 6 *  parametersPhy.symbolDuration
    centerFrequency = ParametersSystem.centerFrequency
    # 3 * 6 = 18 symbols UD and 18 DL, total of 36 symbols. Other 47 - 36 = 11 symbols
    # are for PYH, control, and management traffic
    parametersPhy.maximalBeams = 2
    parametersPhy.beamforming = True
    numberOfTimeSlots = 3 

    packetSize = 800.0 
    trafficUL = 5E5 # bit/s per station
    trafficDL = 5E5 # bit/s per station
    
    noIPHeader = True #Set to true to set IP header to 0
    probeWindowSize = 0.01 # Probe per frame
    scheduler = "Fixed"#"RoundRobin" # "PropFair"

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

bsPlacer = scenarios.placer.HexagonalPlacer(numberOfCircles = 0, interSiteDistance = 1000.0, rotate=0.0)
uePlacer = scenarios.placer.PositionListPlacer(numberOfNodes = 2, positionsList = [
                                                openwns.geometry.position.Position(x = 2000.0, y = 0.0), 
                                                openwns.geometry.position.Position(x = 0.0, y = 10.0)],
                                                #openwns.geometry.position.Position(x = 0.0, y = 500.0)], 
                                                rotate = 0.0)
bsAntenna = scenarios.antenna.IsotropicAntennaCreator([0.0, 0.0, 1.5])
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

wimac.evaluation.default.installDebugEvaluation(WNS, loggingStationIDs, "Moments")

openwns.evaluation.default.installEvaluation(WNS)
