#!/usr/bin/env python3

from logging import getLogger, basicConfig, addLevelName, Handler, INFO, DEBUG
from logging import Logger as ParentLogger

INFO = INFO
DEBUG = DEBUG
VISIBLE = DEBUG - 1	# loglevel to start chrome in visible mode

class Logger():
	'Configure logging'

	def __init__(self, loglevel):
		addLevelName(VISIBLE, "VISIBLE")
		def __visible__(self, msg, *args, **kws):	# adding output method visible to logger
			self._log(VISIBLE, msg, args, **kws) 
		ParentLogger.visible = __visible__
		try:
			level = {'info': INFO, 'debug': DEBUG, 'visible': VISIBLE}[loglevel.lower()]
		except KeyError:
			level = INFO
		basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

	def get(self):
		'Get the logging function'
		return getLogger()
