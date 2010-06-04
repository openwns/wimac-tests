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
testSuite1 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'config.py',
                                           shortDescription = 'Two stations. One neer one far. RoundRobin',
                                           requireReferenceOutput = True,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configBase')

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- Base Test~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite2 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'configPF.py',
                                           shortDescription = 'Two stations. One neer one far. ProportionalFair',
                                           requireReferenceOutput = True,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configBase')

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- OFDMA Test ~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite3 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'config.py',
                                           shortDescription = 'Using multiple subchannels',
                                           requireReferenceOutput = False,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configOFDMA')
##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- SDMA Test ~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite10 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           configFile = 'configSDMA.py',
                                           shortDescription = 'Using SDMA',
                                           requireReferenceOutput = False,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configBeamforming')

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- BypassQueue Test ~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite4 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'config.py',
                                           shortDescription = 'Same as basic test but with bypass queue',
                                           requireReferenceOutput = True,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configBypass')

##################################################################################
#~~~~~~~~~~~~~~~~~~~~~~  TEST-SUITE -- IMT-Advanced Tests ~~~~~~~~~~~~~~~~~~~~~~~~~
testSuite5 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'configUMa.py',
                                           shortDescription = "IMT-A Urban Macro Scenario with 5MHz BW in 3 sectors.",
                                           requireReferenceOutput = False,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configIMTA')

testSuite6 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'configUMi.py',
                                           shortDescription = "IMT-A Urban Micro Scenario with 5MHz BW in 3 sectors.",
                                           requireReferenceOutput = False,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configIMTA')

testSuite7 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'configRMa.py',
                                           shortDescription = "IMT-A Rural Micro Scenario with 5MHz BW in 3 sectors.",
                                           requireReferenceOutput = False,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configIMTA')

testSuite8 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'configSMa.py',
                                           shortDescription = "IMT-A Suburban Macro Scenario with 5MHz BW in 3 sectors.",
                                           requireReferenceOutput = False,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configIMTA')

testSuite9 = pywns.WNSUnit.ProbesTestSuite( sandboxPath = os.path.join('..', '..', '..', 'sandbox'),
                                           
                                           configFile = 'configInH.py',
                                           shortDescription = "IMT-A Indoor Hotspot Scenario with 5MHz BW in 3 sectors.",
                                           requireReferenceOutput = False,
                                           disabled = False,
                                           disabledReason = "",
                                           workingDir = 'configIMTA')


testSuite.addTest(testSuite1)
testSuite.addTest(testSuite2)
testSuite.addTest(testSuite3)
testSuite.addTest(testSuite4)
testSuite.addTest(testSuite5)
testSuite.addTest(testSuite6)
testSuite.addTest(testSuite7)
testSuite.addTest(testSuite8)
testSuite.addTest(testSuite9)
testSuite.addTest(testSuite10)

if __name__ == '__main__':
    # This is only evaluated if the script is called by hand

    # if you need to change the verbosity do it here
    verbosity = 2

    pywns.WNSUnit.verbosity = verbosity

    # Create test runner
    testRunner = pywns.WNSUnit.TextTestRunner()

    # Finally, run the tests.
    testRunner.run(testSuite)
