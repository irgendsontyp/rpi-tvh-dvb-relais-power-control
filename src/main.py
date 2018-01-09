import configparser
import datetime
import json
import logging
import RPi.GPIO as GPIO
import requests
import signal
import threading
import time
import traceback

TVHEADEND_OTA_EPG_GRABBER_WAIT_TIME = 1
TVHEADEND_OTA_EPG_LAST_TRIGGER_FILENAME = "/var/lib/tvh-dvb-relais-power-control/last-epg-check"
TVHEADEND_OTA_EPG_LAST_TRIGGER_TIMESTAMP_FORMAT = "%d.%m.%Y %H:%M:%S"

config = configparser.ConfigParser()
config.read("/etc/tvh-dvb-relais-power-control/config.conf")

GPIO_PIN_DVB_DEVICE_POWER_RELAY = config["gpio"].getint("pin_number_dvb_device_power_relay")
GPIO_PIN_ERROR_LED = config["gpio"].getint("pin_number_error_led")

TVHEADEND_URL = config["tvheadend-api"]["url"]
TVHEADEND_USERNAME = config["tvheadend-api"]["username"]
TVHEADEND_PASSWORD = config["tvheadend-api"]["password"]

MAX_SECONDS_UPCOMING_RECORDING = config["general"].getint("max-seconds-upcoming-recording")
MAIN_CHECK_INTERVAL_SECONDS = config["general"].getint("main-check-interval")

DVB_INPUT_AVAILABLE_CHECK_INTERVAL_SECONDS = config["dvb-input"].getint("input-available-check-interval")


event = threading.Event()


def logErrorAndLightUpErrorLED(errorMessage):
	logging.error(errorMessage)
	
	GPIO.output(GPIO_PIN_ERROR_LED, GPIO.HIGH)
	
	
def indicateDvbDeviceRequired(isRequired):
	GPIO.output(GPIO_PIN_DVB_DEVICE_POWER_RELAY, GPIO.LOW if isRequired else GPIO.HIGH)


def setupLogger():
	logging.basicConfig(filename='/var/log/tvh-dvb-relais-power-control/status.log', level = logging.DEBUG, format = "[%(asctime)s] %(message)s.", datefmt = "%Y-%m-%d %H:%M:%S")	



def checkEpgTriggerRequired():
	logging.info("Checking whether OTA EPG grabber must be triggered")
	
	try:
		with open(TVHEADEND_OTA_EPG_LAST_TRIGGER_FILENAME, "r") as lastEpgAccessFile:
			lastEpgAccessString = lastEpgAccessFile.read()
		
	except FileNotFoundError:
		logging.info("File \"" + TVHEADEND_OTA_EPG_LAST_TRIGGER_FILENAME + "\" was not found. OTA EPG grabber will be triggered")
		
		return True
	
	logging.info("OTA EPG grabber was last triggered at " + lastEpgAccessString)
		
	lastEpgAccessDatetime = datetime.datetime.strptime(lastEpgAccessString, TVHEADEND_OTA_EPG_LAST_TRIGGER_TIMESTAMP_FORMAT)
		
	if ((datetime.datetime.now() - lastEpgAccessDatetime).days >= 7):
		logging.info("7 or more days have past since the last time OTA EPG grabber was triggered. OTA EPG grabber will be triggered")
		
		return True
	else:
		logging.info("OTA EPG grabber will not be triggered")
		
		return False
		
		
def checkIsDvbInputAvailable():
	inputsResponse = requests.get(TVHEADEND_URL + "/api/status/inputs", auth = (TVHEADEND_USERNAME, TVHEADEND_PASSWORD))
	
	inputsObj = json.loads(inputsResponse.text)
	
	return (inputsObj["totalCount"] > 0)

		
def tryTriggerOtaEpgGrabberUntilSuccessful():
	# Wait for a DVB device to be connected
	while (True):
		logging.info("Checking whether a DVB input device is available")
		
		if (checkIsDvbInputAvailable()):
			logging.info("A DVB input device is available")
			
			break
		
		logging.info("No DVB input device is available. Checking again in " + str(DVB_INPUT_AVAILABLE_CHECK_INTERVAL_SECONDS) + " seconds")
		
		time.sleep(DVB_INPUT_AVAILABLE_CHECK_INTERVAL_SECONDS)
		
	# Trigger OTA Grabber and wait
	logging.info("Triggerung OTA EPG grabber")
	
	inputsResponse = requests.get(TVHEADEND_URL + "/api/epggrab/ota/trigger?trigger=300", auth = (TVHEADEND_USERNAME, TVHEADEND_PASSWORD))

	logging.info("Waiting " + str(TVHEADEND_OTA_EPG_GRABBER_WAIT_TIME) + " seconds for OTA EPG grabber to complete")
	
	time.sleep(TVHEADEND_OTA_EPG_GRABBER_WAIT_TIME)
	
	logging.info("Waiting for OTA EPG grabber has finished")
	
	lastEpgTriggerTimestampStr = datetime.datetime.now().strftime(TVHEADEND_OTA_EPG_LAST_TRIGGER_TIMESTAMP_FORMAT)
	
	logging.info("Writing timestamp \"" + lastEpgTriggerTimestampStr + "\" to file \"" + TVHEADEND_OTA_EPG_LAST_TRIGGER_FILENAME + "\"")
	
	with open(TVHEADEND_OTA_EPG_LAST_TRIGGER_FILENAME, "w") as lastEpgAccessFile:
		lastEpgAccessFile.write(lastEpgTriggerTimestampStr)


