#! /usr/bin/env python2.4

import re

def getMean(fileName):
    
    mean_reg = re.compile('.*Mean: ([-0-9.e+]*).*')
    try:
        f = file(fileName)
    except:
        return None

    for line in f:
        match = mean_reg.match(line)
        if match is not None:
            x, = match.groups(1)
            return x


def getStdDev(fileName):
    stdDev_reg = re.compile('.*Standard deviation: ([-0-9.e+]*).*')
    try:
        f = file(fileName)
    except:
        return None

    for line in f:
        match = stdDev_reg.match(line)
        if match is not None:
            x, = match.groups(1)
            return x


print "#ID\tAggBitTP\t\ttopOutBitTP\t\ttopInBitTP\t\tCIR\t\tMap CI\t\tMap CI Std.Dev\tcarrier\t\tStdDev_C\tinterference\tStdDev_I\tdeltaPHYMode"
#print "#ID\tCIR\t\tcarrier\t\tStdDev_Carrier\tinterference\tStdDev_I\tdeltaPHYMode"
for i in range(1,20):
    print i, "\t",\
          getMean("output/topAggregatedBitThroughput_MAC.Id"+str(i)+"_SC1_PDF.dat"), "\t\t", \
          getMean("output/topOutgoingBitThroughput_MAC.Id"+str(i)+"_SC1_PDF.dat"),"\t\t", \
          getMean("output/topIncomingBitThroughput_MAC.Id"+str(i)+"_SC1_PDF.dat"),"\t\t",\
          getMean("output/cir_MAC.Id"+str(i)+"_SC1_PDF.dat"),"\t", \
          getMean("output/mapCIR_MAC.Id"+str(i)+"_SC1_PDF.dat"),"\t", \
          getStdDev("output/mapCIR_MAC.Id"+str(i)+"_SC1_PDF.dat"),"\t", \
          getMean("output/carrier_MAC.Id"+str(i)+"_SC1_PDF.dat"),"\t", \
          getStdDev("output/carrier_MAC.Id"+str(i)+"_SC1_PDF.dat"),"\t", \
          getMean("output/interference_MAC.Id"+str(i)+"_SC1_PDF.dat"),"\t", \
          getStdDev("output/interference_MAC.Id"+str(i)+"_SC1_PDF.dat"),"\t", \
          getMean("output/deltaPHYMode_MAC.Id"+str(i)+"_SC1_PDF.dat")
