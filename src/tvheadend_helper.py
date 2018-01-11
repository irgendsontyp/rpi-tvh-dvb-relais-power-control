import datetime
import logging
import json
import requests
import time


class TVHeadendHelper:
	def __init__(self, conf, dvbDeviceHelper, exitHelper):
		self.__conf = conf
		self.__dvbDeviceHelper = dvbDeviceHelper
		self.__exitHelper = exitHelper
		
		self.__tvHeadendOtaEpgLastTriggerFilename = "/var/lib/tvh-dvb-relay-power-control/last-epg-check"
		self.__tvHeadendOtaEpgLastTriggerTimestampFormat = "%d.%m.%Y %H:%M:%S"
	
	
	def checkEpgTriggerRequired(self):
		logging.info("Checking whether OTA EPG grabber must be triggered.")
		
		try:
			with open(self.__tvHeadendOtaEpgLastTriggerFilename, "r") as lastEpgAccessFile:
				lastEpgAccessString = lastEpgAccessFile.read()
			
		except FileNotFoundError:
			logging.info("File \"" + self.__tvHeadendOtaEpgLastTriggerFilename + "\" was not found. OTA EPG grabber will be triggered.")
			
			return True
		
		logging.info("OTA EPG grabber was last triggered at " + lastEpgAccessString + ".")
			
		lastEpgAccessDatetime = datetime.datetime.strptime(lastEpgAccessString, self.__tvHeadendOtaEpgLastTriggerTimestampFormat)
			
		if ((datetime.datetime.now() - lastEpgAccessDatetime).days >= self.__conf.EPGMaxAge):
			logging.info(str(self.__conf.EPGMaxAge) + " or more days have past since the last time OTA EPG grabber was triggered. OTA EPG grabber will be triggered.")
			
			return True
		else:
			logging.info("OTA EPG grabber will not be triggered.")
			
			return False
		
		
	def switchDvbDevicePowerDependentOnUpcomingRecordings(self):
		logging.info("Checking whether there are upcoming or active recordings.")
		
		upcomingRecordingsResponse = requests.get(self.__conf.TVHeadendURL + "/api/dvr/entry/grid_upcoming", auth = (self.__conf.TVHeadendUsername, self.__conf.TVHeadendPassword))
		
		upcomingRecordingsObj = json.loads(upcomingRecordingsResponse.text)
		
		dvbDeviceRequired = False
		minDate = None
		
		for entry in upcomingRecordingsObj["entries"]:
			if entry["sched_status"] == "recording":
				dvbDeviceRequired = True
			
				logging.info("There is an active recording: \"" + entry["title"]["ger"] + "\".")
			
				break
			elif entry["enabled"]:
				entryStartDatetime = datetime.datetime.fromtimestamp(int(entry["start_real"]))
				
				if (minDate is None or entryStartDatetime < minDate):
					minDate = entryStartDatetime
					
					entryName = entry["title"]["ger"]

		if (not dvbDeviceRequired):
			if (minDate is not None):
				timeDifferenceFromNowToNextEvent = minDate - datetime.datetime.now()
				
				if (timeDifferenceFromNowToNextEvent.total_seconds() <= self.__conf.MaxSecondsUpcomingRecording):	
					logging.info("There is an upcoming recording within the next " + str(self.__conf.MaxSecondsUpcomingRecording) + " seconds: \"" + entryName + "\".")
					
					dvbDeviceRequired = True
				else:
					logging.info("The next upcoming recording is \"" + entryName + "\" which will start in " + str(int(timeDifferenceFromNowToNextEvent.total_seconds())) + " seconds, which is too far in the future.")
			else:
				logging.info("There are no enabled recording entries.")
				
				
		if (dvbDeviceRequired):
			logging.info("Switching the DVB device relay on.")
			
			self.__switchOnAndEnableDvbDevice()
		else:
			logging.info("Switching the DVB device relay off.")
			
			self.__disableDvbDevice()
			self.__dvbDeviceHelper.switchOffDvbDevice()
			
			
	def triggerOtaEpgGrabberIfRequired(self):
		if self.checkEpgTriggerRequired():
			self.__switchOnAndEnableDvbDevice()
			
			self.__tryTriggerOtaEpgGrabberUntilSuccessful()
			
			
	def __waitUntilDvbDeviceIsAvailable(self):
		# Wait for a DVB device to be connected
		while (True):
			logging.info("Checking whether a DVB input device is available.")
			
			if (self.__checkIsDvbInputAvailable()):
				logging.info("A DVB input device is available.")
				
				break
			
			logging.info("No DVB input device is available. Checking again in " + str(self.__conf.DVBInputAvailableCheckIntervalSeconds) + " seconds.")
			
			sleepMilliseconds = self.__conf.DVBInputAvailableCheckIntervalSeconds * 1000
			
			for i in range(1, sleepMilliseconds // 10):
				time.sleep(0.01)
				
				if (self.__exitHelper.isExitRequested()):
					return
			
			
	def __tryTriggerOtaEpgGrabberUntilSuccessful(self):
		self.__waitUntilDvbDeviceIsAvailable()
			
		# Trigger OTA Grabber and wait
		logging.info("Triggering OTA EPG grabber.")
		
		inputsResponse = requests.get(self.__conf.TVHeadendURL + "/api/epggrab/ota/trigger?trigger=" + str(self.__conf.TVHeadendOTAEPGGrabberWaitTime), auth = (self.__conf.TVHeadendUsername, self.__conf.TVHeadendPassword))

		logging.info("Waiting " + str(self.__conf.TVHeadendOTAEPGGrabberWaitTime) + " seconds for OTA EPG grabber to complete.")
		
		
		sleepMilliseconds = self.__conf.TVHeadendOTAEPGGrabberWaitTime * 1000
		
		
		for i in range(1, sleepMilliseconds // 10):
			time.sleep(0.01)
			
			if (self.__exitHelper.isExitRequested()):
				return
	
		logging.info("Waiting for OTA EPG grabber has finished.")
		
		lastEpgTriggerTimestampStr = datetime.datetime.now().strftime(self.__tvHeadendOtaEpgLastTriggerTimestampFormat)
		
		logging.info("Writing timestamp \"" + lastEpgTriggerTimestampStr + "\" to file \"" + self.__tvHeadendOtaEpgLastTriggerFilename + "\".")
		
		with open(self.__tvHeadendOtaEpgLastTriggerFilename, "w") as lastEpgAccessFile:
			lastEpgAccessFile.write(lastEpgTriggerTimestampStr)
		
			
	def __checkIsDvbInputAvailable(self):
		rootDvbDevices = self.__retrieveDvbDeviceTree("root")
		
		return (len(rootDvbDevices) > 0)
		
		
	def __retrieveDvbDeviceTree(self, uuid):
		dvbDeviceTreeResponse = requests.post(self.__conf.TVHeadendURL + "/api/hardware/tree", auth = (self.__conf.TVHeadendUsername, self.__conf.TVHeadendPassword), data = {"uuid" : uuid})
		
		return json.loads(dvbDeviceTreeResponse.text)
		
		
	def __sendDvbDeviceEnableRequest(self, enable):
		logging.info("Trying to retrieve all root DVB devices.")
		
		# First, retrieve all root device nodes
		rootDvbDevices = self.__retrieveDvbDeviceTree("root")
		
		logging.info("Successfully retrieved all root DVB devices.")
		
		# Then, retrieve their children
		for rootDvbDevice in rootDvbDevices:
			logging.info("Trying to retrieve all child DVB devices for root DVB device with UUID \"" + rootDvbDevice["uuid"] + "\".") 
			
			childDvbDevices = self.__retrieveDvbDeviceTree(rootDvbDevice["uuid"])
			
			logging.info("Successfully retrieved all child DVB devices for root DVB device with UUID \"" + rootDvbDevice["uuid"] + "\".") 
			
			# Enable or disable
			for childDvbDevice in childDvbDevices:
				logging.info("Trying to set enabled state to \"" + str(enable) + "\" for child DVB device with UUID \"" + childDvbDevice["uuid"] + "\".")
				
				# Set enabled state
				enableOrDisablePostObject = {"uuid" : childDvbDevice["uuid"], "enabled" : enable}
				enableOrDisablePostJsonString = json.dumps(enableOrDisablePostObject)	
						
				response = requests.post(self.__conf.TVHeadendURL + "/api/idnode/save", auth = (self.__conf.TVHeadendUsername, self.__conf.TVHeadendPassword), data = {"node" : enableOrDisablePostJsonString})

				logging.info("Successfully set enabled state to \"" + str(enable) + "\" for child DVB device with UUID \"" + childDvbDevice["uuid"] + "\".")
		
		
	def __switchOnAndEnableDvbDevice(self):
		self.__dvbDeviceHelper.switchOnDvbDevice()
		self.__waitUntilDvbDeviceIsAvailable()
		self.__sendDvbDeviceEnableRequest(True)


	def __disableDvbDevice(self):	
		self.__sendDvbDeviceEnableRequest(False)