def triggerOtaEpgGrabberIfRequired():
	if checkEpgTriggerRequired():
		indicateDvbDeviceRequired(True)
		
		tryTriggerOtaEpgGrabberUntilSuccessful()
	
		# TODO: Should we disable the blue LED here? Currently it
		# will be disabled by the upcoming recording check
		# routine below
	
def checkForUpcomingOrRunningRecordings():
	logging.info("Checking whether there are upcoming or active recordings")
	
	upcomingRecordingsResponse = requests.get(TVHEADEND_URL + "/api/dvr/entry/grid_upcoming", auth = (TVHEADEND_USERNAME, TVHEADEND_PASSWORD))
	
	upcomingRecordingsObj = json.loads(upcomingRecordingsResponse.text)
	
	dvbDeviceRequired = False
	minDate = None
	
	for entry in upcomingRecordingsObj["entries"]:
		if entry["sched_status"] == "recording":
			dvbDeviceRequired = True
		
			logging.info("There is an active recording: \"" + entry["title"]["ger"] + "\"")
		
			break
		elif entry["enabled"]:
			entryStartDatetime = datetime.datetime.fromtimestamp(int(entry["start_real"]))
			
			if (minDate is None or entryStartDatetime < minDate):
				minDate = entryStartDatetime
				
				entryName = entry["title"]["ger"]

	if (not dvbDeviceRequired):
		if (minDate is not None):
			timeDifferenceFromNowToNextEvent = minDate - datetime.datetime.now()
			
			if (timeDifferenceFromNowToNextEvent.total_seconds() <= MAX_SECONDS_UPCOMING_RECORDING):	
				logging.info("There is an upcoming recording within the next " + str(MAX_SECONDS_UPCOMING_RECORDING) + " seconds: \"" + entryName + "\"")
				
				dvbDeviceRequired = True
			else:
				logging.info("The next upcoming recording is \"" + entryName + "\" which will start in " + str(int(timeDifferenceFromNowToNextEvent.total_seconds())) + " seconds, which is too far in the future")
		else:
			logging.info("There are no enabled recording entries")
			
	logging.info("Switching the DVB device relay " + ("on" if dvbDeviceRequired else "off"))
			
	indicateDvbDeviceRequired(dvbDeviceRequired)
	
	
class GPIOCleanup():
	def __enter__(self):
		logging.info("Setting up GPIOs. DVB device power relay is assigned to pin " + str(GPIO_PIN_DVB_DEVICE_POWER_RELAY) + ", error indicator LED is assigned to pin " + str(GPIO_PIN_ERROR_LED))
	
		GPIO.setmode(GPIO.BOARD)

		GPIO.setup(GPIO_PIN_DVB_DEVICE_POWER_RELAY, GPIO.OUT, initial = GPIO.HIGH)
		GPIO.setup(GPIO_PIN_ERROR_LED, GPIO.OUT, initial = GPIO.LOW)	
		
		logging.info("Finished setting up GPIOs")
		
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		GPIO.cleanup()
	
	
def sigIntHandler(signalNumber, stackFrame):
	logging.info("Received sigint")
	event.set()
	

def sigTermHandler(signalNumber, stackFrame):
	logging.info("Received sigterm")
	event.set()



def main():		
	# Setup logging
	setupLogger()
	
	logging.info("*** Application has started, logging has been set up ***")
	
	
	# Setup program exit signal handlers
	signal.signal(signal.SIGINT, sigIntHandler)
	signal.signal(signal.SIGTERM, sigTermHandler)
	
	
	with GPIOCleanup():
		while (not event.is_set()):
			try:
				# Trigger OTA EPG grabber if required
				triggerOtaEpgGrabberIfRequired()
				
				# Check whether there are upcoming or running recordings
				checkForUpcomingOrRunningRecordings()
			
				loopTimeoutInMilliseconds = MAIN_CHECK_INTERVAL_SECONDS * 1000
					
				# Sleep for MAIN_CHECK_INTERVAL_SECONDS in intervals of 10ms
				for i in range(1, loopTimeoutInMilliseconds // 10):
					if (event.is_set()):
						break
						
					time.sleep(0.01)
					
			except:
				logErrorAndLightUpErrorLED("An unrecoverable error occured: " + traceback.format_exc())
		
# run
main()
