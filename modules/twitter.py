#!/usr/bin/env python3

from re import search as rsearch
from re import sub as rsub
from re import sub as rfindall
from time import sleep
from datetime import datetime
from base.cutter import Cutter
from base.logger import DEBUG

class Twitter:
	'Downloader for Twitter'

	DEFAULTPAGELIMIT = 20

	def __init__(self, job, storage, chrome, stop=None):
		'Generate object for Twitter'
		self.storage = storage
		self.chrome = chrome
		self.logger = self.storage.logger
		self.ct = Cutter()
		self.options = job['options']
		self.logger.debug('Twitter: options: %s' % self.options)
		self.chrome.open(stop=stop)
		if self.options['Search']:	# twitter search
			self.get_search(job['target'])
		else:	# target userss / twitter user
			for i in self.extract_targets(job['target']):				
				self.get_account(i)
		if self.logger.level < DEBUG:
			self.logger.visible('Twitter: finished, now sleeping for 5 seconds until closing browser')
			sleep(5)
		self.chrome.close()

	def extract_targets(self, target):
		'Extract paths (= URLs without ...instagram.com/) from given targets'
		l= []	# list for the target users (id or path)
		for i in self.ct.split(target):
			i = rsub('^.*twitter\.com/', '', i)
			i = rsub('\?.*$', '', i)
			if i != '':
				l.append(i)
		return l

	def rm_banner(self):
		'Remove redundant parts of the page'
		self.chrome.rm_outer_html('ClassName', 'topbar js-topbar')
		self.chrome.rm_outer_html('ClassName', 'topbar-spacer')
		self.chrome.rm_outer_html('ClassName', 'BannnersContainer')
		self.chrome.rm_outer_html('ClassName', 'Bannner eu-cookie-notice')
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
		self.logger.info('Twitter: data will be stored to: %s' % self.storage.modpath(path))
		path_no_ext = self.storage.modpath(path, 'tweets')
		self.chrome.expand_page(path_no_ext=path_no_ext, limit=self.options['limitPages'])
		self.chrome.page_pdf(path_no_ext)
		if self.options['Photos']:
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
		sleep(1)
		self.rm_banner()
		self.storage.mksubdir(path)
		path_no_ext = self.storage.modpath(path, 'account')
		self.chrome.visible_page_png(path_no_ext)	# save the tob of timeline as png
		self.chrome.page_pdf(path_no_ext)	# and as pdf
		self.rm_profile_canopy()
		self.get_tweets(path)

	def get_search(self, target):
		'On Search the target is handled as Twitter search string'
		self.chrome.navigate('https://twitter.com/search?f=tweets&vertical=news&q=%s&src=typd' % target)
		sleep(1)
		path = 'search_'	# handable directory name
		if len(target) > 23:
			path += target.replace(' ', '_')[:23]
		else:
			path += target.replace(' ', '_')
		self.rm_banner()
		self.rm_search()
		self.get_tweets(path)
