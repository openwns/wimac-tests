from Layer2 import *
import dll.UpperConvergence
import wimac.Scheduler
import wimac.FUReseter
import wimac.Relay
import wns.Tools
from wimac.FrameBuilder import ActivationAction, OperationMode
import support.FrameSetup as FrameSetup

class Association:
    def __init__(self,source, destination, id):
        self.source = source
        self.destination = destination
        self.id = id



class BaseStation(Layer2):

    subscriberStations = None
    relayStations = None
    config = None
    
    def __init__(self, node, config):
        super(BaseStation, self).__init__(node, "BS", config)
        self.ring = 1
        self.qosCategory = 'NoQoS'
        self.config = config
        
        # BaseStation specific components
        self.upperconvergence = dll.UpperConvergence.AP()
        self.stationType = "AP"
        self.relayMapper = wimac.Relay.BSRelayMapper()
        self.framehead = wimac.FrameBuilder.FrameHeadCollector('frameBuilder')

        # frame elements
        self.framehead = wimac.FrameBuilder.FrameHeadCollector('frameBuilder')
        self.dlmapcollector = wimac.FrameBuilder.DLMapCollector('frameBuilder', 'dlscheduler')
        self.ulmapcollector = wimac.FrameBuilder.ULMapCollector('frameBuilder', 'ulscheduler')
        self.dlscheduler = wimac.FrameBuilder.DataCollector('frameBuilder')
        self.dlscheduler.txScheduler = wimac.Scheduler.Scheduler(
            "frameBuilder",
            config.parametersPhy.symbolDuration,
            strategy = wns.Scheduler.ProportionalFair(historyWeight = 1.0,
                                                      maxBursts = config.maxBursts),
            freqChannels = config.parametersPhy.subchannels,
            maxBeams = config.maxBeams,
            beamforming = config.beamforming,
            friendliness_dBm = config.friendliness_dBm,
            plotFrames = False,
            resetedBitsProbeName = "wimac.schedulerQueue.reseted.bits",
            resetedCompoundsProbeName = "wimac.schedulerQueue.reseted.compounds",
            callback = wimac.Scheduler.DLCallback( beamforming = config.beamforming )
            )

        self.ulscheduler = wimac.FrameBuilder.DataCollector('frameBuilder')
        self.ulscheduler.rxScheduler = wimac.Scheduler.Scheduler(
            "frameBuilder",
            config.parametersPhy.symbolDuration,
            strategy = wns.Scheduler.ProportionalFairUL(historyWeight = 1.0,
                                                        maxBursts = config.maxBursts),
            freqChannels = config.parametersPhy.subchannels,
            maxBeams = config.maxBeams,
            beamforming =  config.beamforming,
            friendliness_dBm = config.friendliness_dBm,
            callback = wimac.Scheduler.ULCallback(),
            plotFrames = False,
            uplink = True
            )
        self.ulscheduler.rxScheduler.pseudoGenerator = \
            wimac.Scheduler.PseudoBWRequestGenerator('connectionManager',
                                                     'ulscheduler',
                                                     _packetSize = config.packetSize,
                                                     _pduOverhead = config.parametersMAC.pduOverhead)

        self.setupCompoundSwitch()
        self.setupFrame(config)
        self.fun = FUN()
        self.buildFUN(config)
	self.connect()


    def connect(self):
        # Connections Dataplane
        self.upperconvergence.connect(self.topTpProbe)
        self.topTpProbe.connect(self.topPProbe)

        self.topPProbe.connect(self.classifier)
        self.classifier.connect(self.synchronizer)
        self.synchronizer.connect(self.bufferSep)
        self.bufferSep.connect(self.relayMapper)
        self.relayMapper.connect(self.crc)
        self.crc.connect(self.errormodelling)
        self.errormodelling.connect(self.compoundSwitch)
	self.compoundSwitch.connect(self.dlscheduler)
        self.compoundSwitch.upConnect(self.ulscheduler)

        self.framehead.connect(self.frameBuilder)
        self.dlmapcollector.connect(self.frameBuilder)
        self.ulmapcollector.connect(self.frameBuilder)
        self.dlscheduler.connect(self.frameBuilder)
        self.ulscheduler.connect(self.frameBuilder)
        self.frameBuilder.connect(self.phyUser)
          
    def setupCompoundSwitch(self):
        self.compoundSwitch.onDataFilters.append( wimac.CompoundSwitch.FilterAll('All') )
        self.compoundSwitch.sendDataFilters.append( wimac.CompoundSwitch.FilterAll('All') )
        self.compoundSwitch.sendDataFilters.append( wimac.CompoundSwitch.FilterNone('None') )


    def setupFrame(self, config):

        myFrameSetup = FrameSetup.FrameSetup(config)

        # Insert Activations into Timing Control
        # first, configure only real compound collectors
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.frameHeadLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.dlMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.ulMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.dlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.ulDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.dlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.ulDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        # second, now set phase durations
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.frameHeadLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.dlMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.ulMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.dlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        # name of compound collector (here "ttg") is just informative
        activation = wimac.FrameBuilder.Activation('ttg',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.ttgLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.ulDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        # this could be a pause, too
        # but it might be exchanged by real compound collector in the future

        activation = wimac.FrameBuilder.Activation('bwReq',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.bwReqLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ranging',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.rangingLength )
        self.frameBuilder.timingControl.addActivation( activation )

    def getFrameStartupDelay(self):
        return 0.0

    def getFrameActivationsForAssociatedStations(self):

        myFrameSetup = FrameSetup.FrameSetup(self.config)

        activations = []

        # first, configure only real compound collectors
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.frameHeadLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.dlMapLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.ulMapLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.dlDataLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.ulDataLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.dlDataLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.ulDataLength )
        activations.append( activation )


        # second, now set phase durations
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.frameHeadLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.dlMapLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.ulMapLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.dlDataLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ttg',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.ttgLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.ulDataLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('bwReq',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.bwReqLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ranging',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.rangingLength )
        activations.append( activation )

        return activations


