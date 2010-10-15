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

# begin example "wimac.tutorial.experiment1.campaignConfiguration.imports"
from openwns.wrowser.simdb.Parameters import Parameters, Bool, Int, Float, String
# end example

# begin example "wimac.tutorial.experiment1.campaignConfiguration.Set"
class Set(Parameters):
    offeredTraffic = Float()
# end example

# begin example "wimac.tutorial.experiment1.campaignConfiguration.params"
params = Set()
# end example

# begin example "wimac.tutorial.experiment1.campaignConfiguration.offeredTraffic"
for rate in xrange(0,5):
    params.offeredTraffic = 2.5 * rate * 1e6
    params.write()
# end example





