#!/usr/bin/env python3

from tkinter import Tk
from sys import argv
from logging import getLogger, basicConfig, INFO, DEBUG
from base.gui import GUI
from base.cli import CLI

if __name__ == '__main__':	# start here if called as program / app / command
	params = argv[1:]
	if len(params) > 0 and ( params[0].lower() == '--debug' or params[0].lower() == 'debug' ):
		loglevel = DEBUG
		del params[0]
	else:
		loglevel = INFO
	basicConfig(level=loglevel, format='%(asctime)s - %(levelname)s - %(message)s')
	logger = getLogger()
	if len(params) == 0:
		root = Tk()
		GUI(root, logger)
		root.mainloop()
	else:
		CLI(params, logger)
