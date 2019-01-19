#!/usr/bin/env python3

from modules.facebook import Facebook
from modules.instagram import Instagram
from modules.twitter import Twitter

class Worker:
	'Work through a list of jobs and execute modules'

	DEBUG = False
#	DEBUG = True	# do not continue on error

	DRYRUN = False
#	DRYRUN = True	# only print job(s) etc. to debug user interface


	MODULES = (	# the modules with options
		{
			'name': 'Facebook',
			'login': ('Email', 'Password'),
			'options': {
				'Timeline': {'name': 'Timeline', 'default': False, 'row': 0, 'column': 0},
				'expandTimeline': {'name': 'Expand posts', 'default': False, 'row': 0, 'column': 1},
				'translateTimeline': {'name': 'Translate posts', 'default': False, 'row': 0, 'column': 2},
				'untilTimeline': {'name': 'Until', 'default': Facebook.ONEYEARAGO, 'row': 0, 'column': 3},
				'limitTimeline': {'name': 'Limit', 'default': Facebook.DEFAULTPAGELIMIT, 'row': 0, 'column': 4},
				'About': {'name': 'About', 'default': False, 'row': 1, 'column': 0},
				'Photos': {'name': 'Photos', 'default': False, 'row': 2, 'column': 0},
				'expandPhotos': {'name': 'Expand comments', 'default': False, 'row': 2, 'column': 1},
				'translatePhotos': {'name': 'Translate comments', 'default': False, 'row': 2, 'column': 2},
				'limitPhotos': {'name': 'Max. number of pages of photos', 'default': Facebook.DEFAULTPAGELIMIT, 'row': 2, 'column': 3},
				'Network': {'name': 'Network', 'default': False, 'row': 3, 'column': 0},
				'depthNetwork': {'name': 'Depth of recursion', 'default': Facebook.DEFAULTNETWORKDEPTH, 'row': 3,'column': 1},
				'extendNetwork': {'name': 'include Timeline commentors/likers', 'default': False, 'row': 3, 'column': 2}
			}
		},
		{
			'name': 'Instagram',
			'login': None,
			'options': {
				'Media': {'name': 'Download media', 'default': False, 'row': 0, 'column': 0},
				'limitPages': {'name': 'Maximal pages', 'default': Instagram.DEFAULTPAGELIMIT, 'row': 1, 'column': 0}
			}
		},
		{
			'name': 'Twitter',
			'login': None,
			'options': {
				'Search': {'name': 'Perform Twitter Search\ninstead of targetting accounts', 'default': False, 'row': 0, 'column': 0},
				'Photos': {'name': 'Photos', 'default': False, 'row': 1, 'column': 0},
				'limitPages': {'name': 'Limit', 'default': Twitter.DEFAULTPAGELIMIT, 'row': 2, 'column': 0}
			}
		}
	)

	def __init__(self, storage, chrome):
		'Create object that works out the jobs'
		self.storage = storage
		self.chrome = chrome
		self.modulenames = [ i['name'] for i in self.MODULES ]
		self.logins = dict()
		self.options = dict()
		for i in self.MODULES:
			if i['login'] != None:
				self.logins[i['name']] = { j: '' for j in i['login'] }
			else:
				self.logins[i['name']] = None
			if i['options'] != None:
				self.options[i['name']] = { j: i['options'][j] for j in i['options'] }
			else:
				self.options[i['name']] = None
		self.options_defaults = { i: { j: self.options[i][j]['default'] for j in self.options[i] } for i in self.options }

	def new_job(self, module):
		'Create new empty job'
		job = {'module': module, 'target': ''}
		try:
			job['options'] = self.options_defaults[module]
		except KeyError:
			job['options'] = None
		try:
			job['login'] = self.logins[module]
		except KeyError:
			job['login'] = None
		return job

	def execute_job(self, job, headless=True, stop=None):
		'Execute jobs'
		message = ''
		self.storage.mkmoddir(job['module'])
		cmd = '%s(job, self.storage, self.chrome, stop=stop, headless=headless, debug=self.DEBUG)' % job['module']
		if self.DRYRUN:
			print('----------------------------------------')
			print('job:', job)
			print('chrome.path:', self.chrome.path)
			print('output directory:', self.storage.moddir)
			print('cmd:', cmd)
			print('----------------------------------------')
		else:
			if self.DEBUG:
				exec(cmd)
			else:
				try:
					exec(cmd)
				except Exception as error:
					message += str(error) + '\n'
		return message
