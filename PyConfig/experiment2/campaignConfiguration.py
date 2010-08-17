#! /usr/bin/python
###############################################################################
# This file is part of openWNS (open Wireless Network Simulator)
# _____________________________________________________________________________
#
# Copyright (C) 2004-2007
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

import sys
import os

from openwns.wrowser.simdb.Parameters import Parameters, Bool, Int, Float, String


class Set(Parameters):
    offeredTraffic = Float()
    scheduler = String()
    #def setDefault(self):
    #    self.offeredTraffic = 10.01e6



params = Set()
#params.setDefault()

#for params.subStrategy in ["ProportionalFair", "ExhaustiveRoundRobin", "DSADrivenRR", "RoundRobin"]:
#for params.dsa in ["Fixed", "Random", "LinearFFirst"]:

# begin example "wimac.tutorial.experiment2.campaignConfiguration.offeredTraffic"
for params.scheduler in ["RoundRobin", "PropFair", "ExhaustiveRR", "Fixed"]:
    for rate in xrange(0,9)
        params.offeredTraffic = (0.1 + rate * 1.25) * 1e6
        params.write()
# end example