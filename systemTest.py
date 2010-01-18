#! /usr/bin/env python

# this is needed, so that the script can be called from everywhere
import os
import sys
base, tail = os.path.split(sys.argv[0])
os.chdir(base)

# Append the python sub-dir of WNS--main--x.y ...
sys.path.append(os.path.join('..', '..', '..', 'sandbox', 'default', 'lib', 'python2.4', 'site-packages'))

# ... because the module WNS unit test framework is located there.
import pywns.WNSUnit


testSuite = pywns.WNSUnit.TestSuite()

#### create the system Tests

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- Base Test~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite0 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'config.py',
                                           shortDescription = 'Two stations. One neer one far. RoundRobin',
                                           requireReferenceOutput = True,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configBase')

#checkULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeUT_PDF.dat',
#                                              ['probe.trials == 10', 'probe.mean == 8964000.0'],
#                                              'dbg')


#testSuite1.addTest(checkULThroughput)

#checkDLThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeBS_PDF.dat',
#                                              ['probe.trials == 10', 'probe.mean == 4448800.0'],
#                                              'dbg')

#testSuite1.addTest(checkDLThroughput)

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- Base Test~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite1 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'configPF.py',
                                           shortDescription = 'Two stations. One neer one far. ProportionalFair',
                                           requireReferenceOutput = True,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configBase')

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- TDMA Test~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite2 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'config.py',
                                           shortDescription = 'Two stations. One neer one far',
                                           requireReferenceOutput = False,
                                           disabled = True,
                                           disabledReason = "Needs work",
                                           workingDir = 'configTDMA')

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- SDMA Test~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite3 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                            configFile = 'config.py',
                                            shortDescription = 'Test with SDMA Scheduler',
                                            requireReferenceOutput = False,
                                            disabled = True,
                                            disabledReason = "New schedulers do not support SDMA",
                                            workingDir = 'configSDMA')

#checkULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeUT_PDF.dat',
#                                              ['probe.trials == 98', 'probe.mean == 10166857.1428571'],
#                                              'dbg')


#testSuite.addTest(checkULThroughput)

#checkDLThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeBS_PDF.dat',
#                                              ['probe.trials == 49', 'probe.mean == 18209567.3469388'],
#                                              'dbg')

#testSuite.addTest(checkDLThroughput)




##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- Subframe TDD Test ~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite4 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'config.py',
                                           shortDescription = 'Relay enhanced cell',
                                           requireReferenceOutput = False,
                                           disabled = True,
                                           disabledReason = "Needs work and verification",
                                           workingDir = 'configSubframeTDD')


##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- OFDMA Test ~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite5 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'config.py',
                                           shortDescription = 'Using multiple subchannels',
                                           requireReferenceOutput = False,
                                           disabled = True,
                                           disabledReason = "OFDMA needs to be enabled",
                                           workingDir = 'configOFDMA')



testSuite6 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'config.py',
                                           shortDescription = 'Same as basic test but with bypass queue',
                                           requireReferenceOutput = True,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configBypass')

testSuite.addTest(testSuite0)
testSuite.addTest(testSuite1)
testSuite.addTest(testSuite2)
testSuite.addTest(testSuite3)
testSuite.addTest(testSuite4)
testSuite.addTest(testSuite5)
testSuite.addTest(testSuite6)


if __name__ == '__main__':
    # This is only evaluated if the script is called by hand

    # if you need to change the verbosity do it here
    verbosity = 2

    pywns.WNSUnit.verbosity = verbosity

    # Create test runner
    testRunner = pywns.WNSUnit.TextTestRunner()

    # Finally, run the tests.
    testRunner.run(testSuite)
