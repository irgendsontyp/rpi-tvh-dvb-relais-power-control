import configparser


class Config:
	def __init__(self, filename):
		config = configparser.ConfigParser()
		config.read(filename)

		self.__pinNumberDvbDevicePowerRelay = config["gpio"].getint("pin_number_dvb_device_power_relay")
		self.__pinNumberErrorLed = config["gpio"].getint("pin_number_error_led")

		self.__tvheadendUrl = config["tvheadend-api"]["url"]
		self.__tvheadendUsername = config["tvheadend-api"]["username"]
		self.__tvHeadendPassword = config["tvheadend-api"]["password"]

		self.__maxSecondsUpcomingRecording = config["general"].getint("max-seconds-upcoming-recording")
		self.__mainCheckIntervalSeconds = config["general"].getint("main-check-interval")
		self.__tvHeadendOtaEpgGrabberWaitTime = config["general"].getint("ota-epg-wait-time")
		self.__epgMaxAgeDays = config["general"].getint("epg-max-age")

		self.__dvbInputAvailableCheckIntervalSeconds = config["dvb-input"].getint("input-available-check-interval")
		
	
	@property
	def PinNumberDVBDevicePowerRelay(self):
		return self.__pinNumberDvbDevicePowerRelay
		
		
	@property
	def PinNumberErrorLED(self):
		return self.__pinNumberErrorLed
		
		
	@property
	def TVHeadendURL(self):
		return self.__tvheadendUrl
		
		
	@property
	def TVHeadendUsername(self):
		return self.__tvheadendUsername
		
		
	@property
	def TVHeadendPassword(self):
		return self.__tvHeadendPassword
		
		
	@property
	def MaxSecondsUpcomingRecording(self):
		return self.__maxSecondsUpcomingRecording
		
		
	@property
	def MainCheckIntervalSeconds(self):
		return self.__mainCheckIntervalSeconds
		
		
	@property
	def TVHeadendOTAEPGGrabberWaitTime(self):
		return self.__tvHeadendOtaEpgGrabberWaitTime
		
		
	@property
	def EPGMaxAge(self):
		return self.__epgMaxAgeDays
		
		
	@property
	def DVBInputAvailableCheckIntervalSeconds(self):
		return self.__dvbInputAvailableCheckIntervalSeconds
