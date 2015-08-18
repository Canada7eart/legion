#! /usr/bin/env python2
from __future__ import with_statement, division, print_function
import cProfile
import time
import os, re
import launcher

def main():
	try:
		prof = cProfile.Profile()
		prof.enable()
		print("Started")
		launcher.main()
	finally:
		prof.disable()
		timestr = re.sub("[^\w]", "_", time.strftime("%x_x_%X"))
		prof.dump_stats("./prof/%s.prof" % timestr)

if __name__ == "__main__":
	main()
