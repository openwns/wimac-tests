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

# begin example "wimac.tutorial.experiment1.campaignConfiguration.import"
from openwns.wrowser.simdb.Parameters import Parameters, Bool, Int, Float, String
# end example

# begin example "wimac.tutorial.experiment1.campaignConfiguration.Set"
class Set(Parameters):
    offeredTraffic = Float()
    bandwidth = Int()
    distance = Float()
    def setDefault(self):
        self.offeredTraffic = 10.01e6
        self.bandwidth = 5
        self.distance = 100
# end example

# begin example "wimac.tutorial.experiment1.campaignConfiguration.params"
params = Set()
params.setDefault()
# end example

# begin example "wimac.tutorial.experiment1.campaignConfiguration.offeredTraffic"
for rate in xrange(0,6):
    params.offeredTraffic = (0.01 + 2.5 * rate) * 1e6
    params.write()
# end example

# begin example "wimac.tutorial.experiment1.campaignConfiguration.bandwidth"
for rate in [0,10,15,30,35]:
    for params.bandwidth in [5,10,20]:
        params.offeredTraffic = (0.001 + rate) * 1e6
        params.write()
# end example

# begin example "wimac.tutorial.experiment1.campaignConfiguration.distance"
#for dist in xrange(1,7):
#    params.distance = dist * 2000
#    params.write()
# end example
