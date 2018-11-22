#!/usr/bin/env python3

import re, datetime, time, random

class Facebook:
	'Downloader for Facebook'

	ONEYEARAGO  = ( datetime.datetime.now() - datetime.timedelta(days=366) ).strftime('%Y-%m-%d')
	DEFAULT_PAGE_LIMIT = 200
	DEFINITION = [
		'Facebook',
		['Email', 'Password'],
		[
			[['Timeline', True], ['Expand', False], ['Translate', False], ['Visitors', False], ['Until', ONEYEARAGO], ['Limit', DEFAULT_PAGE_LIMIT]],
			[['About', False]],
			[['Photos', False], ['Expand', False], ['Translate', False], ['Limit', DEFAULT_PAGE_LIMIT]],
			[['Friends', False]],
			[['Network', False], ['Depth', 1]]
		]
	]

	ACCOUNT = ('type', 'id', 'name', 'path', 'link')

	def __init__(self, target, options, login, chrome, storage):
		'Generate object for Facebook by giving the needed parameters'
		self.storage = storage
		self.chrome = chrome
		targets = self.extract_paths(target)
		self.chrome.navigate('https://www.facebook.com/login')	# go to facebook login
		for i in range(3):	# try 3x to log into your facebbok account
			self.sleep(1)
			try:
				self.chrome.insert_element_by_id('email', login['Email'])	# login with email
				self.chrome.insert_element_by_id('pass', login['Password'])	# and password
				self.chrome.click_element_by_id('loginbutton')	# click login
			except:
				continue
			self.sleep(1)
			if self.chrome.get_inner_html_by_id('findFriendsNav') != None:
				break
			if i == 2:
				self.chrome.visible_page_png(self.storage.path('login'))
				raise Exception('Could not login to Facebook.')
		if self.chrome.debug:	# abort on errors in debug mode
			if 'Network' in options:
				self.get_network(targets, options['Network']['Depth'])
			for i in targets:
				if self.chrome.stop_check():
					break
				account = self.get_landing(i)
				if self.chrome.stop_check():
					break
				if 'Timeline' in options:
					self.stop_utc = self.get_utc(options['Timeline']['Until'])
					self.get_timeline(
						account,
						expand = 'Expand' in options['Timeline'] and options['Timeline']['Expand'],
						translate = 'Translate' in options['Timeline'] and options['Timeline']['Translate'],
						visitors = 'Visitors' in options['Timeline'] and options['Timeline']['Visitors'],
						until = self.get_utc(options['Timeline']['Until']),
						limit = options['Timeline']['Limit']
					)
				if self.chrome.stop_check():
					break
				if 'Posts' in options:
					self.stop_utc = self.get_utc(options['Posts']['Until'])
					account = self.get_posts(
						i,
						expand = 'Expand' in options['Posts'] and options['Posts']['Expand'],
						translate = 'Translate' in options['Posts'] and options['Posts']['Translate'],
						visitors = 'Visitors' in options['Posts'] and options['Posts']['Visitors'],
						account = account,
						limit = options['Posts']['Limit']
					)
				if self.chrome.stop_check():
					break
				if 'About' in options:
					account = self.get_about(i, account = account)
				if self.chrome.stop_check():
					break
				if 'Photos' in options:
					account = self.get_photos(
						i,
						expand = 'Expand' in options['Photos'] and options['Photos']['Expand'],
						translate = 'Translate' in options['Photos'] and options['Photos']['Translate'],
						account = account,
						limit = options['Photos']['Limit']
					)
				if self.chrome.stop_check():
					break
				if 'Friends' in options and not 'Network' in options:	# friend list download is included in network option
					account = self.get_friends(i, account = account)
		else:	# error robust
			errors = ''
			if 'Network' in options:
				try:
					self.get_network(targets, options['Network']['Depth'])
				except:
					errors += ' Network,'
			for i in targets:
				account = None	# reset targeted account
				if self.chrome.stop_check():
					break
				if 'Landing' in options:
					try:
						account = self.get_landing(i, account=account)
					except:
						errors += ' %s/Landing,' % i
				if self.chrome.stop_check():
					break
				if 'Timeline' in options:
					try:
						self.stop_utc = self.get_utc(options['Timeline']['Until'])
						account = self.get_timeline(
							i,
							expand = 'Expand' in options['Timeline'] and options['Timeline']['Expand'],
							translate = 'Translate' in options['Timeline'] and options['Timeline']['Translate'],
							visitors = 'Visitors' in options['Timeline'] and options['Timeline']['Visitors'],
							account = account,
							limit = options['Timeline']['Limit']
						)
					except:
						errors += ' %s/Timeline,' % i
				if self.chrome.stop_check():
					break
				if 'Posts' in options:
					try:
						self.stop_utc = self.get_utc(options['Posts']['Until'])
						account = self.get_posts(
							i,
							expand = 'Expand' in options['Posts'] and options['Posts']['Expand'],
							translate = 'Translate' in options['Posts'] and options['Posts']['Translate'],
							visitors = 'Visitors' in options['Posts'] and options['Posts']['Visitors'],
							account = account,
							limit = options['Posts']['Limit']
						)
					except:
						errors += ' %s/Posts,' % i
				if self.chrome.stop_check():
					break
				if 'About' in options:
					try:
						account = self.get_about(i, account = account)
					except:
						errors += ' %s/About,' % i
				if self.chrome.stop_check():
					break
				if 'Photos' in options:
					try:
						account = self.get_photos(
							i,
							expand = 'Expand' in options['Photos'] and options['Photos']['Expand'],
							translate = 'Translate' in options['Photos'] and options['Photos']['Translate'],
							account = account,
							limit = options['Photos']['Limit']
						)
					except:
						errors += ' %s/Photos,' % i
				if self.chrome.stop_check():
					break
				if 'Friends' in options and not 'Network' in options:	# friend list download is included in network option
					try:
						account = self.get_friends(i, account = account)
					except:
						errors += ' %s/Friends,' % i
			if errors != '':
				raise Exception('The following Facebook accont(s)/action(s) returned errors: %s' % errors.rstrip(','))

	def sleep(self, t):
		'Sleep a slightly ranomized time'
		time.sleep(t + random.uniform(0, 0.1))

	def extract_paths(self, target):
		'Extract facebook paths from target that might be urls'
		l= []	# list for the target users (id or path)
		for i in target.split(';'):
			i = re.sub('^.*facebook.com/', '', i.strip().rstrip().rstrip('/'))
			i = re.sub('&.*$', '', i)
			if i != '':
				l.append(i)
		return l

	def get_utc(self, date_str):
		'Convert date given as string (e.g. "2018-02-01") to utc as seconds since 01.01.1970'
		l = date_str.split('-')
		try:
			return int(datetime.datetime(int(l[0]),int(l[1]),int(l[2]),0,0).timestamp())
		except ValueError:
			return 0

	def get_fid(self, html):
		'Extract facebook id using regex'
		m = re.search('\.php\?id=[0-9]+', html)	# get id
		if m == None:
			return ''
		return m.group()[8:]

	def get_name(self, html):
		'Extract name of a facebook link using regex'
		m = re.search('">[^<]+</a>', html)	# cut out name
		if m == None:
			return ''
		return m.group()[2:-4]

	def get_path(self, html):
		'Extract path of a facebook link using regex'
		m = re.search('href="https://www\.facebook\.com/[^?/"]+.', html)	# cut out from href
		if m == None:
			return ''
		if m.group()[31:] == 'profile.php?':	# regular profile id only
			m = re.search('href="https://www\.facebook\.com/profile\.php\?id=[0-9]+', html)	# cut out more to get profile.php?id=100...
			if m == None:	# just in case...
				return ''
			return m.group()[31:]
		if m.group()[31:] == 'pages/':	# facebook pages like places etc.
			m = re.search('href="https://www\.facebook\.com/pages/[^/]+', html)	# cut out more to get profile.php?id=100...
			if m == None:	# just in case...
				return ''
			return m.group()[37:]
		if m.group()[-1] == '?':	# regular profile with facebook user name as path
			return m.group()[31:-1]
		return ''

	def get_flink(self, html):
		'Extract facebook link using regex'
		m = re.search('href="https://www\.facebook\.com/profile\.php\?id=[0-9]+', html)	# get link on url: ...?id=100...
		if m != None:
			return m.group()[6:]
		m = re.search('href="https://www\.facebook\.com/pages/[^/"?]+', html)	# get link on url: .../pages/...
		if m != None:
			return m.group()[6:]
		m = re.search('href="https://www\.facebook\.com/[^/"?]+', html)	# get link on url: .../path?...
		if m != None:
			return m.group()[6:]
		return ''

	def get_user(self, html):
		'Get complete user information out of link'
		fid = self.get_fid(html)	# get id
		if fid == '':
			return None
		name = self.get_name(html)	# get name
		if name == '':
			return None
		path = self.get_path(html)	# get path
		if path == '':
			return None
		flink = self.get_flink(html)	# get link
		if flink == '':
			return None
		return {'id': fid, 'name': name, 'path': path, 'link': flink}

	def extract_coverinfo(self):
		'Get information about given user (id or path) out of targeted profile cover'
		html = self.chrome.get_inner_html_by_id('fbProfileCover')
		if html == None:	# exit if no cover ProfileCover
			return None
		account = {'type': 'profile'}
		m = re.search(' data-referrerid="[0-9]+" ', html)	# get id
		try:
			account['id'] = m.group()[18:-2]
		except:
			account['id'] = 'undetected'
		html = self.chrome.get_inner_html_by_id('fb-timeline-cover-name')
		m = re.search('">[^<]+</a>', html)	# try to cut out displayed name (e.g. John McLane)
		try:
			account['name'] = m.group()[2:-4]
		except:
			m = re.search('href="https://www\.facebook\.com/[^"]+"><span>[^<]+<', html)
			try:
				account['name'] = m.group().split('>')[2][:-1]
			except:
				account['name'] = 'undetected'
		html = self.chrome.get_inner_html_by_id('fbTimelineHeadline')
		m = re.search(' data-tab-key="timeline" href="https://www\.facebook\.com/[^"]+[?&]lst=', html)
		try:
			account['link'] = m.group()[31:-5]
			account['path'] = m.group()[56:-5]
		except:
			account['link'] = None
			account['path'] = None
		return account	# return dictionary

	def extract_sidebarinfo(self):
		'Get infos from entity_sidebar'
		html = self.chrome.get_outer_html_by_id('entity_sidebar')
		if html == None:	# exit if no cover entity_sidebar
			return None
		account = {'type': 'pg'}
		m = re.search(' href="https://www\.facebook\.com/[^"]+"><span>[^<]+', html)
		try:
			account['name'] = m.group().rsplit('>', 1)[1]
			account['path'] = m.group().rsplit('/', 2)[1]
			account['link'] = m.group()[7:].split('"')[0][:-1]
		except:
			account['name'] = 'undetected'
			account['path'] = None
			account['link'] = None
		m = re.search(' aria-label="Profile picture" class="[^"]+" href="/[0-9]+', html)
		try:
			account['id'] = m.group().rsplit('/', 1)[1]
		except:
			account['id'] = 'undetected'
		return account

	def extract_leftcolinfo(self):
		'Get infos from leftCol'
		html = self.chrome.get_inner_html_by_id('leftCol')
		if html == None:	# exit if no cover entity_sidebar
			return None
		m = re.search('<a href="/[^"]+">[^<]+', html)
		try:
			account = {'type': m.group().split('/', 3)[1], 'id': 'undetected'}
			account['name'] = m.group().rsplit('>', 1)[1]
			account['path'] = '%s/%s' % ( m.group().split('/', 3)[1], m.group().split('/', 3)[2] )
			account['link'] = 'https://www.facebook.com/%s/%s' % ( m.group().split('/', 3)[1], m.group().split('/', 3)[2] )
		except:
			account = None
		return account

	def dirname(self, account):
		'Generate dirname to store Screenshots, PDFs, JSON, CSV etc.'
		m = re.search('profile\.php\?id=[0-9]+', account['path'])
		if m == None:
			dirname = account['path']
		else:
			dirname = m.group()[15:]
		return dirname.replace('/', '_')

	def get_account(self, path):
		'Get account data and write information as CSV and JSON file if not alredy done'
		account = self.extract_coverinfo()	# try to get facebook id, path/url and name from profile page
		if account == None:
			account = self.extract_sidebarinfo()	# try to get account info from pg page
		if account == None:
			account = self.extract_leftcolinfo()	# try to get account info from groups etc.
		if account == None:
			account = {'type': 'unknown', 'id': 'undetected', 'name': 'undetected', 'path': path, 'link': 'https://www.facebook.com/%s' % path}
		if account['path'] == None:
			 account['path'] = path
			 account['link'] = 'https://www.facebook.com/%s' % path
		dirname = self.dirname(account)
		self.storage.write_dicts(account, self.ACCOUNT, 'account.csv', dirname)
		self.storage.write_json(account, 'account.json', dirname)
		return account

	def rm_pagelets(self):
		'Remove bluebar and other unwanted pagelets'
		self.chrome.rm_outer_html_by_id('pagelet_bluebar')
		self.chrome.rm_outer_html_by_id('pagelet_sidebar')
		self.chrome.rm_outer_html_by_id('pagelet_dock')
		self.chrome.rm_outer_html_by_id('pagelet_escape_hatch')	# remove "Do you know ...?"
		self.chrome.rm_outer_html_by_id('pagelet_ego_pane')	# remove "Suggested Groups"
		self.chrome.rm_outer_html_by_id('pagelet_rhc_footer')
		self.chrome.rm_outer_html_by_id('pagelet_page_cover')
		self.chrome.rm_outer_html_by_id('ChatTabsPagelet')
		self.chrome.rm_outer_html_by_id('BuddylistPagelet')

	def rm_profile_cover(self):
		'Remove fbProfileCover'
		self.chrome.rm_outer_html_by_id('fbProfileCover')

	def rm_sides_of_timeline(self):
		'Remove Intro, Photos, Friends etc. on the left'
		self.chrome.rm_outer_html('ClassName', '_1vc-')
		self.chrome.rm_outer_html_by_id('entity_sidebar')
		self.chrome.rm_outer_html_by_id('pages_side_column')

	def click_translations(self):
		'Find the See Translation buttons and click'
		html = self.chrome.get_inner_html_by_id('recent_capsule_container')
		for i in re.findall('<span id="translationSpinnerPlaceholder_[^"]+"', html):
			self.chrome.click_element_by_id(i[10:-1])

	def terminator(self):
		'Check date of posts to abort'
		if self.stop_utc <= 0:
			return False
		try:
			for i in self.chrome.get_outer_html('TagName', 'abbr'):
				m = re.search('.* data-utime=".* class="timestampContent">.*', i)
				if int(re.sub('.*data-utime="', '', m.group()).split('"')[0]) <= self.stop_utc:
					return True
		except:
			pass
		return False

	def expand_page(self, path_no_ext='', expand=True, translate=False, until=ONEYEARAGO, limit=0):
		'Go through page, expand, translate, take screenshots and generate pdf'
		clicks = []
		if expand:	# clicks to expand page
			clicks.extend([
				['ClassName', 'see_more_link'],
				['ClassName', 'UFIPagerLink'],
				['ClassName', 'UFICommentLink']
			])
		if translate:	# show translations if in options
			clicks.extend([
				['ClassName', 'UFITranslateLink']
			])
			action = self.click_translations()
		else:
			action = None
		self.stop_utc = until
		self.chrome.expand_page(
			path_no_ext = path_no_ext,
			click_elements_by = clicks,
			per_page_action = action,
			terminator=self.terminator,
			limit=limit
		)

	def get_landing(self, path):
		'Get screenshot from start page about given user (id or path)'
		self.chrome.navigate('https://www.facebook.com/%s' % path)	# go to landing page of the given faebook account
		self.sleep(1)
		account = self.get_account(path)		# get account infos if not already done
		self.rm_pagelets()	# remove bluebar etc.
		path_no_ext = self.storage.path('landing', self.dirname(account))
		self.chrome.visible_page_png(path_no_ext)	# save the visible part of the page as png
		self.chrome.page_pdf(path_no_ext)
		return account

	def get_timeline(self, account, expand=False, translate=False, visitors=False, until=ONEYEARAGO, limit=DEFAULT_PAGE_LIMIT):
		'Get timeline'
		path_no_ext=self.storage.path('timeline', self.dirname(account))
		self.rm_profile_cover()
		self.rm_sides_of_timeline()
		self.expand_page(path_no_ext=path_no_ext, expand=expand, translate=translate, until=until, limit=limit)	# go through timeline
		self.chrome.page_pdf(path_no_ext)
		if visitors:
			self.get_visitors(account)
		return account

	def get_visitors(self, account):
		'Get all visitors who left comments or likes etc. in timeline - timeline has to be open end expand'
		visitors = []	# list to store links to other profiles
		visitor_ids = {account['id']}	# create set to store facebook ids of visitors to get uniq visitors
		html = self.chrome.get_outer_html_by_id('recent_capsule_container')	# get timeline
		for i in re.findall(	# look for comment authors
			'UFICommentActorName" data-hovercard="/ajax/hovercard/hovercard\.php\?id=[0-9]+[^>]*>[^<]+</a>',
			html ):
			try:
				fid = self.get_fid(i)
				flink = self.get_flink(i)
				if flink != '' and not fid in visitor_ids:	# uniq
					visitors.append({'type': 'profile', 'id': fid, 'name': self.get_name(i), 'path': self.get_path(i), 'link': flink})
					visitor_ids.add(fid)
			except:
				pass
		for i in re.findall('href="/ufi/reaction/[^"]+"', html):	# go through reactions
			if self.chrome.stop_check():
				return
			self.chrome.navigate('https://www.facebook.com' + i[6:-1])	# open reaction page
			self.chrome.expand_page(terminator=self.terminator)	# scroll through page
			self.rm_pagelets()	# remove bluebar etc.
			html = self.chrome.get_outer_html_by_id('globalContainer')	# get the necessary part of the page
			for j in re.findall(	# get people who reacted
				'href="https://www\.facebook\.com/[^"]+;hc_location=profile_browser" data-hovercard="/ajax/hovercard/user\.php\?id=[0-9]+[^>]*>[^<]+</a>',
				html ):
				try:
					fid = self.get_fid(j)
					flink = self.get_flink(j)
					if flink != '' and not fid in visitor_ids:	# uniq
						visitors.append({'type': 'profile', 'id': fid, 'name': self.get_name(j), 'path': self.get_path(j), 'link': flink})
						visitor_ids.add(fid)
				except:
					pass
		dirname = self.dirname(account)
		self.storage.write_2d([ [ i[j] for j in self.ACCOUNT ] for i in visitors ], 'visitors.csv', dirname)
		self.storage.write_json(visitors, 'visitors.json', dirname)

	def get_about(self, user, account=None):
		'Get About'
		self.chrome.navigate('https://www.facebook.com/%s/about' % user)	# go to about
		account = self.get_account(user, account)	# get account infos if not already done
		path_no_ext=self.storage.path('about', self.dirname(account))
		self.rm_pagelets()	# remove bluebar etc.
		self.expand_page(path_no_ext=path_no_ext)
		self.chrome.page_pdf(path_no_ext)
		return account

	def get_photos(self, user, expand=False, translate=False, account=None, limit=DEFAULT_PAGE_LIMIT):
		'Get Photos'
		self.chrome.navigate('https://www.facebook.com/%s/photos_all' % user)
		if self.chrome.get_outer_html_by_id('medley_header_photos') == None:
			self.chrome.navigate('https://www.facebook.com/pg/%s/photos' % user)
		account = self.get_account(user, account)	# get account infos if not already done
		dirname = self.dirname(account)
		path_no_ext = self.storage.path('photos', dirname)
		self.rm_pagelets()	# remove bluebar etc.
		self.expand_page(path_no_ext=path_no_ext, limit=limit)
		self.chrome.page_pdf(path_no_ext)
		html = self.chrome.get_outer_html_by_id('pagelet_timeline_medley_photos')
		if html == None:
			html = self.chrome.get_outer_html_by_id('content_container')
			if html == None:
				raise Exception('No photos were found')
		cnt = 1	# to number screenshots
		for i in re.findall('ajaxify="https://www\.facebook\.com/photo\.php?[^"]*"', html):	# loop through photos
			self.chrome.navigate(i[9:-1])
			self.chrome.rm_outer_html_by_id('photos_snowlift')	# show page with comments
			path_no_ext = self.storage.path('%05d_photo' % cnt, dirname)
			self.rm_pagelets()	# remove bluebar etc.
			self.expand_page(path_no_ext=path_no_ext, limit=limit, expand=expand, translate=translate)	# expand photo comments
			self.chrome.page_pdf(path_no_ext)
			cnt += 1
			if cnt == 100000:
				break
			self.chrome.go_back()
		return account

	def get_friends(self, user, account=None):
		'Get friends list from given user (id or path)'
		flist = []	# list to store friends
		self.chrome.navigate('https://www.facebook.com/%s/friends' % user)
		account = self.get_account(user, account)	# get account infos if not already done
		dirname = self.dirname(account)
		path_no_ext = self.storage.path('friends', dirname)
		self.rm_pagelets()	# remove bluebar etc.
		self.chrome.expand_page(path_no_ext=path_no_ext, limit=99999)	# no limit for friends - it makes no sense not getting all friends
		self.chrome.page_pdf(path_no_ext)
		html = self.chrome.get_inner_html_by_id('pagelet_timeline_medley_friends')	# try to get friends
		if html == None:
			return (account, flist)	# return empty list if no visible friends
		for i in re.findall('href="https://www\.facebook\.com\/[^<]+=friends_tab" [^<]+</a>',html):	# regex vs facebook
			u = self.get_user(i)
			if u != None:
				flist.append(u)	# append to friend list if info was extracted
		self.storage.write_2d([ [ i[j] for j in i] for i in flist ], 'friends.csv', dirname)
		self.storage.write_json(flist, 'friends.json', dirname)
		return (account, flist)	# return account and friends as list

	def get_network(self, targets, depth):
		'Get friends and friends of friends and so on to given depth or abort if limit is reached'
		network = dict()	# dictionary to store friend lists
		old_ids = set()	# set to store ids (friend list has been downloaded)
		for i in targets:	# start with the given target accounts
			(account, flist) = self.get_friends(i)	# get friend list
			network.update({
				account['id']: {
					'name':		account['name'],
					'path':		account['path'],
					'link':		account['link'],
					'friends':	flist
				}
			})
			old_ids.add(account['id'])
		for i in range(depth):	# stay in depth limit and go through friend lists
			new_ids = { k['id'] for j in network for k in network[j]['friends'] }	# set to store ids (friend list has not been downloaded so far)
			new_paths = { k['id']: k['path'] for j in network for k in network[j]['friends'] if k['id'] in new_ids - old_ids }	# dict to store paths
			for j in new_ids - old_ids:
				(account, flist) = self.get_friends(new_paths[j])	# get friend list
				network.update({
					account['id']: {
						'name':		account['name'],
						'path':		account['path'],
						'link':		account['link'],
						'friends':	flist
					}
				})
				old_ids.add(account['id'])
				if self.chrome.stop_check():
					self.write_network(network)
					return
		self.write_network(network)

	def write_network(self, network):
		'Write network data'
		self.storage.write_json(network, 'network.json')
		self.storage.write_2d({ (i, j['id']) for i in network for j in network[i]['friends'] }, 'network.csv') # list of friend connections
