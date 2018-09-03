#!/usr/bin/env python3

import re, time

class Instagram:
	'Downloader for Instagram'

	DEFINITION = ['Instagram', [],	[] ]

	def __init__(self, target, options, login, chrome, storage, stop=None):
		'Generate object for Instagram'
		self.storage = storage
		self.chrome = chrome
		self.stop = stop
		for i in self.extract_targets(target):
			self.get_main(i)

	def extract_targets(self, target):
		'Extract paths (= URLs without ...instagram.com/) from given targets'
		l= []	# list for the target users (id or path)
		for i in target.split(';'):
			i = re.sub('^.*instagram\.com/', '', i)
			i = re.sub('/.*$', '', i)
			i = i.lstrip(' ').rstrip(' ')
			if i != '' and i != 'p':
				l.append(i)
		return l

	def extract_name(self):
		'Get information about given user out of targeted page'
		try:
			return re.findall('<h1 class="[^"]+" title="[^"]+"', self.chrome.get_outer_html('TagName', 'header')[0])[0].split('"')[3]
		except:
			return 'UNKNOWN'

	def rm_banner(self):
		'Remove redundant parts of the page'
		self.chrome.rm_outer_html('TagName', 'nav')
		self.chrome.rm_outer_html('TagName', 'footer')

	def get_main(self, path):
		'Scroll through page and get images'
		self.chrome.navigate('http:www.instagram.com/%s' % path)
		name = self.extract_name()	# get displayed name out of page header
		self.write_info(path, name)
		self.rm_banner()
		self.chrome.set_x_center()
		self.links = set()
		self.chrome.expand_page(	# scroll through page and take screenshots
			path_no_ext = self.storage.path('main', path),
			per_page_action = self.get_links
		)
		cnt = 0	# counter for the images
		for i in self.links:	# go through links
			print(i)
			self.chrome.navigate('http:www.instagram.com/%s' % i)
			time.sleep(0.2)
			self.rm_banner()
			cnt += 1
			self.chrome.visible_page_png(self.storage.path('image_%05d' % cnt, path))	# save image/page as png
			print(self.chrome.get_inner_html('TagName', 'article'))

	def get_links(self):
		'Extract links from tag "article"'
		for i in re.findall('<a href="/p/[^"]+', self.chrome.get_outer_html('TagName', 'article')[0]):	# go through links
			self.links.update({i[9:]})

	def write_info(self, path, name):
		'Write account information as CSV and JSON file'
		self.storage.write_1d([path, name, 'http://www.instagram.com/%s' % path], 'info.csv', path)
		self.storage.write_json({'path': path, 'name': name, 'link': 'http://www.instagram.com/%s' % path}, 'info.json', path)
