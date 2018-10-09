#!/usr/bin/env python3

import re, time, datetime

class Twitter:
	'Downloader for Twitter'

	DEFINITION = ['Twitter',
		['Email', 'Password'],
		[
			[['Landing', True]],
			[['Tweets', True], ['Search', False], ['Media', False], ['Limit', 100]]
		]
	]

	def __init__(self, target, options, login, chrome, storage):
		'Generate object for Twitter'
		self.options = options
		self.chrome = chrome
		self.storage = storage
		self.chrome.navigate('https://twitter.com/login')	# go to twitter login
		time.sleep(2)
		
		self.chrome.insert_element('Name', 'session[username_or_email]', 0, login['Email'])	# login with email
		self.chrome.insert_element('Name', 'session[password]', 0, login['Password'])	# and password
		self.chrome.click_element('ClassName', 'submit EdgeButton EdgeButton--primary EdgeButtom--medium', 0)	# click login
		
		if 'Landing' in options:
			self.landing = True
		elif not 'Tweets' in self.options:
			raise Exception('Nothing to do.')
		else:
			self.landing = False
		if self.landing or not self.options['Tweets']['search']:
			for i in self.extract_targets(target):				
				self.get_account(i)
		else:
			pass	# twitter search	


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
		self.chrome.rm_outer_html('ClassName', 'ProfileCanopy-inner')
		self.chrome.rm_outer_html('ClassName', 'Grid-cell')

	def get_account(self, path):
		'Get tweets of an account / twitter user'
		self.chrome.navigate('http://twitter.com/%s' % path)
		time.sleep(0.5)
		self.rm_banner()
		path_no_ext = self.storage.path('landing', path)
		if self.landing:
			self.chrome.page_pdf(path_no_ext)
			self.chrome.visible_page_png(path_no_ext)
		if not 'Tweets' in self.options:
			return
		self.rm_profile_canopy()
		self.chrome.set_x_center()
		return
		
		try:	# try to get header part of main page
			html = self.chrome.get_outer_html('TagName', 'header')[0]
		except:
			html = ''
		try:	# try to get displayed name out of page header
			name = re.findall('<h1 class="[^"]+" title="[^"]+"', html)[0].split('"')[3]
		except:
			name = 'UNKNOWN'
		self.storage.write_str('%s\t%s\thttp://www.instagram.com/%s' % (path, name, path), 'profile.csv', path)	# write information as file
		self.storage.write_json({'path': path, 'name': name, 'link': 'http://www.instagram.com/%s' % path}, 'profile.json', path)	# write as json file
		try:	# try to download profile picture
			url = re.findall(' src="[^"]+"', self.chrome.get_outer_html('TagName', 'img')[0])[0][6:-1]
			self.storage.download(url, 'profile' + self.cut_ext(url), path)	# download media file using the right file extension
		except:
			pass
		self.rm_banner()
		self.chrome.set_x_center()
		self.chrome.page_pdf(self.storage.path('main', path))
		self.links = []
		self.limit_reached = False
		self.chrome.drive_by_png(	# scroll through page and take screenshots
			path_no_ext = self.storage.path('main', path),
			per_page_action = self.get_links,
			terminator = self.terminator
		)
		minfo = []	# list for media info
		cnt = 0	# counter for the images/videos
		for i in self.links:	# go through links
			if self.chrome.stop_check():
				break
			self.chrome.navigate('http:www.instagram.com/%s' % i)
			time.sleep(0.2)
			self.rm_banner()
			cnt += 1
			store_path = self.storage.path('%05d_page' % cnt, path)
			self.chrome.visible_page_png(store_path)	# save page as png
			self.chrome.page_pdf(store_path)	# save as pdf
			self.storage.write_text(self.chrome.get_inner_html('TagName', 'article')[0], '%05d_page.txt' % cnt, path)	# write comments
			try:	# try to get video url
				url = re.findall(' src="[^"]+"', self.chrome.get_outer_html('TagName', 'video')[-1])[0][6:-1]
				fname = '%05d_video' % cnt
				if self.photosonly:
					continue
			except:
				try:	# try to get image url
					url = re.findall(' src="[^"]+"', self.chrome.get_outer_html('TagName', 'img')[-1])[0][6:-1]
					fname = '%05d_image' % cnt
				except:
					continue
			try:	# try to download media file
				fname += self.cut_ext(url)
				self.storage.download(url, fname, path)
				minfo.append({	# store counter, media type and url to media info list
					'file':	fname,
					'time':	datetime.datetime.utcnow().strftime('%Y-%-m-%d %H:%M:%S'),
					'url':	url
				})
			except:
				pass
		self.storage.write_dicts(minfo,('file','time','url') , 'media.csv', path)
		self.storage.write_json(minfo, 'media.json', path)

	def get_tweets(self):
		'Extract tweets'
		for i in self.chrome.get_outer_html('ClassName', 'content'):	# get all class="content"
			

	def terminator(self):
		'Test if limit of media to download is reached'
		if len(self.links) >= self.limit:
			return True
		return False

	def cut_ext(self, url):
		'Cut file extension out of media URL'
		try:
			ext = re.findall('\.[^.]+$', re.sub('\?.*$', '', url))[-1]
		except:
			ext = ''
		return ext
