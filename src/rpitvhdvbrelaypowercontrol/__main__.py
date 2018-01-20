import argparse
from .config import Config
import datetime
from .dvb_device_helper import DVBDeviceHelper
from irgendsontyphelpers.application_exit_helper import ApplicationExitHelper
from .gpio_helper import GPIOHelper
import logging
from logging.handlers import RotatingFileHandler
import os
import signal
from .system_helper import SystemHelper
import time
import traceback
from .tvheadend_helper import TVHeadendHelper


class Main:
	def __init__(self, debugMode):
		self.applicationExitHelper = ApplicationExitHelper()
		self.debugMode = debugMode
			
		self.lastEpgCheckFilename = ("debug/" if debugMode else "/var/lib/tvh-dvb-relay-power-control/") + "last-epg-check"
		self.logFilename = ("debug/" if debugMode else "/var/log/tvh-dvb-relay-power-control/") + "status.log"
		self.configFilename = ("debug/" if debugMode else "/etc/tvh-dvb-relay-power-control/") + "config.conf"

		self.conf = Config(self.configFilename)
		
		
	def run(self): 
		if (self.debugMode):
			os.makedirs("debug", exist_ok = True)
		
		# Setup logging
		self.__setupLogger()
			 
		logging.info("*** Application has started, logging has been set up ***")
		
		# Setup program exit signal handlers
		signal.signal(signal.SIGINT, self.__sigIntHandler)
		signal.signal(signal.SIGTERM, self.__sigTermHandler)
		
		systemHelper = SystemHelper()
		
		with GPIOHelper(self.conf) as gpioHelper, DVBDeviceHelper(gpioHelper, systemHelper) as dvbDeviceHelper, TVHeadendHelper(self.lastEpgCheckFilename, self.conf, dvbDeviceHelper, self.applicationExitHelper) as tvHeadendHelper:
			while (not self.applicationExitHelper.isExitRequested()):
				try:
					# Trigger OTA EPG grabber if required
					tvHeadendHelper.triggerOtaEpgGrabberIfRequired()
					
					# Check whether there are upcoming or running recordings
					tvHeadendHelper.switchDvbDevicePowerDependentOnUpcomingRecordings()
								
					logging.info("Check done. Waiting " + str(self.conf.MainCheckIntervalSeconds) + " seconds until the next check.")
								
					self.applicationExitHelper.sleepWhileNotExitRequested(self.conf.MainCheckIntervalSeconds)
						
				except:
					logging.error("An unrecoverable error occured: " + traceback.format_exc())
					gpioHelper.switchOnErrorLED()
					
					# Wait for the user to stop the application so he can see the red LED and react accordingly
					self.applicationExitHelper.waitForExitRequest()


	def __setupLogger(self):
		logFormatter = logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S")
		
		logFileHandler = RotatingFileHandler(self.logFilename, maxBytes = 5 * 1024 * 1024, backupCount = 1, encoding = "utf-8")
		logFileHandler.setFormatter(logFormatter)
		logFileHandler.setLevel(logging.DEBUG)
		
		logging.getLogger().addHandler(logFileHandler)
		logging.getLogger().setLevel(logging.DEBUG)
	

	def __sigIntHandler(self, signalNumber, stackFrame):
		logging.info("Received signal SIGINT. Requesting application exit.")
		
		self.applicationExitHelper.requestExit()
		

	def __sigTermHandler(self, signalNumber, stackFrame):
		logging.info("Received signal SIGTERM. Requesting application exit.")
		
		self.applicationExitHelper.requestExit()


def run():		
	argumentParser = argparse.ArgumentParser()
	argumentParser.add_argument("--debug", dest = "debug", action = "store_true", default = False)
	
	parsedArguments = argumentParser.parse_args()
	
	Main(parsedArguments.debug).run()
		
		
# run
if (__name__ == "__main__"):
	run()
