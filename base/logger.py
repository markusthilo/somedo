#!/usr/bin/env python3

from logging import getLogger, basicConfig, addLevelName, Handler, INFO, DEBUG
from logging import Logger as ParentLogger

INFO = INFO
DEBUG = DEBUG
TRACE = DEBUG - 1	# loglevel to start chrome in visible mode

class Logger():
	'Configure logging'

	def __init__(self, loglevel):
		addLevelName(TRACE, "TRACE")
		def __trace__(self, msg, *args, **kws):	# adding output method visible to logger
			self._log(TRACE, msg, args, **kws) 
		ParentLogger.trace = __trace__
		try:
			level = {'info': INFO, 'debug': DEBUG, 'trace': TRACE}[loglevel.lower()]
		except KeyError:
			level = INFO
		basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

	def get(self):
		'Get the logging function'
		return getLogger()
