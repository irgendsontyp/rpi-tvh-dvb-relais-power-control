class DVBDeviceHelper:
	def __init__(self, gpioHelper, systemHelper):
		self.__gpioHelper = gpioHelper
		self.__systemHelper = systemHelper
		
		
	def __enter__(self):
		return self
		
		
	def __exit__(self, type, value, traceback):
		self.switchOffDvbDevice()
		
	
	def switchOnDvbDevice(self):
		self.__gpioHelper.switchOnDvbDevice()


	def switchOffDvbDevice(self):
		self.__systemHelper.unloadDvbDevice()
		self.__gpioHelper.switchOffDvbDevice()
