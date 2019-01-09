#!/usr/bin/env python3

from modules.facebook import Facebook
from modules.instagram import Instagram
from modules.twitter import Twitter

MODULE_DEFINITIONS = [	# to load definitions for each module
	Facebook.DEFINITION,
	Instagram.DEFINITION,
	Twitter.DEFINITION
]

class Worker:
	''' Work through a list of jobs and execute modules.
		The modules needs definitions (type: list) in this form:

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
		def __init__(target, options, login, storage, chrome, stop=None, headless=True, debug=False):
		...
		targets: string that is given to your class/object
		options: dictionary of dictionarys that is given to your class/object
		login: dictionary with the credentials to login
		chrome: object Chrome from base.chrometools
		storage: object Storage from base.storage
		stop_thread: threading.Event object to give the abort signal, None if not set
	'''

	def __init__(self, storage, chrome, debug=False):
		'Create object that works out the jobs'
		self.storage = storage
		self.chrome = chrome
		self.debug = debug
		self.mods = [ i[0] for i in MODULE_DEFINITIONS ]	# list of all the loaded somedo modules
		self.logins = { i[0]: i[1] for i in MODULE_DEFINITIONS }
		self.opts = { i[0]: i[2] for i in MODULE_DEFINITIONS }

	def execute(self, jobs, config, headless=True, stop=None):
		'Execute jobs'
		message = ''
		for i in jobs:
			self.storage.mkmoddir(i[0])
			if self.debug:
				exec('%s(i[1], i[2], config[i[0]], self.storage, self.chrome, stop=stop, headless=headless, debug=self.debug)' % i[0])
			else:
				try:
					exec('%s(i[1], i[2], config[i[0]], self.storage, stop=stop, headless=headless, debug=self.debug)' % i[0])
				except Exception as error:
					message += str(error) + '\n'
		if message == '':
			return 'All done'
		return 'Errors occurred:\n' + message
