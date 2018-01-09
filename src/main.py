from config import Config
import datetime
from dvb_device_helper import DVBDeviceHelper
from exit_helper import ExitHelper
from gpio_helper import GPIOHelper
import logging
import signal
from system_helper import SystemHelper
import time
import traceback
from tvheadend_helper import TVHeadendHelper


exitHelper = ExitHelper()


def setupLogger():
	logging.basicConfig(filename = "/var/log/tvh-dvb-relay-power-control/status.log", level = logging.DEBUG, format = "[%(asctime)s] %(message)s", datefmt = "%Y-%m-%d %H:%M:%S")	
	

def sigIntHandler(signalNumber, stackFrame):
	logging.info("Received signal SIGINT. Requesting application exit.")
	exitHelper.requestExit()
	

def sigTermHandler(signalNumber, stackFrame):
	logging.info("Received signal SIGTERM. Requesting application exit.")
	exitHelper.requestExit()


def main():		
	conf = Config("/etc/tvh-dvb-relay-power-control/config.conf")
	

	# Setup logging
	setupLogger()
	
	logging.info("*** Application has started, logging has been set up ***")
	
	
	# Setup program exit signal handlers
	signal.signal(signal.SIGINT, sigIntHandler)
	signal.signal(signal.SIGTERM, sigTermHandler)
	
	systemHelper = SystemHelper()
	
	with GPIOHelper(conf) as gpioHelper, DVBDeviceHelper(gpioHelper, systemHelper) as dvbDeviceHelper:
		tvHeadendHelper = TVHeadendHelper(conf, dvbDeviceHelper, exitHelper)

		while (not exitHelper.isExitRequested()):
			try:
				# Trigger OTA EPG grabber if required
				tvHeadendHelper.triggerOtaEpgGrabberIfRequired()
				
				# Check whether there are upcoming or running recordings
				tvHeadendHelper.switchDvbDevicePowerDependentOnUpcomingRecordings()
			
				loopTimeoutInMilliseconds = conf.MainCheckIntervalSeconds * 1000
					
				# Sleep for the configured amount of milliseconds in intervals of 10ms
				for i in range(1, loopTimeoutInMilliseconds // 10):
					if (exitHelper.isExitRequested()):
						break
						
					time.sleep(0.01)
					
			except:
				logging.error("An unrecoverable error occured: " + traceback.format_exc())
				gpioHelper.switchOnErrorLED()
				
				# Wait for the user to stop the application so he can see the red LED and react accordingly
				exitHelper.waitForExitRequest()
		
# run
main()
