#!/usr/bin/env python3

from base.chrometools import *
from base.storage import *
from modules.facebook import *
from modules.instagram import *

MODULE_DEFINITIONS = [Facebook.DEFINITION, Instagram.DEFINITION]

class Worker:
	''' Work through a list of jobs and execute modules.
		The modules must be in the same directory as this script.
		The modules needs definitions (type: list) in this form:
		
		from base.chrometools import *
		from base.storage import *
		class Modulename:
			DEFINITION = [
				'NAME',
				['Email', 'Password', ...]
				[
					[['1st Action', True]],
					[['2nd Action', False], ['Option 1', False], ['Option 2', False], ['Parameter', 0]],
					...
				]
			]
		def __init__(self, targets, options, login, chrome, storage, stop=stop_thread):
		...
		targets: string that is given to your class/object
		options: dictionary of dictionarys that is given to your class/object
		login: dictionary with the credentials to login
		chrome: object Chrome from base.chrometools
		storage: object Storage from base.storage
		stop_thread: threading.Event object to give the abort signal, None if not set
	'''

	def __init__(self):
		'Create object that works out the jobs'
		self.mods = [ i[0] for i in sorted(MODULE_DEFINITIONS) ]	# list of all the loaded somedo modules
		self.logins = { i[0]: i[1] for i in MODULE_DEFINITIONS }
		self.opts = { i[0]: i[2] for i in MODULE_DEFINITIONS }

	def execute(self, jobs, config, headless=True, stop=None):
		'Execute jobs'
		message = 'Errors occurred:\n'
		chrome = Chrome(config['Chrome'], headless=headless)
		for i in jobs:
############################################################################## DEBUG
#			try:
			exec('%s(i[1], i[2], config[i[0]], chrome, Storage(config["Output directory"], i[0]), stop=stop)' % i[0])
#			except Exception as error:
#				message += str(error) + '\n'
		chrome.close()
		if message == 'Errors occurred:\n':
			return 'All done'
		else:
			return message
