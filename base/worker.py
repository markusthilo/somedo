#!/usr/bin/env python3

from modules.facebook import Facebook
from modules.instagram import Instagram
from modules.twitter import Twitter

class Worker:
	'Work through a list of jobs and execute modules'

	DEBUG = True
	MODULES = (
		{
			'name': 'Facebook',
			'login': ('Email', 'Password'),
			'options': {
				'timeline': {'name': 'Timeline', 'default': False, 'row': 0, 'column': 0},
				'expand_timeline': {'name': 'Expand posts', 'default': False, 'row': 0, 'column': 1},
				'translate_timeline': {'name': 'Translate posts', 'default': False, 'row': 0, 'column': 2},
				'timeline_until': {'name': 'Until', 'default': Facebook.ONEYEARAGO, 'row': 0, 'column': 3},
				'timeline_limit': {'name': 'Limit', 'default': Facebook.DEFAULTPAGELIMIT, 'row': 0, 'column': 4},
				'about': {'name': 'About', 'default': False, 'row': 1, 'column': 0},
				'photos': {'name': 'Photos', 'default': False, 'row': 2, 'column': 0},
				'expand_photos': {'name': 'Expand comments', 'default': False, 'row': 2, 'column': 1},
				'translate_photos': {'name': 'Translate comments', 'default': False, 'row': 2, 'column': 2},
				'photos_limit': {'name': 'Limit', 'default': Facebook.DEFAULTPAGELIMIT, 'row': 2, 'column': 3},
				'network': {'name': 'Network', 'default': False, 'row': 3, 'column': 0},
				'network_depth': {'name': 'Depth', 'default': Facebook.DEFAULTNETWORKDEPTH, 'row': 3,'column': 1},
				'network_visitors': {'name': 'include Timeline visitors', 'default': False, 'row': 3, 'column': 2},
				'visitors_limit': {'name': 'Limit', 'default': Facebook.DEFAULTPAGELIMIT, 'row': 3, 'column': 3}
			}
		},
		{
			'name': 'Instagram',
			'login': None,
			'options': {
				'media': {'name': 'Expand comments', 'default': False, 'row': 0, 'column': 0},
				'limit': {'name': 'Limit', 'default': Instagram.DEFAULTPAGELIMIT, 'row': 1, 'column': 0}
			}
		},
		{
			'name': 'Twitter',
			'login': None,
			'options': {
				'search': {'name': 'Search', 'default': False, 'row': 0, 'column': 0},
				'photos': {'name': 'Photos', 'default': False, 'row': 1, 'column': 0},
				'limit': {'name': 'Limit', 'default': Twitter.DEFAULTPAGELIMIT, 'row': 2, 'column': 0}
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
		self.directory = self.storage.mkmoddir(job['module'])
		cmd = '%s(job,  self.storage, self.chrome, stop=stop, headless=headless, debug=True)' % job['module']
		if self.DEBUG:
			exec(cmd)
		else:
			try:
				exec(cmd)
			except Exception as error:
				message += str(error) + '\n'
		return message

	def execute_jobs(self, jobs, headless=True, stop=None):
		'Execute jobs'
		message = ''
		for i in jobs:
			message += execute_job(i)
		return message
