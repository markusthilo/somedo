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
from shutil import copytree

class Storage:
	'Save data into destination directory and subdirectories'

	def __init__(self):
		'Create object by making a destination directory if not exists'
		self.workdir = getcwd()
		if os_name == 'nt':
			self.slash = '\\'	# to build filepaths in windows
			self.rootdir = self.workdir	# working directory as root on windows
		else:
			self.slash = '/'	# the real slash for real operating systems :-)
			self.rootdir = os_path.realpath(__file__).rsplit(self.slash, 2)[0]	# set root directory of the application (one level up from here)
		self.icondir = self.rootdir + self.slash + 'icons'
		self.outdir = self.workdir + self.slash + self.today() + '_SocialMedia'
		self.moddir = self.outdir	# output directory

	def today(self):
		'Give date of today as string'
		return datetime.utcnow().strftime('%Y-%m-%d')

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

	def genpath(self, path, *args):
		'Generate file path from base directory, subdirectory/subdirectories and probalbly filename'
		for i in args:
			if isinstance(i, str):
				path += self.slash + i
			elif isinstance(i, list) or isinstance(i, tuple):	# also take lists or tuples
				for j in i:
					path += self.slash + j
			else:
				raise RuntimeError('Only strings, lists or tuples work as arguments')
		return path.rstrip(self.slash)

	def rootpath(self, *args):
		'Build file path under root directory'
		return self.genpath(self.rootdir, *args)

	def modpath(self, *args):
		'Build file path under module directory (e.g. Facebook/)'
		return self.genpath(self.moddir, *args)

	def read_static(self, *args):
		'Read file as string from root directory or static subdirectory (e.g. vis/)'
		with open(self.rootpath(*args), 'r', encoding='utf-8') as f:
			return f.read()

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

	def cptree2moddir(self, *args):
		'Copy recursivly from root or static subdirectory to module directory'
		sourcepath = self.rootpath(*args)
		sourcedir = sourcepath.rsplit(self.slash, 1)[1]
		copytree(sourcepath, self.moddir + self.slash + sourcedir)

	def write_str(self, string, *args):
		'Write string to file from main or subdirectory'
		with open(self.modpath(*args), 'w', encoding='utf-8') as f:
			f.write(str(string))	# write string

	def read_str(self, *args):
		'Read file as string from main or subdirecoty'
		with open(modpath(*args), 'r', encoding='utf-8') as f:
			return f.read()

	def write_xml(self, string, *args):
		'Write string to file while encoding UTF8 to HTML'
		with open(self.modpath(*args), 'wb') as f:
			f.write(string.encode('ascii', 'xmlcharrefreplace'))

	def write_1d(self, lst1d, *args):
		'Write (1-dimensional) list to CSV/TSV file (1 line, tab separated)'
		with open(self.modpath(*args), 'w', encoding='utf-8') as f:
			line = ''
			for i in lst1d:	# write list as CSV/TSV (tab stop seperated fields)
				line += '"%s";' % str(i)
			f.write(line[:-1] + '\n')

	def write_2d(self, lst2d, *args):
		'Write list of lists (2-dimensinal list) to CSV/TSV file'
		with open(self.modpath(*args), 'w', encoding='utf-8') as f:
			for i in lst2d:
				line = ''
				for j in i:
					line += '"%s";' % str(j)
				f.write(line[:-1] + '\n')

	def write_dicts(self, dictionary, index, *args):
		'Write dictionary or list of dictionaries to CSV/TSV file'
		with open(self.modpath(*args), 'w', encoding='utf-8') as f:
			if isinstance(dictionary, dict):
				ldicts = [dictionary]
			else:
				ldicts = dictionary
			for i in ldicts:
				line = ''
				for j in index:
					line += '"%s";' % str(i[j])
				f.write(line[:-1] + '\n')

	def write_json(self, json, *args):
		'Write data to JSON file'
		self.json_dump(json, self.modpath(*args))

	def write_text(self, string, *args):
		'Convert from html to text and write to file'
		with open(self.modpath(*args), 'w', encoding='utf-8') as f:
			f.write(html2text(string))

	def download(self, url, *args):
		'Download and writte file'
		urlretrieve(url, self.modpath(*args))
