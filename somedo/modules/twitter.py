#!/usr/bin/env python3

import re, time, datetime

class Twitter:
	'Downloader for Twitter'

	DEFINITION = ['Twitter',
		[],
		[
			[['User', True], ['Photos', False], ['Limit', 20]],
			[['Search', False], ['Photos', False], ['Limit', 20]]
		]
	]

	def __init__(self, target, options, login, chrome, storage):
		'Generate object for Twitter'
		self.chrome = chrome
		self.storage = storage
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
			i = re.sub('^.*twitter\.com/', '', i)
			i = re.sub('\?.*$', '', i)
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
		m = re.search('<div class="Grid-cell [^"]+', self.chrome.get_inner_html_by_id('page-container'))
		self.chrome.rm_outer_html('ClassName', 'SearchNavigation')
		if m != None:
			self.chrome.set_outer_html('ClassName', m.group()[12:], 0, '')

	def get_tweets(self, path):
		'Get Tweets by scrolling down.'
		path_no_ext = self.storage.path('tweets', path)
		self.chrome.expand_page(path_no_ext=path_no_ext, limit=self.limit)
		self.chrome.page_pdf(path_no_ext)
		if self.photos:
			cnt = 1
			pinfo = []	# to store urls
			for html in self.chrome.get_outer_html('ClassName', 'AdaptiveMediaOuterContainer'):	# get all embeded media
				if re.search(' class="AdaptiveMedia[^"]*Photo"', html) == None:	# check for photos
					continue
				photo_urls = [ i[6:] for i in re.findall(' src="[^"]+', html) ]	# get the urls
				for url in photo_urls:
					fname = 'photo_%05d%s' % (cnt, self.storage.url_cut_ext(url))
					try:	# try to download photo
						self.storage.download(url, fname, path)
					except:
						continue
					cnt += 1
					pinfo.append({	# store counter, media type and url to media info list
						'file':	fname,
						'time':	datetime.datetime.utcnow().strftime('%Y-%-m-%d %H:%M:%S'),
						'url':	url
					})
			if pinfo != []:
				self.storage.write_dicts(pinfo,('file','time','url') , 'photos.csv', path)
				self.storage.write_json(pinfo, 'photos.json', path)

	def get_account(self, path):
		'Get tweets of an account / Twitter user'
		self.chrome.navigate('http://twitter.com/%s' % path)
		for i in range(3):
			time.sleep(1)
			if self.chrome.get_inner_html_by_id('timeline') != None:
				break
			if i == 2:
				raise Exception('Could not open Twitter Timeline.')
		self.rm_banner()
		path_no_ext = self.storage.path('landing', path)
		self.chrome.page_pdf(path_no_ext)
		self.chrome.visible_page_png(path_no_ext)
		self.rm_profile_canopy()
		self.get_tweets(path)

	def get_search(self, target):
		'On Search the target is handled as Twitter search string'
		self.chrome.navigate('https://twitter.com/search?f=tweets&vertical=news&q=%s&src=typd' % target)
		for i in range(3):
			time.sleep(1)
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
