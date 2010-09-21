###############################################################################
# This file is part of openWNS (open Wireless Network Simulator)
# _____________________________________________________________________________
#
# Copyright (C) 2004-2008
# Chair of Communication Networks (ComNets)
# Kopernikusstr. 16, D-52074 Aachen, Germany
# phone: ++49-241-80-27910,
# fax: ++49-241-80-22242
# email: info@openwns.org
# www: http://www.openwns.org
# _____________________________________________________________________________
#
# openWNS is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License version 2 as published by the
# Free Software Foundation;
#
# openWNS is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

# This trick assures we use the dummy parameters in 
# ./openwns/wrowser/simdb/SimConfig when in systemTest. 
import sys
import os
sys.path.insert(0, os.getcwd())

import random
random.seed(7)

import openwns
from openwns.pyconfig import Frozen
import openwns.evaluation.default

import scenarios
import scenarios.builders
import scenarios.placer
import scenarios.antenna

import ip
import ip.BackboneHelpers

import wimac.support.nodecreators
import wimac.support.helper
import wimac.evaluation.default
import wimac.support.PostProcessor as PostProcessor
from wimac.support.Parameters16m import ParametersOFDMA, ParametersMAC

from openwns.wrowser.simdb.SimConfig import params

# Global station id generator
def stationID():
    id = 1
    while (True):
        yield id
        id += 1
        
stationIDs = stationID()

associations = {}

###  Distinguished Simulation Settings
class Config(Frozen):
    # Set basic WiMAX Parameters
    parametersPhy         = ParametersOFDMA(bandwidth = 5)
    parametersMAC         = ParametersMAC
    
    packetSize = 1200.0 
    trafficUL = params.offeredTraffic / 2.0 # bit/s per station
    trafficDL = params.offeredTraffic / 2.0 # bit/s per station
    scheduler = params.scheduler
    
    settlingTime = 0.1
    
    numberOfTimeSlots = 3 #(consistent naming "subframeDuration")
    parametersPhy.slotDuration = 6 *  parametersPhy.symbolDuration
    parametersPhy.adaptUTTxPower = True
    # True (assuming all UTs served in parallel):    power_per_subchannel = max_power / #subchannel * #user_terminals
    # False (assuming UTs use very few subchannels): power_per_subchannel = max_power
    noIPHeader = True #Set to true to set IP header to 0 (ipHeaderSize)
    probeWindowSize = 0.005 # Probe per frame

WNS = openwns.Simulator(simulationModel = openwns.node.NodeSimulationModel())
openwns.setSimulator(WNS)
WNS.maxSimTime = 1.10 # seconds
WNS.masterLogger.backtrace.enabled = False
WNS.masterLogger.enabled = True
WNS.outputStrategy = openwns.simulator.OutputStrategy.DELETE
WNS.statusWriteInterval = 30 # in seconds
WNS.probesWriteInterval = 300 # in seconds


WNS.modules.wimac.parametersPHY = Config.parametersPhy

WNS.modules.rise.debug.antennas = True

bsPlacer = scenarios.placer.HexagonalPlacer(numberOfCircles = 0, interSiteDistance = 100.0, rotate=0.0)
# begin example "wimac.tutorial.experiment2.config.scenario"
uePlacer = scenarios.placer.LinearPlacer(numberOfNodes = 2, positionsList = [100, 3000])
# end example
bsAntenna = scenarios.antenna.IsotropicAntennaCreator([0.0, 0.0, 5.0])
bsCreator = wimac.support.nodecreators.WiMAXBSCreator(stationIDs, Config)
ueCreator = wimac.support.nodecreators.WiMAXUECreator(stationIDs, Config)
channelmodelcreator = wimac.support.helper.TestChannelModelCreator()
scenarios.builders.CreatorPlacerBuilder(bsCreator, bsPlacer, bsAntenna, ueCreator, uePlacer, channelmodelcreator)


wimac.support.helper.setupScheduler(WNS, Config.scheduler)

wimac.support.helper.setupPhy(WNS, Config, "LoS_Test")

if Config.noIPHeader:
    wimac.support.helper.disableIPHeader(WNS)

# DHCP, ARP, DNS for IP
ip.BackboneHelpers.createIPInfrastructure(WNS, "WIMAXRAN")

wimac.support.helper.createULPoissonTraffic(WNS, Config.trafficUL, Config.packetSize)

if Config.trafficDL > 0.0:
    wimac.support.helper.createDLPoissonTraffic(WNS, Config.trafficDL, Config.packetSize)

wimac.support.helper.setL2ProbeWindowSize(WNS, Config.probeWindowSize)

utNodes = WNS.simulationModel.getNodesByProperty("Type", "UE")
bsNodes = WNS.simulationModel.getNodesByProperty("Type", "BS")

loggingStationIDs = []

for node in utNodes + bsNodes:    
    loggingStationIDs.append(node.dll.stationID)

# begin example "wimac.tutorial.experiment2.config.probing"
wimac.evaluation.default.installTutorialEvaluation(WNS, loggingStationIDs, Config.settlingTime, "Moments")

# New Wrowser CouchDB feature available from Ubuntu Linux 10.04 on
#wimac.evaluation.default.installJSONScheduleEvaluation(WNS, loggingStationIDs)

openwns.evaluation.default.installEvaluation(WNS)
# end example
