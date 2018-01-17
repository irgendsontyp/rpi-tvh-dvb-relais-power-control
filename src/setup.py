from setuptools import setup, find_packages
import rpitvhdvbrelaypowercontrol

setup(name = "rpi-tvh-dvb-relay-power-control",
      version = rpitvhdvbrelaypowercontrol.__version__,
      description = "Switches a relay on or off depending on whether there are upcoming or running recording entries in TVHeadend or not",
      author = "irgendsontyp",
      url = "https://github.com/irgendsontyp/rpi-tvh-dvb-relay-power-control.git",
      dependency_links = ["git+https://github.com/irgendsontyp/python-irgendsontyp-helpers.git/@1.1.0#egg=irgendsontyp-helpers-1.1.0"],
      install_requires = ["irgendsontyp-helpers==1.1.0", "Rpi.GPIO", "requests"],
      packages = find_packages()
     )
