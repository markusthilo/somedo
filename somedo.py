#!/usr/bin/env python3

#from tkinter import Tk
from sys import argv
from base.worker import Worker
from base.gui import GUI, Tk
from base.cli import CLI

if __name__ == '__main__':	# start here if called as program / app / command
	params = argv[1:]
	if len(params) > 0 and params[0].lower() in ('--debug', '-debug', 'debug'):
		loglevel = 'debug'
		del params[0]
	elif len(params) > 0 and params[0].lower() in ('--visible', '-visible', 'visible'):
		loglevel = 'visible'
		del params[0]
	else:
		loglevel = 'info'
	if len(params) == 0:
		root = Tk()
		GUI(root, Worker(loglevel))
		root.mainloop()
	else:
		CLI(params, Worker(loglevel))
