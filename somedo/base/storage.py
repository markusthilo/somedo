#!/usr/bin/env python3

import os, json, re, urllib.request, html2text

class Storage:
	'Save data into destination directory and subdirectories'

	def __init__(self, root_dir, platform):
		'Create object by making a destination directory if not exists'
		if os.name == 'nt':
			self.slash = '\\'	# to build filepaths in windows
		else:
			self.slash = '/'	# the real slash for real operating systems :-)
		try:
			self.root_dir = self.__mkdir__(root_dir)
		except:
			raise RuntimeError('Could not create root directory %s' % root_dir)
		try:
			self.main_dir = self.__mkdir__(self.root_dir + platform + self.slash)
		except:
			raise RuntimeError('Could not create main directory for %s' % platform)	

	def __mkdir__(self, path):
		'Make directory. Do nothing if already existent.'
		path = path.rstrip(self.slash)
		try:
			os.mkdir(path)
		except:
			if not os.path.isdir(path):
				raise RuntimeError('Could not create %s.' % path)
		return path + self.slash	# directory path ends with /

	def mkdir(self, *args):
		'Make subdirectory under main directory. This should mostly be used for an account'
		if len(args) == 0:
			subdir = ''
		elif len(args) == 1:
			subdir = args[0]
		else:
			raise RuntimeError('None or 1 argument (subdirectory) are possible.')
		self.__mkdir__( ( self.main_dir + subdir ).rstrip(self.slash) + self.slash)

	def path(self, *args):
		'Build file path. Arguments: filename (, subdir).'
		path = self.main_dir	# 1 main directory for 1 session
		if len(args) == 1:	# handle 1 give list or up to 2 arguments
			if isinstance(args[0], str):
				path += args[0]
			elif isinstance(args[0], list) or isinstance(args[0], tuple):
				if len(args[0]) == 1:
					path += args[0][0]
				elif len(args[0]) == 2:
					self.__mkdir__(path + args[0][1])
					path += args[0][1].rstrip(self.slash) + self.slash + args[0][0]
				else:
					raise RuntimeError('1 or 2 string arguments (filename or filename, subdir) are needed. They can be in a list.')
		elif len(args) == 2:
			self.__mkdir__(path + args[1])
			path += args[1].rstrip(self.slash) + self.slash + args[0]
		else:
			raise RuntimeError('1 or 2 string arguments (filename or filename, subdir) are needed.')
		return path

	def write_str(self, *args):
		'Write string to file. Arguments: string, filename (, subdir). If no subdirectory is give, write to main directory'
		with open(self.path(args[1:]) , 'w', encoding='utf-8') as f:
			f.write(str(args[0]))	# write string

	def write_1d(self, *args):
		'Write (1-dimensional) list to CSV/TSV file (1 line, tab separated)'
		with open(self.path(args[1:]), 'w', encoding='utf-8') as f:
			line = ''
			for i in args[0]:	# write list as CSV/TSV (tab stop seperated fields)
				line += str(i) + '\t'
			f.write(line.rstrip('\t') + '\n')

	def write_2d(self, *args):
		'Write list of lists (2-dimensinal list) to CSV/TSV file'
		with open(self.path(args[1:]), 'w', encoding='utf-8') as f:
			for i in args[0]:
				line = ''
				for j in i:
					line += str(j) + '\t'
				f.write(line.rstrip('\t') + '\n')

	def write_dicts(self, *args):
		'Write dictionary or list of dictionaries to CSV/TSV file'
		with open(self.path(args[2:]), 'w', encoding='utf-8') as f:
			if isinstance(args[0], dict):
				ldicts = [args[0]]
			else:
				ldicts = args[0]
			for i in ldicts:
				line = ''
				for j in args[1]:
					line += str(i[j]) + '\t'
				f.write(line.rstrip('\t') + '\n')

	def write_json(self, *args):
		'Write data to JSON file'
		with open(self.path(args[1:]), 'w', encoding='utf-8') as f:
			json.dump(args[0], f, ensure_ascii=False)

	def write_text(self, *args):
		'Convert from html to text and write to file - very basic conversion but should work for the task here'
		with open(self.path(args[1:]), 'w', encoding='utf-8') as f:
			f.write(html2text.html2text(args[0]))

	def download(self, *args):
		'Download and writte file'
		urllib.request.urlretrieve(args[0], self.path(args[1:]))

	def url_cut_ext(self, url):
		'Cut file extension out of media URL'
		try:
			ext = re.findall('\.[^.]+$', re.sub('\?.*$', '', url))[-1]
		except:
			ext = ''
		return ext
