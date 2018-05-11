#!/usr/bin/env python3

import re, datetime, time

class Facebook:
	'Downloader for Facebook'

	DEFINITION = [
		'Facebook',
		['Email', 'Password'],
		[
			[['Landing', False]],
			[['Timeline', True], ['Expand', False], ['Translate', False], ['Visitors', False], ['Until', '1970-01-01']],
			[['Posts', False], ['Expand', False], ['Translate', False], ['Visitors', False], ['Until', '1970-01-01']],
			[['About', False]],
			[['Photos', False]],
			[['Friends', False]],
			[['Network', False], ['Depth', 1]]
		]
	]

	ACCOUNT = ['id', 'name', 'path', 'link']

	def __init__(self, target, options, login, chrome, storage, stop=False):
		'Generate object for Facebook by giving the needed parameters'
		self.storage = storage
		self.chrome = chrome
		self.stop = stop
		targets = self.extract_users(target)
		errors = ''
		try:
			self.chrome.navigate('https://www.facebook.com/login')	# go to facebook login
			time.sleep(2)
			self.chrome.insert_element_by_id('email', login['Email'])	# login with email
			self.chrome.insert_element_by_id('pass', login['Password'])	# and password
			self.chrome.click_element_by_id('loginbutton')	# click login
		except:
			raise Exception('Could not login to Facebook.')
		time.sleep(2)
		if 'Network' in options:
			try:
				self.get_network(targets, options['Network']['Depth'])
			except:
				errors += ' Network,'
		for i in targets:
			get_account = True	# to check if info from cover had already been extracted
			if self.chrome.stop_check():
				break
			if 'Landing' in options:
				try:
					self.get_landing(i, get_account=get_account)
					get_account = False
				except:
					errors += ' %s/Landing,' % i
			if self.chrome.stop_check():
				break
			if 'Timeline' in options:
#				try:
				self.stop_utc = self.get_utc(options['Timeline']['Until'])
				self.get_timeline(
					i,
					expand = 'Expand' in options['Timeline'] and options['Timeline']['Expand'],
					translate = 'Translate' in options['Timeline'] and options['Timeline']['Translate'],
					visitors = 'Visitors' in options['Timeline'] and options['Timeline']['Visitors'],
					get_account = get_account
				)
				get_account = False
