#!/usr/bin/env python3

import sys, os
from setuptools import setup
from setuptools import find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, "README")).read()

required_version = (3, 3)
if sys.version_info < required_version:
	raise SystemExit("Migen requires python {0} or greater".format(
		".".join(map(str, required_version))))

setup(
	name="migen",
	version="unknown",
	description="Python toolbox for building complex digital hardware",
	long_description=README,
	author="Sebastien Bourdeauducq",
	author_email="sebastien@milkymist.org",
	url="http://www.milkymist.org",
	download_url="https://github.com/milkymist/migen",
	packages=find_packages(here),
	test_suite="migen.test",
	license="BSD",
	platforms=["Any"],
	keywords="HDL ASIC FPGA hardware design",
	classifiers=[
		"Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
		"Environment :: Console",
		"Development Status :: Alpha",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: BSD License",
		"Operating System :: OS Independent",
		"Programming Language :: Python",
	],
)
