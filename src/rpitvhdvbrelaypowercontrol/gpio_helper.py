import logging
import RPi.GPIO as GPIO


class GPIOHelper:	
	def __init__(self, conf):
		self.__conf = conf
		
		logging.info("Setting up GPIO.")
		
		GPIO.setmode(GPIO.BOARD)
		
		logging.info("GPIO pin number for DVB Device power relay is set to " + str(conf.PinNumberDVBDevicePowerRelay) + ".")
		GPIO.setup(self.__conf.PinNumberDVBDevicePowerRelay, GPIO.OUT, initial = GPIO.HIGH)
		
		logging.info("GPIO pin number for error indicator LED is set to " + str(conf.PinNumberErrorLED) + ".")
		GPIO.setup(self.__conf.PinNumberErrorLED, GPIO.OUT, initial = GPIO.LOW)
		
	
	def __enter__(self):
		return self	
	
		
	def __exit__(self, type, value, traceback):
		GPIO.cleanup()
		
		
	def switchOnErrorLED(self):
		GPIO.output(self.__conf.PinNumberErrorLED, GPIO.HIGH)
	
		
	def switchOnDvbDevice(self):
		GPIO.output(self.__conf.PinNumberDVBDevicePowerRelay, GPIO.LOW)
		
		
	def switchOffDvbDevice(self):
		GPIO.output(self.__conf.PinNumberDVBDevicePowerRelay, GPIO.HIGH)
