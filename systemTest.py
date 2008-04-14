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
                                           requireReferenceOutput = False,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configBase')

checkULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeUT_SC1_PDF.dat',
                                              ['probe.trials == 10', 'probe.mean == 9480000.0'],
                                              'dbg')


testSuite.addTest(checkULThroughput)

checkDLThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeBS_SC1_PDF.dat',
                                              ['probe.trials == 10', 'probe.mean == 4234400.0'],
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

checkULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeUT_SC1_PDF.dat',
                                              ['probe.trials == 98', 'probe.mean == 10162318.0'],
                                              'dbg')


testSuite.addTest(checkULThroughput)

checkDLThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.StationTypeBS_SC1_PDF.dat',
                                              ['probe.trials == 49', 'probe.mean == 18200490.0'],
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
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configSubframe')

checkDLThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.Ring1_SC2_PDF.dat',
                                              ['probe.trials == 9', 'probe.mean == 10533333.0'],
                                              'dbg')
testSuite.addTest(checkDLThroughput)


checkRing2ULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.Ring2_SC2_PDF.dat',
                                              ['probe.trials == 18', 'probe.mean == 5266666.7'],
                                              'dbg')
testSuite.addTest(checkRing2ULThroughput)

checkRing3ULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.Ring3_SC2_PDF.dat',
                                              ['probe.mean == 0.0'],
                                              'dbg')
testSuite.addTest(checkRing3ULThroughput)

checkRing4ULThroughput = pywns.WNSUnit.Expectation('wimac.top.window.aggregated.bitThroughput_MAC.Ring4_SC2_PDF.dat',
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
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configSubframeTDD')
# create a system test
wimacTestSuite.addTest(testSuite)


if __name__ == '__main__':
    # This is only evaluated if the script is called by hand

    # if you need to change the verbosity do it here
    verbosity = 2

    pywns.WNSUnit.verbosity = verbosity

    # Create test runner
    testRunner = pywns.WNSUnit.TextTestRunner()#verbosity=verbosity)

    # Finally, run the tests.
    for it in wimacTestSuite:
       testRunner.run(it)
