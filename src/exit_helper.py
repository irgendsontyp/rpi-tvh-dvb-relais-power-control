import threading


class ExitHelper:
	def __init__(self):
		self.__exitEvent = threading.Event()
		
		
	def isExitRequested(self):
		return self.__exitEvent.is_set()
		
		
	def requestExit(self):
		self.__exitEvent.set()
		
		
	def waitForExitRequest(self):
		self.__exitEvent.wait()


	def sleepWhileNotExitRequested(self, seconds):
		self.__exitEvent.wait(seconds)
