#!/usr/bin/env python3

import re

class Instagram:
	'Downloader for Instagram'

	DEFINITION = [
		'Instagram',
		[],
		[
			[['Landing', True]]
		]
	]

	def __init__(self, target, login, chrome, storage, stop=False):
		'Generate object for Instagram'
		self.storage = storage
		self.chrome = chrome
		self.stop = stop
		for i in self.extract_targets(target):
			if 'Landing' in options:
				self.get_landing(i)

	def extract_targets(self, target):
		'Extract usernames from urls'
		l= []	# list for the target users (id or path)
		for i in target.split(';'):
			i = re.sub('^.*instagram.com/', '', i)	# cut out id or path if url is given
			i = re.sub('[?%&/"].*$', '', i)
			i = i.lstrip(' ').rstrip(' ')
			if i != '':
				l.append(i)
		return l

	def get_landing(self, user):
		'Get landing page of Instagramm account'
		self.chrome.navigate('https://www.instagram.com/%s' % user)
		name = self.extract_name()	# get displayed name out of side header
		self.write_account(user, name)	# save user name, name and link
		self.chrome.expand_page(path_no_ext = self.storage.path('landing', user))	# scroll through page and take screenshots

	def extract_name(self):
		'Get information about given user out of targeted page'
		try:
			header = self.driver.find_element('class', '_mainc ')	# extract header part of the page
			html = header.get_attribute("outerHTML")
			return re.findall('<h1 class="[^>]*>[^<]*', self.chrome.get_outer_html('ClassName', '_mainc ')[0])[1].split('>')[1]
		except:
			return 'UNKNOWN'

	def write_account(self, user, name):
		'Write account information as CSV and JSON file'
		self.storage.write_1d([user, name, 'https://www.instagram.com/%s/' % user], 'account.csv', user)
		self.storage.write_json({'user': user, 'name': name, 'link': 'https://www.instagram.com/%s/' % user}, 'account.json', user)
