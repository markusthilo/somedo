#!/usr/bin/env python3

from os import name as os_name
from os import path as os_path
from os import mkdir as os_mkdir
from os import getcwd
from datetime import datetime
from json import dump as jdump
from json import load as jload
from urllib.request import urlretrieve
from html2text import html2text

class Storage:
	'Save data into destination directory and subdirectories'

	def __init__(self):
		'Create object by making a destination directory if not exists'
		if os_name == 'nt':
			self.slash = '\\'# to build filepaths in windows
		else:
			self.slash = '/'# the real slash for real operating systems :-)
		self.rootdir = os_path.realpath(__file__).rsplit(self.slash, 2)[0]# set root directory of the application (one level up from here)
		self.outdir = getcwd() + self.slash + datetime.utcnow().strftime('%Y%m%d_SocialMedia')
		self.moddir = self.outdir# output directory

	def mkdir(self, path):
		'Make directory. Do nothing if already existent.'
		if self.dir_exists(path):
			return path
		try:
			os_mkdir(path)
		except:
			raise RuntimeError('Could not create directory %s.' % path)
		return path

	def file_exists(self, path):
		'Check if file exists and is a regular file'
		return os_path.isfile(path)

	def dir_exists(self, path):
		'Check if directory exists'
		return os_path.isdir(path)

	def json_dump(self, json, path):
		'Write JSON file'
		with open(path, 'w', encoding='utf-8') as f:
			jdump(json, f, ensure_ascii=False)

	def json_load(self, path):
		'Load JSON file'
		with open(path, 'r', encoding='utf-8') as f:
			return jload(f)

	def mkoutdir(self):
		'Make top level output directory'
		self.mkdir(self.outdir)

	def mkmoddir(self, module):
		'Make directory for a module such as Facebook'
		self.mkoutdir()
		self.moddir = self.mkdir(self.outdir + self.slash + module)

	def mksubdir(self, dirname):
		'Make subdirectory under module directory directory, e.g. for an account'
		return self.mkdir(self.moddir + self.slash + dirname)

	def modpath(self, *args):
		'Build file path. Arguments: filename (, subdir).'
		path = self.moddir	# 1 main directory for 1 session
		for i in args:
			if isinstance(i, str):
				path += self.slash + i
			elif isinstance(i, list) or isinstance(i, tuple):# also tke lists or tuples
				for j in i:
					path += self.slash + j
			else:
				raise RuntimeError('Only strings, lists or tuples work as arguments')
		return path.rstrip(self.slash)

	def write_str(self, *args):
		'Write string to file. Arguments: string, filename (, subdir). If no subdirectory is give, write to main directory'
		with open(self.modpath(args[1:]) , 'w', encoding='utf-8') as f:
			f.write(str(args[0]))	# write string

	def write_1d(self, *args):
		'Write (1-dimensional) list to CSV/TSV file (1 line, tab separated)'
		with open(self.modpath(args[1:]), 'w', encoding='utf-8') as f:
			line = ''
			for i in args[0]:	# write list as CSV/TSV (tab stop seperated fields)
				line += '"%s";' % str(i)
			f.write(line[:-1] + '\n')

	def write_2d(self, *args):
		'Write list of lists (2-dimensinal list) to CSV/TSV file'
		with open(self.modpath(args[1:]), 'w', encoding='utf-8') as f:
			for i in args[0]:
				line = ''
				for j in i:
					line += '"%s";' % str(j)
				f.write(line[:-1] + '\n')

	def write_dicts(self, *args):
		'Write dictionary or list of dictionaries to CSV/TSV file'
		with open(self.modpath(args[2:]), 'w', encoding='utf-8') as f:
			if isinstance(args[0], dict):
				ldicts = [args[0]]
			else:
				ldicts = args[0]
			for i in ldicts:
				line = ''
				for j in args[1]:
					line += '"%s";' % str(i[j])
				f.write(line[:-1] + '\n')

	def write_json(self, *args):
		'Write data to JSON file'
		with open(self.modpath(args[1:]), 'w', encoding='utf-8') as f:
			jdump(args[0], f, ensure_ascii=False)

	def write_text(self, *args):
		'Convert from html to text and write to file'
		with open(self.modpath(args[1:]), 'w', encoding='utf-8') as f:
			f.write(html2text(args[0]))

	def download(self, *args):
		'Download and writte file'
		urlretrieve(args[0], self.modpath(args[1:]))

	def url_cut_ext(self, url):
		'Cut file extension out of media URL'
		splitted = url.rsplit('/', 1)[-1].split('?', 1)[0].rsplit('.', 1)
		if len(splitted) == 1:
			return splitted[1]
		else:
			return ''
