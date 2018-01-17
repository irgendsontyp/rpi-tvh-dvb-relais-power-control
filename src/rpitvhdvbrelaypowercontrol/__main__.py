from .config import Config
import datetime
from .dvb_device_helper import DVBDeviceHelper
from irgendsontyphelpers.application_exit_helper import ApplicationExitHelper
from .gpio_helper import GPIOHelper
import logging
from logging.handlers import RotatingFileHandler
import signal
from .system_helper import SystemHelper
import time
import traceback
from .tvheadend_helper import TVHeadendHelper


applicationExitHelper = ApplicationExitHelper()


def setupLogger():
	logFormatter = logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S")
	
	logFileHandler = RotatingFileHandler("/var/log/tvh-dvb-relay-power-control/status.log", maxBytes = 5 * 1024 * 1024, backupCount = 1, encoding = "utf-8")
	logFileHandler.setFormatter(logFormatter)
	logFileHandler.setLevel(logging.DEBUG)
	
	logging.getLogger().addHandler(logFileHandler)
	logging.getLogger().setLevel(logging.DEBUG)
	

def sigIntHandler(signalNumber, stackFrame):
	logging.info("Received signal SIGINT. Requesting application exit.")
	applicationExitHelper.requestExit()
	

def sigTermHandler(signalNumber, stackFrame):
	logging.info("Received signal SIGTERM. Requesting application exit.")
	applicationExitHelper.requestExit()


def main():		
	conf = Config("/etc/tvh-dvb-relay-power-control/config.conf")
	

	# Setup logging
	setupLogger()
	
	logging.info("*** Application has started, logging has been set up ***")
	
	
	# Setup program exit signal handlers
	signal.signal(signal.SIGINT, sigIntHandler)
	signal.signal(signal.SIGTERM, sigTermHandler)
	
	systemHelper = SystemHelper()
	
	with GPIOHelper(conf) as gpioHelper, DVBDeviceHelper(gpioHelper, systemHelper) as dvbDeviceHelper, TVHeadendHelper(conf, dvbDeviceHelper, applicationExitHelper) as tvHeadendHelper:
		while (not applicationExitHelper.isExitRequested()):
			try:
				# Trigger OTA EPG grabber if required
				tvHeadendHelper.triggerOtaEpgGrabberIfRequired()
				
				# Check whether there are upcoming or running recordings
				tvHeadendHelper.switchDvbDevicePowerDependentOnUpcomingRecordings()
							
				logging.info("Check done. Waiting " + str(conf.MainCheckIntervalSeconds) + " seconds until the next check.")
							
				applicationExitHelper.sleepWhileNotExitRequested(conf.MainCheckIntervalSeconds)
					
			except:
				logging.error("An unrecoverable error occured: " + traceback.format_exc())
				gpioHelper.switchOnErrorLED()
				
				# Wait for the user to stop the application so he can see the red LED and react accordingly
				applicationExitHelper.waitForExitRequest()
		
# run
if (__name__ == "__main__"):
	main()
