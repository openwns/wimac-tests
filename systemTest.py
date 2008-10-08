#! /usr/bin/env python2.4

# this is needed, so that the script can be called from everywhere
import os
import sys
base, tail = os.path.split(sys.argv[0])
os.chdir(base)

# Append the python sub-dir of WNS--main--x.y ...
sys.path.append(os.path.join('..', '..', '..', 'sandbox', 'default', 'lib', 'python2.4', 'site-packages'))

# ... because the module WNS unit test framework is located there.
import pywns.WNSUnit


wimacTestSuite = pywns.WNSUnit.TestSuite()

#### create the system Tests

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- Base Test~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           executeable = "wns-core",
                                           configFile = 'config.py',
                                           shortDescription = 'WiMAC: simple one on one',
                                           requireReferenceOutput = True,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configBase')

checkULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeUT_PDF.dat',
                                              ['probe.trials == 10', 'probe.mean == 9480000.0'],
                                              'dbg')


testSuite.addTest(checkULThroughput)

checkDLThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeBS_PDF.dat',
                                              ['probe.trials == 10', 'probe.mean == 4202800.0'],
                                              'dbg')

testSuite.addTest(checkDLThroughput)

wimacTestSuite.addTest(testSuite)

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- SDMA Test~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           executeable = "wns-core",
                                            configFile = 'config.py',
                                            shortDescription = 'WiMAC: Test with SDMA Scheduler',
                                            requireReferenceOutput = False,
                                            disabled = False,
                                            disabledReason = "",
                                            workingDir = 'configSDMA')

checkULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeUT_PDF.dat',
                                              ['probe.trials == 98', 'probe.mean == 10166857.1428571'],
                                              'dbg')


testSuite.addTest(checkULThroughput)

checkDLThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeBS_PDF.dat',
                                              ['probe.trials == 49', 'probe.mean == 18209567.3469388'],
                                              'dbg')

testSuite.addTest(checkDLThroughput)

wimacTestSuite.addTest(testSuite)


##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- Subframe Test ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           executeable = "wns-core",
                                           configFile = 'config.py',
                                           shortDescription = 'WiMAC: Relay enhanced cell',
                                           requireReferenceOutput = False,
                                           disabled = True,
                                           disabledReason = "pending reconfiguration of the compound switch",
                                           workingDir = 'configSubframe')

checkDLThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.Ring1_PDF.dat',
                                              ['probe.trials == 9', 'probe.mean == 10533333.0'],
                                              'dbg')
testSuite.addTest(checkDLThroughput)


checkRing2ULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.Ring2_PDF.dat',
                                              ['probe.trials == 18', 'probe.mean == 5266666.7'],
                                              'dbg')
testSuite.addTest(checkRing2ULThroughput)

checkRing3ULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.Ring3_PDF.dat',
                                              ['probe.mean == 0.0'],
                                              'dbg')
testSuite.addTest(checkRing3ULThroughput)

checkRing4ULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.Ring4_PDF.dat',
                                              ['probe.mean > 9.1e+05'],
                                              'dbg')
testSuite.addTest(checkRing3ULThroughput)

wimacTestSuite.addTest(testSuite)

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- Subframe TDD Test ~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           executeable = "wns-core",
                                           configFile = 'config.py',
                                           shortDescription = 'WiMAC: Relay enhanced cell',
                                           requireReferenceOutput = False,
                                           disabled = True,
                                           disabledReason = "Pending migration to openwns.evaluation",
                                           workingDir = 'configSubframeTDD')
# create a system test
wimacTestSuite.addTest(testSuite)


if __name__ == '__main__':
    # This is only evaluated if the script is called by hand

    # if you need to change the verbosity do it here
    verbosity = 2

    pywns.WNSUnit.verbosity = verbosity

    # Create test runner
    testRunner = pywns.WNSUnit.TextTestRunner()

    # Finally, run the tests.
    for it in wimacTestSuite:
       testRunner.run(it)
