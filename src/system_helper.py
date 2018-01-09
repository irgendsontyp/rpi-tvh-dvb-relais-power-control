import logging
import subprocess


class SystemHelper:
	def unloadDvbDevice(self):
		logging.info("Removing kernel module \"dvb_usb_dvbsky\".")
		subprocess.run(["sudo", "modprobe", "-r", "dvb_usb_dvbsky"], check = True)
		logging.info("Kernel module \"dvb_usb_dvbsky\" was successfully removed")
