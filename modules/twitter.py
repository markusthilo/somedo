#!/usr/bin/env python3

from re import search as rsearch
from re import sub as rsub
from re import sub as rfindall
from time import sleep
from datetime import datetime
from base.cutter import Cutter

class Twitter:
	'Downloader for Twitter'

	DEFINITION = ['Twitter',
		[],
		[
			[['User', True], ['Photos', False], ['Limit', 200]],
			[['Search', False], ['Photos', False], ['Limit', 200]]
		]
	]

	def __init__(self, target, options, login, chrome, storage):
		'Generate object for Twitter'
		self.chrome = chrome
		self.storage = storage
		self.ct = Cutter()
		if 'User' in options and not 'Search' in options:	# target userss / twitter user
			if 'Photos' in options['User']:
				self.photos = options['User']['Photos']
			else:
				self.photos = None
			self.limit = options['User']['Limit']
			self.rm_banner()
			for i in self.extract_targets(target):				
				self.get_account(i)
		elif not 'User' in options and 'Search' in options:	# twitter search
			if 'Photos' in options['Search']:
				self.photos = options['Search']['Photos']
			else:
				self.photos = None
			self.limit = options['Search']['Limit']
			self.get_search(target)
		elif 'User' in options and 'Search' in options:	# either account or search, not both
			raise Exception('Targetting a Twitter user does not work together with the Twitter search option.')
		else:
			raise Exception('Nothing to do an Twitter.')

	def extract_targets(self, target):
		'Extract paths (= URLs without ...instagram.com/) from given targets'
		l= []	# list for the target users (id or path)
		for i in target.split(';'):
			i = rsub('^.*twitter\.com/', '', i)
			i = rsub('\?.*$', '', i)
			i = i.lstrip(' ').rstrip(' ')
			if i != '':
				l.append(i)
		return l

	def rm_banner(self):
		'Remove redundant parts of the page'
		self.chrome.rm_outer_html('ClassName', 'topbar js-topbar')
		self.chrome.rm_outer_html('ClassName', 'topbar-spacer')
		self.chrome.rm_outer_html('ClassName', 'BannnersContainer')
		self.chrome.rm_outer_html('ClassName', 'MoveableModule')

	def rm_profile_canopy(self):
		'Remove general infos from profile'
		self.chrome.rm_outer_html('ClassName', 'ProfileCanopy ProfileCanopy--withNav ProfileCanopy--large js-variableHeightTopBar')
		self.chrome.rm_outer_html('ClassName', 'Grid-cell')

	def rm_search(self):
		'Remove search filters etc.'
		m = rsearch('<div class="Grid-cell [^"]+', self.chrome.get_inner_html_by_id('page-container'))
		self.chrome.rm_outer_html('ClassName', 'SearchNavigation')
		if m != None:
			self.chrome.set_outer_html('ClassName', m.group()[12:], 0, '')

	def get_tweets(self, path):
		'Get Tweets by scrolling down.'
		path_no_ext = self.storage.modpath(path, 'tweets')
		self.chrome.expand_page(path_no_ext=path_no_ext, limit=self.limit)
		self.chrome.page_pdf(path_no_ext)
		if self.photos:
			cnt = 1
			pinfo = []	# to store urls
			for html in self.chrome.get_outer_html('TagName', 'img'):	# get all embeded media
				if rsearch('class="avatar', html) == None and rsearch('class="Emoji', html) == None:
					url = self.ct.src(html)
					fname = 'photo_%05d%s' % (cnt, self.ct.ext(url))
					try:	# try to download photo
						self.storage.download(url, path, fname)
					except:
						continue
					cnt += 1
					pinfo.append({	# store counter, media type and url to media info list
						'file':	fname,
						'time':	datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
						'url':	url
					})
			if pinfo != []:
				self.storage.write_dicts(pinfo, ('file','time','url') , path, 'photos.csv')
				self.storage.write_json(pinfo, path, 'photos.json')

	def get_account(self, path):
		'Get tweets of an account / Twitter user'
		self.chrome.navigate('http://twitter.com/%s' % path)
		for i in range(3):
			sleep(1)
			if self.chrome.get_inner_html_by_id('timeline') != None:
				break
			if i == 2:
				raise Exception('Could not open Twitter Timeline.')
		self.rm_banner()
		self.storage.mksubdir(path)
		path_no_ext = self.storage.modpath(path, 'landing')
		self.chrome.page_pdf(path_no_ext)
		self.chrome.visible_page_png(path_no_ext)
		self.rm_profile_canopy()
		self.get_tweets(path)

	def get_search(self, target):
		'On Search the target is handled as Twitter search string'
		self.chrome.navigate('https://twitter.com/search?f=tweets&vertical=news&q=%s&src=typd' % target)
		for i in range(3):
			sleep(1)
			if self.chrome.get_inner_html_by_id('timeline') != None:
				break
			if i == 2:
				raise Exception('Could not open Twitter Search.')
		path = 'search_'	# handable directory name
		if len(target) > 23:
			path += target.replace(' ', '_')[:23]
		else:
			path += target.replace(' ', '_')
		self.rm_banner()
		self.rm_search()
		self.get_tweets(path)
