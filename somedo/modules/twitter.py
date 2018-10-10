#!/usr/bin/env python3

import re, time, datetime

class Twitter:
	'Downloader for Twitter'

	DEFINITION = ['Twitter',
###		['Email', 'Password'],	###
		[],
		[
			[['Landing', True]],
			[['Tweets', True], ['Search', False], ['Photos', False], ['Limit', 200]]
		]
	]

	def __init__(self, target, options, login, chrome, storage):
		'Generate object for Twitter'
		self.landing = False
		self.tweets = False
		self.photos = False
		search = False
		if 'Landing' in options:
			self.landing = True
		if 'Tweets' in options:
			self.tweets = True
			self.limit = options['Tweets']['Limit']
			if 'Search' in options['Tweets']:
				search = True
			if 'Photos' in options['Tweets']:
				self.photos = True
		elif not self.landing:
			raise Exception('Nothing to do.')
		self.chrome = chrome
		self.storage = storage
###		if login['Email'] != '':	# go to twitter login if email is given
###			self.chrome.navigate('https://twitter.com/login')	# go to twitter login
###			time.sleep(1)
###			self.chrome.insert_element('Name', 'session[username_or_email]', 0, login['Email'])	# login with email
###			self.chrome.insert_element('Name', 'session[password]', 0, login['Password'])	# and password
###			self.chrome.click_element('ClassName', 'submit EdgeButton EdgeButton--primary EdgeButtom--medium', 0)	# click login
		if search:
			raise Exception('Twitter search is not implemented.')
		for i in self.extract_targets(target):				
			self.get_account(i)

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
		self.chrome.rm_outer_html('ClassName', 'MoveableModule')

	def rm_profile_canopy(self):
		'Remove general infos from profile'
		self.chrome.rm_outer_html('ClassName', 'ProfileCanopy ProfileCanopy--withNav ProfileCanopy--large js-variableHeightTopBar')
		self.chrome.rm_outer_html('ClassName', 'Grid-cell')

	def rm_tweetstuff(self):
		'Remove background from  tweet'
		self.chrome.rm_outer_html_by_id('doc')
		self.chrome.rm_outer_html('ClassName', 'inline-reply-tweetbox-container')
		self.chrome.rm_outer_html('ClassName', 'module Trends trends Trends--wide')
		self.chrome.rm_outer_html('ClassName', 'Footer module roaming-module Footer--slim')
		self.chrome.rm_outer_html('ClassName', 'permalink-footer')

	def get_account(self, path):
		'Get tweets of an account / twitter user'
		self.chrome.navigate('http://twitter.com/%s' % path)
		time.sleep(0.5)
		self.rm_banner()
		path_no_ext = self.storage.path('landing', path)
		if self.landing:
			self.chrome.page_pdf(path_no_ext)
			self.chrome.visible_page_png(path_no_ext)
		if self.tweets:
			self.rm_profile_canopy()
			path_no_ext = self.storage.path('tweets', path)
			self.chrome.expand_page(path_no_ext=path_no_ext, limit=self.limit)
			self.chrome.page_pdf(path_no_ext)
			self.get_tweets(path)

	def get_tweets(self, path):
		'Extract tweets'
		tweet_cnt = 1
		minfo = []
		for html in self.chrome.get_outer_html('ClassName', 'content'):	# get all class="content"
			if self.chrome.stop_check():
				break
			tweet_url = 'https://twitter.com' + re.findall('<a href="[^"]+" class="tweet-timestamp js-permalink js-nav js-tooltip"', html)[0][9:-56]
			self.chrome.navigate(tweet_url)
			self.rm_tweetstuff()
			text = tweet_url + '<br><br>' + self.chrome.get_inner_html('ClassName', 'js-tweet-text-container')[0]
###			for html in self.chrome.get_outer_html('ClassName', 'content'):	# get all class="content"
###				text += '<br><br>%s' % html
			self.storage.write_text(text, 'tweet_%05d.txt' % tweet_cnt, path)
			path_no_ext = self.storage.path('tweet_%05d' % tweet_cnt, path)
			self.chrome.visible_page_png(path_no_ext)
			self.chrome.page_pdf(path_no_ext)
			if self.photos:
				try:
					html = self.chrome.get_outer_html('ClassName', 'AdaptiveMedia-container')[0]
				except:
					continue
				m = re.search(' class="AdaptiveMedia[^"]*Photo"', html)
				if m != None:
					photo_cnt = 1
					photo_urls = [ i[6:] for i in re.findall(' src="[^"]+', html) ]
					for photo_url in photo_urls:
						if len(photo_urls) == 1:
							fname = 'photo_%05d%s' % (tweet_cnt, self.storage.url_cut_ext(photo_url))
						else:
							fname = 'photo_%05d_%05d%s' % (tweet_cnt, photo_cnt, self.storage.url_cut_ext(photo_url))
						try:	# try to download photo
							self.storage.download(photo_url, fname, path)
							minfo.append({	# store counter, media type and urls to media info list
								'file': fname,
								'time': datetime.datetime.utcnow().strftime('%Y-%-m-%d %H:%M:%S'),
								'photo_url': photo_url,
								'tweet_url': tweet_url
							})
							photo_cnt += 1
						except:
							pass
			tweet_cnt += 1
		if minfo != []:
			self.storage.write_dicts(minfo,('file','time','photo_url','tweet_url') , 'media.csv', path)
			self.storage.write_json(minfo, 'media.json', path)
