#!/usr/bin/python3

from sys import stderr as sys_stderr
from sys import exit as sys_exit
from base.storage import Storage
from base.worker import Worker
from base.chrometools import Chrome

class CLI:
	'Command Line Interface for Somedo'

	def __init__(self, clargs):
		'Generate object to parse the command line arguments and execute a job'
		self.storage = Storage()	# object for file system accesss
		if len(clargs) < 2 or clargs[1].lower() in ('-h', '-help', 'h', 'help'):
			for i in ('README.md', 'README.txt', 'README.md.txt', 'README.txt.md', 'README'):
				try:
					with open(self.storage.rootdir + self.storage.slash + i, 'r', encoding='utf-8') as f:
						about_help = f.read()
					print(about_help)
					sys_exit(0)
				except:
					sys_exit(0)
			self.__error__('Go to https://github.com/markusthilo/somedo or https://sourceforge.net/p/somedo/wiki/Somedo/ for Infos.')
		self.chrome = Chrome()	# object to work with chrome/chromium
		self.worker = Worker(self.storage, self.chrome)	# generate object for the worker (smd_worker.py)
		if clargs[1] in ('-f', '-file', '--file', '-r', '-read', '--read'):
			try:
				with open(clargs[2], 'r', encoding='utf-8') as f:
					jobfile = f.read()
			except:
				self.__error__('Could not open file to read job(s).')
			jobs = [ self.__job__([ j for j in i.split(' ') if j != '' ]) for i in jobfile.split('\n') if i != '' ]
			self.__execute_jobs__(jobs=jobs)
			sys_exit(0)
		self.__job__(clargs[1:])
		self.__execute_jobs__()
		sys_exit(0)

	def __error__(self, msg):
		'Print error message to stderr and quit application returning 1 to Shell'
		sys_stderr.write('ERROR: ' + msg)
		sys_exit(1)

	def __job__(self, args):
		'Run one job'
		self.args = args
		if not self.args[0] in self.worker.modulenames:
			msg = 'First argument has to be the module name. Available: '
			for i in self.worker.modulenames:
				msg += i + ', '
			self.__error__(msg[:-2])
			return True
		self.job = self.worker.new_job(self.args.pop(0))
		self.headless = True
		self.chrome_set = False
		self.outdir_set = False
		self.target_set = False
		self.login_set = False
		self.options_set = False
		while len(self.args) > 0:
			opt = self.args.pop(0)
			if opt in ('-v', '-verbose', '--verbose'):
				self.headless = False
				continue
			if len(self.args) < 1:
				self.__error__('Undecodable argument "%s".' % opt)
			if opt in ('-c', '-chrome', '--chrome'):
				self.__chrome__()
			elif opt in ('-d', '-dir', '-outdir', '--dir', '--outdir'):
				self.__outdir__()
			elif opt in ('-t', '-target', '-targets', '--target', '--targets'):
				self.__target__()
			elif opt in ('-l', '-login', '--login'):
				self.__login__()
			elif opt in ('-o', '-option', '-options', '--option', '--options'):
				self.__options__()
			else:
				self.__error__('Unknown option "%s".' % opt)
		if self.job['target'] == '':
			self.__error__('Job without target will not work')
		return(self.job)

	def __2margs__(self):
		'Too many arguments'
		self.__error__('Too many arguments.')

	def __wmarg__(self, opt):
		'Wrong or missing argument'
		self.__error__('Wrong or missing argument for %s.' % opt)

	def __chrome__(self):
		'Set path to Chrome/Chromium'
		if self.chrome_set:
			self.__2margs__()
		try:
			self.chrome.path = self.args.pop(0)
		except:
			self.__wmarg__('--chrome or -c')
		self.chrome_set = True

	def __outdir__(self):
		'Set output directory'
		if self.outdir_set:
			self.__2margs__()
		try:
			self.storage.outdir = self.args.pop(0)
		except:
			self.__wmarg__('--dir / -d')
		self.outdir_set = True

	def __target__(self):
		'Set output directory'
		if self.target_set:
			self.__2margs__()
		try:
			self.job['target'] = self.args.pop(0)
		except:
			self.__wmarg__('--target / -t')
		self.target_set = True

	def __login__(self):
		'Get login credentials'
		if self.login_set:
			self.__2margs__()
		if self.job['login'] == None:
			self.__error__('Module %s does not take login data' % self.job['module'])
		self.login_set = True
		while True:
			try:
				arg = self.args[0].split('=', 1)
			except:
				return
			if len(arg) < 2:
				return
			if arg[0] in self.job['login']:
				self.job['login'][arg[0]] = arg[1]
			else:
				self.__error__('Unknown login argument "%s".' % arg[0])
			self.args.pop(0)

	def __options__(self):
		'Get the job options'
		if self.options_set:
			self.__2margs__()
		self.options_set = True
		while True:
			try:
				arg = self.args[0].split('=', 1)
			except:
				return
			if len(arg) < 2:
				return
			if arg[0] in self.job['options']:
				if isinstance(self.job['options'][arg[0]], bool):
					if arg[1] in ('True', 'T', 'true', 't', '+', '1'):
						self.job['options'][arg[0]] = True
					else:
						self.job['options'][arg[0]] = False
				elif isinstance(self.job['options'][arg[0]], int):
					self.job['options'][arg[0]] = int(arg[1])
				else:
					self.job['options'][arg[0]] = arg[1]
			else:
				self.__error__('Unknown option "%s".' % arg[0])
			self.args.pop(0)

	def __execute_jobs__(self, jobs=None):
		'Execute/start job or jobs'
		if jobs == None:
			jobs = [self.job]
		errors = ''
		for i in jobs:
			if self.worker.DEBUG:
				self.worker.execute_job(i, headless=self.headless)
			else:
				try:
					self.worker.execute_job(i, headless=self.headless)
				except Exception as error:
					errors += str(error) + '\n'
		if errors!= '': 
			self.__error__(errors)
		sys_exit(0)