class RelayStation(Layer2):

    subscriberStations = None
    relayStations = None
    injectMultiplexer = None
    config = None
    mainFrameLength = None
    subframeOffset = None
    
    def __init__(self, node, config, stationID):
        super(RelayStation, self).__init__(node, "RS", config)
        self.upperconvergence = dll.UpperConvergence.No()
        self.stationType = "FRS"
        self.config = config
        
        self.setStationID(stationID)
        self.relayMapper = wimac.Relay.RSRelayMapper()
        self.framehead = wimac.FrameBuilder.FrameHeadCollector('frameBuilder')

        # frame elements
        self.dlmapcollector = wimac.FrameBuilder.DLMapCollector( 'frameBuilder', 'dlscheduler')
        self.ulmapcollector = wimac.FrameBuilder.ULMapCollector( 'frameBuilder', 'ulscheduler')
        self.dlscheduler = wimac.FrameBuilder.DataCollector('frameBuilder')
        self.dlscheduler.txScheduler = wimac.Scheduler.Scheduler(
            'frameBuilder',
            config.parametersPhy.symbolDuration,
            strategy = wns.Scheduler.ProportionalFair(historyWeight = 1.0,
                                                      maxBursts = config.maxBursts),
            freqChannels =  config.parametersPhy.subchannels,
            maxBeams = config.maxBeams,
            beamforming = config.beamforming,
            friendliness_dBm = config.friendliness_dBm,
            plotFrames = False,
            resetedBitsProbeName = "wimac.schedulerQueue.reseted.bits",
            resetedCompoundsProbeName = "wimac.schedulerQueue.reseted.compounds",
            callback = wimac.Scheduler.DLCallback( beamforming = config.beamforming )
            )
        self.dlscheduler.rxScheduler = wimac.FrameBuilder.SSDLScheduler('frameBuilder', 'dlmapcollector')
        
        self.ulscheduler = wimac.FrameBuilder.DataCollector('frameBuilder')
        self.ulscheduler.rxScheduler = wimac.Scheduler.Scheduler(
            'frameBuilder',
            config.parametersPhy.symbolDuration,
            strategy = wns.Scheduler.ProportionalFairUL(historyWeight = 1.0,
                                                        maxBursts = config.maxBursts),
            freqChannels =  config.parametersPhy.subchannels,
            maxBeams = config.maxBeams,
            beamforming = config.beamforming,
            friendliness_dBm = config.friendliness_dBm,
            callback = wimac.Scheduler.ULCallback(),
            plotFrames = False,
            uplink = True
            )
        self.ulscheduler.rxScheduler.pseudoGenerator = \
            wimac.Scheduler.PseudoBWRequestGenerator('connectionManager',
                                                     'ulscheduler',
                                                     _packetSize = config.packetSize,
                                                     _pduOverhead = config.parametersMAC.pduOverhead)

        self.ulscheduler.txScheduler = wimac.FrameBuilder.SSULScheduler('frameBuilder', 'ulmapcollector')

        self.injectMultiplexer = wns.Multiplexer.Dispatcher(0)


        self.setupCompoundSwitch()
        self.setupFrame(config)
        #print self.name + " has " + str(len(self.frameBuilder.timingControl.activations)) + " activations registered after setupFrame()"
        self.fun = FUN()
        self.buildFUN(config)
        self.injectMultiplexer = Node('injectMultiplexer', self.injectMultiplexer)
        self.fun.add(self.injectMultiplexer)
	self.connect()


    def associate(self, destination):
        assert isinstance(destination, Layer2)
        it = Association(self, destination, destination.getAssociationID())
        self.associations.append(it)
        self.associateTo = destination.stationID
        self.qosCategory = 'BE'
        self.ring = destination.ring + 2
        self.connectionControl.associateTo(destination.stationID)
        self.phyUser.config.bandwidth = destination.phyUser.config.bandwidth
        self.phyUser.config.centerFrequency = destination.phyUser.config.centerFrequency
        self.phyUser.config.numberOfSubCarrier = destination.phyUser.config.numberOfSubCarrier

        self.frameBuilder.config.timingControl.activations = \
            destination.getFrameActivationsForAssociatedStations() + self.frameBuilder.config.timingControl.activations
        
    def connect(self):
        # Connections Controlplane

        # Connections Dataplane
        self.uprelayinject.downConnect(self.injectMultiplexer)
        self.downrelayinjectSep.downConnect(self.injectMultiplexer)
        self.injectMultiplexer.downConnect(self.relayMapper)
        self.relayMapper.connect(self.crc)
        self.crc.connect(self.errormodelling)
	self.errormodelling.connect(self.compoundSwitch)
        self.compoundSwitch.connect(self.dlscheduler)
        self.compoundSwitch.connect(self.ulscheduler)

        self.framehead.connect(self.frameBuilder)
        self.dlmapcollector.connect(self.frameBuilder)
        self.ulmapcollector.connect(self.frameBuilder)
        self.dlscheduler.connect(self.frameBuilder)
        self.ulscheduler.connect(self.frameBuilder)
        self.frameBuilder.connect(self.phyUser)

    def setupCompoundSwitch(self):
	self.compoundSwitch.onDataFilters.append( wimac.CompoundSwitch.FilterAll('All') )
        self.compoundSwitch.sendDataFilters.append( wimac.CompoundSwitch.RelayDirection('Down', wimac.Relay.Direction.Down) )
        self.compoundSwitch.sendDataFilters.append( wimac.CompoundSwitch.RelayDirection('Up', wimac.Relay.Direction.Up) )

    def setupFrame(self, config):


        myFrameSetup = FrameSetup.FrameSetup(config)
        if(config.operationModeRelays == 'SDM'):
            myFrameSetup.subPrePause  = 0
            myFrameSetup.subPostPause = 0
        elif(config.operationModeRelays == 'TDM'):
            myFrameSetup.subPrePause  = ((self.stationID - config.nBSs - 1.0) % config.nRSs) * myFrameSetup.subframe / config.nRSs
            myFrameSetup.subPostPause = (config.nRSs - 1.0 - ((self.stationID - config.nBSs - 1) % config.nRSs)) * myFrameSetup.subframe / config.nRSs
        else:
            print error

        myFrameSetup.subPrePauseLength  = myFrameSetup.subPrePause  * config.parametersPhy.symbolDuration
        myFrameSetup.subPostPauseLength = myFrameSetup.subPostPause * config.parametersPhy.symbolDuration

        self.subframeOffset = myFrameSetup.subPrePauseLength

        #print 'pre-/PostP subPreP subPostP subPrePLength subPostPLength subframeOffset subframe',((self.stationID - config.nBSs - 1.0) % config.nRSs),  (config.nRSs - 1.0 - ((self.stationID - config.nBSs - 1) % config.nRSs)), myFrameSetup.subPrePause, myFrameSetup.subPostPause,  myFrameSetup.subPrePauseLength, myFrameSetup.subPostPauseLength, self.subframeOffset, myFrameSetup.subframe
        print myFrameSetup.printFramePhases()
        ## Only Sub Frame needed here ##

        # Insert Activations into Timing Control
        # first, configure only real compound collectors
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.subFrameHeadLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.subDlMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.subDlMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.subDlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.subUlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.subDlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.subUlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )


        # second, now set phase durations
        activation = wimac.FrameBuilder.Activation('PrePause',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.subPrePauseLength )
        self.frameBuilder.timingControl.addActivation( activation )
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.subFrameHeadLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.subDlMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.subUlMapLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.subDlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        # name of compound collector (here "ttg") is just informative
        activation = wimac.FrameBuilder.Activation('ttg',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.ttgLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.subUlDataLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('bwReq',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.subBwReqLength )
        self.frameBuilder.timingControl.addActivation( activation )

        activation = wimac.FrameBuilder.Activation('ranging',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.subRangingLength )
        self.frameBuilder.timingControl.addActivation( activation )
        activation = wimac.FrameBuilder.Activation('PostPause',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.subPostPauseLength )
        self.frameBuilder.timingControl.addActivation( activation )

        self.mainFrameLength = myFrameSetup.frameHeadLength +\
                               myFrameSetup.dlMapLength +\
                               myFrameSetup.ulMapLength +\
                               myFrameSetup.dlDataLength +\
                               myFrameSetup.ttgLength +\
                               myFrameSetup.ulDataLength +\
                               myFrameSetup.bwReqLength +\
                               myFrameSetup.rangingLength

    def getFrameStartupDelay(self):
        #missleading name
        return self.mainFrameLength + self.subframeOffset

    def getFrameActivationsForAssociatedStations(self):

        myFrameSetup = FrameSetup.FrameSetup(self.config)

        activations = []

        # first, configure only real compound collectors
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.subFrameHeadLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.subDlMapLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.subUlMapLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.subDlDataLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.StartCollection ),
                                                   myFrameSetup.subUlDataLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.subDlDataLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.FinishCollection ),
                                                   myFrameSetup.subUlDataLength )
        activations.append( activation )


        # second, now set phase durations
        activation = wimac.FrameBuilder.Activation('framehead',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.subFrameHeadLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('dlmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.subDlMapLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ulmapcollector',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.subUlMapLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('dlscheduler',
                                                   OperationMode( OperationMode.Receiving ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.subDlDataLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ttg',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.ttgLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ulscheduler',
                                                   OperationMode( OperationMode.Sending ),
                                                   ActivationAction( ActivationAction.Start ),
                                                   myFrameSetup.subUlDataLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('bwReq',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.subBwReqLength )
        activations.append( activation )

        activation = wimac.FrameBuilder.Activation('ranging',
                                                   OperationMode( OperationMode.Pausing ),
                                                   ActivationAction( ActivationAction.Pause ),
                                                   myFrameSetup.subRangingLength )
        activations.append( activation )

        return activations


class SubscriberStation(Layer2):
    forwarder = None

    def __init__(self, node, config):
        super(SubscriberStation, self).__init__(node, "SS", config)
        # actually this can be 2 + 2*numberOfRingAssociated to (1. BS, 2. Relay, ...)
        self.upperconvergence = dll.UpperConvergence.UT()
        self.stationType = "UT"
        self.relayMapper = wimac.Relay.SSRelayMapper()
        self.framehead = wimac.FrameBuilder.FrameHeadCollector('frameBuilder')
        

        # frame elements
        self.dlmapcollector = wimac.FrameBuilder.DLMapCollector('frameBuilder', None)
        self.ulmapcollector = wimac.FrameBuilder.ULMapCollector('frameBuilder', None)
        self.dlscheduler = wimac.FrameBuilder.DataCollector('frameBuilder')
        self.dlscheduler.rxScheduler = wimac.FrameBuilder.SSDLScheduler('frameBuilder', 'dlmapcollector')
        self.ulscheduler = wimac.FrameBuilder.DataCollector('frameBuilder')
        self.ulscheduler.txScheduler = wimac.FrameBuilder.SSULScheduler('frameBuilder', 'ulmapcollector')


        self.setupCompoundSwitch()
        #self.setupFrame(config)
        self.fun = FUN()
        self.buildFUN(config)
	self.connect()


    def associate(self, destination):
        assert isinstance(destination, Layer2)
        it = Association(self, destination, destination.getAssociationID())
        self.associations.append(it)
        self.associateTo = destination.stationID
        self.qosCategory = 'BE'
        self.ring = destination.ring + 1
        self.connectionControl.associateTo(destination.stationID)
        self.phyUser.config.bandwidth = destination.phyUser.config.bandwidth
        self.phyUser.config.centerFrequency = destination.phyUser.config.centerFrequency
        self.phyUser.config.numberOfSubCarrier = destination.phyUser.config.numberOfSubCarrier
        self.frameBuilder.config.timingControl.frameStartupDelay = destination.getFrameStartupDelay()
        self.frameBuilder.config.timingControl.activations = \
            destination.getFrameActivationsForAssociatedStations()


    def connect(self):

        # Connections Dataplane
        self.upperconvergence.connect(self.topTpProbe)
        self.topTpProbe.connect(self.topPProbe)
        self.topPProbe.connect(self.classifier)
        self.classifier.connect(self.synchronizer)
        self.synchronizer.connect(self.bufferSep)
        self.bufferSep.connect(self.relayMapper)
        self.relayMapper.connect(self.crc)
        self.crc.connect(self.errormodelling)
        self.errormodelling.connect(self.compoundSwitch)
        self.compoundSwitch.upConnect(self.dlscheduler)
        self.compoundSwitch.connect(self.ulscheduler)

        self.framehead.connect(self.frameBuilder)
        self.dlmapcollector.connect(self.frameBuilder)
        self.ulmapcollector.connect(self.frameBuilder)
        self.dlscheduler.connect(self.frameBuilder)
        self.ulscheduler.connect(self.frameBuilder)
        self.frameBuilder.connect(self.phyUser)

    def setupCompoundSwitch(self):
	self.compoundSwitch.onDataFilters.append( wimac.CompoundSwitch.FilterAll('All') )
	self.compoundSwitch.sendDataFilters.append( wimac.CompoundSwitch.FilterAll('All') )


        
