import logging
import subprocess


class SystemHelper:
	def unloadDvbDevice(self):
		logging.info("Stopping service \"tvheadend\".")
		subprocess.run(["sudo", "systemctl", "stop", "tvheadend"], check = True)
		logging.info("Service \"tvheadend\" was successfully stopped.")

		logging.info("Removing kernel module \"dvb_usb_dvbsky\".")
		subprocess.run(["sudo", "modprobe", "-r", "dvb_usb_dvbsky"], check = True)
		logging.info("Kernel module \"dvb_usb_dvbsky\" was successfully removed")

		logging.info("Starting service \"tvheadend\".")
		subprocess.run(["sudo", "systemctl", "start", "tvheadend"], check = True)
		logging.info("Service \"tvheadend\" was successfully started.")