#				except:
#					errors += ' %s/Timeline,' % i
			if self.chrome.stop_check():
				break
			if 'Posts' in options:
				try:
					self.stop_utc = self.get_utc(options['Posts']['Until'])
					self.get_posts(
						i,
					expand = 'Expand' in options['Posts'] and options['Posts']['Expand'],
					translate = 'Translate' in options['Posts'] and options['Posts']['Translate'],
					visitors = 'Visitors' in options['Posts'] and options['Posts']['Visitors'],
						get_account = get_account
					)
					get_account = False
				except:
					errors += ' %s/Posts,' % i
			if self.chrome.stop_check():
				break
			if 'About' in options:
				try:
					self.get_about(i, get_account = get_account)
					get_account = False
				except:
					errors += ' %s/About,' % i
			if self.chrome.stop_check():
				break
			if 'Photos' in options:
				try:
					self.get_photos(i, get_account = get_account)
					get_account = False
				except:
					errors += ' %s/Photos,' % i
			if self.chrome.stop_check():
				break
			if 'Friends' in options and not 'Network' in options:	# friend list download is included in network option
				try:
					self.get_friends(i, get_account = get_account)
					get_account = False
				except:
					errors += ' %s/Friends,' % i
		if errors != '':
			raise Exception('The following Facebook accont(s)/action(s) returned errors: %s' % errors.rstrip(','))

	def extract_users(self, target):
		'Extract facebook id or path from url'
		l= []	# list for the target users (id or path)
		for i in target.split(';'):
			i = re.sub('^.*facebook.com/', '', i)	# cut out id or path if url is given
			i = re.sub('^profile\.php\?id=', '', i)
			if i[:3] == 'pg/':
				i = i[3:]
			i = re.sub('[?%&/"].*$', '', i)
			i = i.lstrip(' ').rstrip(' ')
			if i != '':
				l.append(i)
		return l

	def get_fid(self, flink):
		'Extract facebook id using regex'
		m = re.search('\.php\?id=[0-9]+', flink)	# get id
		if m == None:
			return ''
		return m.group()[8:]

	def get_name(self, flink):
		'Extract name of a facebook link using regex'
		m = re.search('">[^<]+</a>', flink)	# cut out name
		if m == None:
			return ''
		return m.group()[2:-4]

	def get_path(self, flink):
		'Extract path of a facebook link using regex'
		m = re.search('href="https://www\.facebook\.com/[^?/"]+.', flink)	# cut out from href
		if m == None:
			return ''
		if m.group()[31:] == 'profile.php?':	# regular profile id only
			m = re.search('href="https://www\.facebook\.com/profile\.php\?id=[0-9]+', flink)	# cut out more to get profile.php?id=100...
			if m == None:	# just in case...
				return ''
			return m.group()[31:]
		if m.group()[31:] == 'pages/':	# facebook pages like places etc.
			m = re.search('href="https://www\.facebook\.com/pages/[^/]+', flink)	# cut out more to get profile.php?id=100...
			if m == None:	# just in case...
				return ''
			return m.group()[37:]
		if m.group()[-1] == '?':	# regular profile with facebook user name as path
			return m.group()[31:-1]
		return ''

	def get_flink(self, flink):
		'Extract facebook link using regex'
		m = re.search('href="https://www\.facebook\.com/profile\.php\?id=[0-9]+', flink)	# get link on url: ...?id=100...
		if m != None:
			return m.group()[6:]
		m = re.search('href="https://www\.facebook\.com/pages/[^/"?]+', flink)	# get link on url: .../pages/...
		if m != None:
			return m.group()[6:]
		m = re.search('href="https://www\.facebook\.com/[^/"?]+', flink)	# get link on url: .../path?...
		if m != None:
			return m.group()[6:]
		return ''

	def get_user(self, flink):
		'Get complete user information out of link'
		fid = self.get_fid(flink)	# get id
		if fid == '':
			return None
		name = self.get_name(flink)	# get name
		if name == '':
			return None
		path = self.get_path(flink)	# get path
		if path == '':
			return None
		flink = self.get_flink(flink)	# get link
		if flink == '':
			return None
		return {'id': fid, 'name': name, 'path': path, 'link': flink}

	def extract_coverinfo(self, user):
		'Get information about given user (id or path) out of targeted profile cover'
		if re.sub('[0-9]+', '', user) == '':
			account = {'id': user, 'name': '', 'path': '', 'link': 'https://www.facebook.com/profile.php?id=%s' % user}
		else:
			account = {'id': '', 'name': '', 'path': user, 'link': 'https://www.facebook.com/%s' % user}
		try:	# try to get id, name and path of given user
			html = self.chrome.get_outer_html_by_id('fbProfileCover')
		except:	# no 'normal' user account
			try:	# try for /pg/-account
				html = self.chrome.get_outer_html_by_id('entity_sidebar')
			except:
				account['link'] = 'undetected'
				if account['id'] == '':
					account['id'] == 'undetected for %s' % user
				return account
			try:
				m = re.search('href="/[0-9]+/photos/', html)
				fid = m.group()[7:-8]
			except:
				fid = ''
			else:
				account['id'] = fid
		else:
			try:
				m = re.search('referrer_profile_id=[0-9]+', html)
				fid = m.group()[20:]
			except:
				fid = ''
		if fid != '':
			account['id'] = fid
		try:
			m = re.search('href="https://www\.facebook\.com/[^"]+">[^<]+<', html)
			path = m.group()[31:].split('"')[0].rstrip('/')	# cut out path
		except:
			pass
		else:
			if path != '':
				account['path'] = path
		try:
			name = m.group().split('>')[1].split('<')[0].rstrip(' ')	# cut out diplayed name
		except:
			pass
		else:
			if name != '':
				account['name'] = name
		return account	# return dictionary

	def rm_pagelets(self):
		'Remove bluebar and unwanted pagelets'
		self.chrome.set_outer_html_by_id('pagelet_bluebar', '')
		self.chrome.set_outer_html_by_id('pagelet_sidebar', '')
		self.chrome.set_outer_html_by_id('pagelet_dock', '')

	def get_utc(self, date_str):
		'Convert date given as string (e.g. "2018-02-01") to utc as seconds since 01.01.1970'
		l = date_str.split('-')
		try:
			return int(datetime.datetime(int(l[0]),int(l[1]),int(l[2]),0,0).timestamp())
		except ValueError:
			return 0

	def terminator(self):
		'Check date of posts to abort'
		if self.stop_utc <= 0:
			return False
		try:
			for i in self.driver.find_elements('tag', 'abbr'):
				m = re.search('.* data-utime=".* class="timestampContent">.*', i.get_attribute("outerHTML"))
				if int(re.sub('.*data-utime="', '', m.group()).split('"')[0]) <= self.stop_utc:
					return True
		except:
			pass
		return False

	def get_landing(self, user, get_account=True):
		'Get screenshot from start page (=unscrolled Timeline) about given user (id or path)'
		self.chrome.navigate('https://www.facebook.com/%s' % user)	# go to landing page of the given faebook account
		if get_account:
			account = self.extract_coverinfo(user)	# get facebook id, path/url and name
		self.write_account(account)	# save id, name etc. as csv and json
		self.rm_pagelets()	# remove bluebar etc.
		self.chrome.visible_page_png(self.storage.path('landing', account['id']))	# save the visible part of the page as png
		self.chrome.page_pdf(path)

	def get_timeline(self, user, expand=False, translate=False, visitors=False, get_account=True):
		'Get timeline'
		self.chrome.navigate('https://www.facebook.com/%s' % user)	# go to timeline
		if get_account:
			account = self.extract_coverinfo(user)	# get facebook id, path/url and name
		self.write_account(account)	# save id, name etc. as csv and json
		self.rm_pagelets()	# remove bluebar etc.
		self.chrome.set_outer_html_by_id('pagelet_escape_hatch', '')	# remove "Do you know ...?"
		self.chrome.set_outer_html_by_id('timeline_sticky_header_container', '')	# some other redundant bar
		clicks = []
		if expand:	# clicks to expand page
			clicks.extend([
				['ClassName', 'see_more_link'],
				['ClassName', 'UFIPagerLink'],
				['ClassName', 'UFICommentLink']
			])
		if translate:	# show translations if is in options
			clicks.extend([
				['ClassName', 'UFITranslateLink']
			])
		path = self.storage.path('timeline', account['id'])
		self.chrome.expand_page(
			click_elements_by = clicks,
			path_no_ext = path,
			terminator=self.terminator
		)
		self.chrome.page_pdf(path)
		if visitors:
			self.get_visitors(account)

	def get_visitors(self, account):
		'Get all visitors who left comments or likes etc. in timeline - timeline has to be open end expand'
		visitors = []	# list to store links to other profiles
		visitor_ids = {account['id']}	# create set to store facebook ids of visitors to get uniq visitors
		timeline = self.chrome.get_outer_html_by_id('recent_capsule_container')	# get timeline
		for i in re.findall('<a [^<]+</a>', timeline):	# look for links
			u = self.get_user(i)	# extract information from link
			if u != None and not u['id'] in visitor_ids:	# uniq
				visitors.append(u)
				visitor_ids.add(u['id'])
		for i in re.findall('href="/ufi/reaction/[^"]+"', timeline):	# look for links to reactions
			if self.chrome.stop_check():
				return
			self.chrome_navigate('https://www.facebook.com' + i[6:-1])	# open reaction page
			self.driver.expand_page()	# scroll through page
			reactions = self.chrome.get_outer_html('ClassName', 'uiList _4kg')	# extract reactions as list
			if len(reactions) > 0:
				for j in re.findall('<a [^<]+</a>', reactions):	# get links
					u = self.get_user(j)	# extract information from link
					if u != None and not u['id'] in visitor_ids:	# uniq
						visitors.append(u)
						visitor_ids.add(u['id'])
		self.storage.write_2d([ [ i[j] for j in self.ACCOUNT ] for i in visitors ], 'visitors.csv', account['id'])
		self.storage.write_json(visitors, 'visitors.json', account['id'])

	def get_posts(self, user, expand=False, translate=False, visitors=False):
		'Get posts on a bussines page'
		self.driver.get('https://www.facebook.com/pg/%s/posts/' % user)	# go to posts
		account = self.extract_coverinfo(user)	# get facebook id, path/url and name
		self.write_account(account)	# save id, name etc. as csv and json
		selectors = []	# selectors for selenium to interact with facebook page
		if expand:
			selectors.extend([
				['class', 'see_more_link'],
				['class', 'UFIPagerLink'],
				['class', 'UFICommentLink']
			])
		if translate:	# show translations if is in options
			selectors.append(['class', 'UFITranslateLink'])
		if expand or translate:
			self.driver.expand_page(selectors)
			self.driver.save_entire_png(self.storage.path('posts', account['id']))
		else:
			self.driver.scroll_save_png(self.storage.path('posts', account['id']))
		if visitors:
			self.get_visitors(account)

	def get_about(self, user):
		'Get About'
		self.driver.get('https://www.facebook.com/%s/about' % user)	# go to about
		account = self.extract_coverinfo(user)	# get facebook id, path/url and name
		self.write_account(account)
		self.driver.scroll_save_png(self.storage.path('about', account['id']))

	def get_photos(self, user):
		'Get photos of given user (id or path) and take screenshots'
		self.driver.get('https://www.facebook.com/%s/photos_albums' % user)
		account = self.extract_coverinfo(user)	# get facebook id, path/url and name
		self.write_account(account)	# save id, name etc. as csv and json
		album_cnt = 1	# to number screenshots
		try:
			albums = self.driver.find_element('id', 'pagelet_timeline_medley_photos')
		except:	# /pg/-account
			self.driver.get('https://www.facebook.com/pg/%s/photos' % user)
			try:
				albums = self.driver.find_id('id', 'content_container')
			except:
				self.driver.scroll_save_png(self.storage.path('photos', account['id']))
				return
		self.driver.scroll_save_png(self.storage.path('albums', account['id']))	
		try:
			for i in re.findall('"https://www\.facebook\.com/media/set/\?[^"]*"', albums.get_attribute("outerHTML")):
				self.driver.get(i.strip('"'))
				self.driver.scroll_save_png(self.storage.path('album_%04d_page_' % album_cnt, account['id']))
				album_cnt += 1
				photo_cnt = 1	# to number screenshots
				photos = self.driver.find_element('id', 'pagelet_timeline_medley_photos')
				try:
					for j in re.findall('"https://www\.facebook\.com/photo\.php?[^"]*"', photos.get_attribute("outerHTML")):
						self.driver.get(j.strip('"'))
						self.driver.save_visible_png(self.storage.path('album_%04d_photo_%04d' % (album_cnt, photo_cnt), account['id']))	# save page as png
						photo_cnt += 1
						self.driver.go_back()
				except:
					pass
				self.driver.go_back()
		except:
			pass

	def get_friends(self, user, get_account=True):
		'Get friends list from given user (id or path)'
		flist = []	# list to store friends
		self.chrome.navigate('https://www.facebook.com/%s/friends' % user)
		if getaccount:
			account = self.extract_coverinfo(user)	# get facebook id, path/url and name
		self.write_account(account)	# save id, name etc. as csv and json
		self.driver.scroll_save_png(self.storage.path('friends', account['id']))	
		try:	# try to get friends
			friends = self.driver.find_element('id', 'pagelet_timeline_medley_friends')
			html = friends.get_attribute("outerHTML")
		except:
			return (account, flist)	# return empty list if no visible friends
		for i in re.findall('<a href=\"[^?]*\?[^"]+\" [^<]*<\/a>', html):	# regex vs facebook
			u = self.get_user(i)	# get link
			if u != None:	
				flist.append(u)	# append to friend list if info was extracted
		self.storage.write_2d([ [ i[j] for j in i] for i in flist ], 'friends.csv', account['id'])
		self.storage.write_json(flist, 'friends.json', account['id'])
		return (account, flist)	# return account and friends as list

	def get_network(self, targets, depth):
		'Get friends and friends of friends and so on to given depth or abort if limit is reached'
		network = dict()	# dictionary to store ids: {target-id: {friend-id, ...}, ...}
		for i in targets:	# start with the given target accounts
			(account, flist) = self.get_friends(i)	# get friend list
			network.update({account['id']: [j['id'] for j in flist]})
		for i in range(depth):	# stay in depth limit
			for j in network:
				for k in network[j]:
					if not k in network:
						(account, flist) = self.get_friends(k)	# get friend list
						network.update({account['id']: [l['id'] for l in flist]})
						if self.driver.stop_check():
							self.write_network(network)
							return
		self.write_network(network)

	def write_network(self, network):
		'Write network data'
		self.storage.write_json(network, 'network.json')
		nodes = []	# list of friend connections: [ {id1, id2}, {id1, id3}, {id2, id4} ]
		for i in network:
			for j in network[i]:
				if {i,j} not in nodes:	# uniq
					nodes.append({i,j})
		self.storage.write_2d(nodes, 'network.csv')

	def write_account(self, account):
		'Write account information as CSV and JSON file'
		self.storage.write_1d([ account[i] for i in self.ACCOUNT], 'account.csv', account['id'])
		self.storage.write_json(account, 'account.json', account['id'])
