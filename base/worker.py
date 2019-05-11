#!/usr/bin/env python3

from time import sleep
from base.logger import Logger, DEBUG
from base.storage import Storage
from base.chrometools import Chrome
from modules.facebook import Facebook
from modules.instagram import Instagram
from modules.twitter import Twitter

class Worker:
	'Work through a list of jobs and execute modules'

	MODULES = (Facebook.OPTIONS, Instagram.OPTIONS, Twitter.OPTIONS)

	def __init__(self, loglevel):
		'Create object that works out the jobs'
		logger = Logger(loglevel)	# configure logging
		self.logger = logger.get()	# get the logging function
		self.storage = Storage(self.logger)	# object for file system accesss
		self.chrome = Chrome(self.logger)	# object to work with chrome/chromium
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

	def execute_job(self, job, jobnumber=None, stop=None):
		'Execute jobs'
		if jobnumber == None:
			self.storage.mkmoddir(job['module'])
		else:
			self.storage.mkmoddir('{:02}_'.format(jobnumber) + job['module'])
		cmd = '%s(job, self.storage, self.chrome, stop=stop)' % job['module']
		self.logger.debug('Worker: job: %s' % job)
		self.logger.debug('Worker: chrome.path: %s' % self.chrome.path)
		self.logger.debug('Worker: output directory: %s' % self.storage.moddir)
		self.logger.debug('Worker: cmd: %s' % cmd)
		self.logger.debug('Worker: loglevel: %s' % self.logger.level)
		if self.logger.level <= DEBUG :
			exec(cmd)
		else:
			try:
				exec(cmd)
			except:
				pass
		if self.chrome.is_running():
			self.logger.warning('Worker: Chrome/Chromium was still running finishing jobs')
			if self.logger.level < DEBUG:
				self.logger.trace('Worker: finished, now sleeping for 5 seconds until closing browser')
				sleep(5)
			self.chrome.close()
		self.logger.debug('Worker: done!')
