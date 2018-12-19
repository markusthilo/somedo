#!/usr/bin/env python3

import re, datetime, time, random

class Facebook:
	'Downloader for Facebook Accounts'

	ONEYEARAGO  = ( datetime.datetime.now() - datetime.timedelta(days=366) ).strftime('%Y-%m-%d')
	DEFAULT_PAGE_LIMIT = 200
	DEFINITION = [
		'Facebook',
		['Email', 'Password'],
		[
			[['Timeline', True],
				['Expand', False],
				['Translate', False],
				['Visitors', False],
				['Until', ONEYEARAGO],
				['Limit', DEFAULT_PAGE_LIMIT]],
			[['About', False]],
			[['Photos', False],
				['Expand', False],
				['Translate', False],
				['Limit', DEFAULT_PAGE_LIMIT]],
			[['Videos', False],
				['Limit', DEFAULT_PAGE_LIMIT]],
			[['Friends', False]],
			[['Network', False], ['Depth', 1]]
		]
	]

	ACCOUNT = ('type', 'id', 'name', 'path', 'link')

	def __init__(self, target, options, login, chrome, storage):
		'Generate object for Facebook by giving the needed parameters'
		self.storage = storage
		self.chrome = chrome
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
			accounts = [ self.get_landing(i) for i in self.extract_paths(target) ]	# get account infos with a first visit
			if 'Network' in options:
				self.get_network(accounts, options['Network']['Depth'])
			for i in accounts:
				if self.chrome.stop_check():
					break
				if 'About' in options:
					self.get_about(i)
				if self.chrome.stop_check():
					break
				if 'Photos' in options:
					self.get_photos(
						i,
						expand = 'Expand' in options['Photos'] and options['Photos']['Expand'],
						translate = 'Translate' in options['Photos'] and options['Photos']['Translate'],
						limit = options['Photos']['Limit']
					)
				if self.chrome.stop_check():
					break
				if 'Videos' in options:
					self.get_videos(
						i,
						limit = options['Videos']['Limit']
					)
				if self.chrome.stop_check():
					break
				if 'Friends' in options and not 'Network' in options:	# friend list download is included in network option
					self.get_friends(i)
				if self.chrome.stop_check():
					break
				if 'Timeline' in options:
					self.stop_utc = self.get_utc(options['Timeline']['Until'])
					self.get_timeline(
						i,
						expand = 'Expand' in options['Timeline'] and options['Timeline']['Expand'],
						translate = 'Translate' in options['Timeline'] and options['Timeline']['Translate'],
						visitors = 'Visitors' in options['Timeline'] and options['Timeline']['Visitors'],
						until = self.get_utc(options['Timeline']['Until']),
						limit = options['Timeline']['Limit']
					)
		else:	# error robust
			errors = ''# to return errors that might help
			accounts = []	# list of target accounts
			for i in self.extract_paths(target):	# get account infos with a first visit
				try:
					account = self.get_landing(i)
				except:
					continue
				accounts.append(account)
			if 'Network' in options:
				try:
					self.get_network(accounts, options['Network']['Depth'])
				except:
					errors += ' Network,'
			for i in accounts:
				if self.chrome.stop_check():
					break
				if 'About' in options:
					try:
						self.get_about(i)
					except:
						errors += ' %s/About,' % i
				if self.chrome.stop_check():
					break
				if 'Photos' in options:
					try:
						self.get_photos(
							i,
							expand = 'Expand' in options['Photos'] and options['Photos']['Expand'],
							translate = 'Translate' in options['Photos'] and options['Photos']['Translate'],
							limit = options['Photos']['Limit']
						)
					except:
						errors += ' %s/Photos,' % i
				if self.chrome.stop_check():
					break
				if 'Friends' in options and not 'Network' in options:	# friend list download is included in network option
					try:
						self.get_friends(i)
					except:
						errors += ' %s/Friends,' % i
				if self.chrome.stop_check():
					break
				if 'Timeline' in options:
					try:
						self.get_timeline(
							i,
							expand = 'Expand' in options['Timeline'] and options['Timeline']['Expand'],
							translate = 'Translate' in options['Timeline'] and options['Timeline']['Translate'],
							visitors = 'Visitors' in options['Timeline'] and options['Timeline']['Visitors'],
							until = self.get_utc(options['Timeline']['Until']),
							limit = options['Timeline']['Limit']
						)
					except:
						errors += ' %s/Timeline,' % i
			if errors != '':
				raise Exception('The following Facebook account(s)/action(s) returned errors: %s' % errors[:-1])

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
		except:
			return 0

	def dirname(self, account):
		'Generate dirname to store Screenshots, PDFs, JSON, CSV etc.'
		m = re.search('profile\.php\?id=[0-9]+', account['path'])
		if m == None:
			dirname = account['path']
		else:
			dirname = m.group()[15:]
		return dirname.replace('/', '_')

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

	def get_profile_id(self, html):
		'Extract id'
		m = re.search('id=[0-9]+', html)
		if m == None:
			return None
		return m.group()[3:]

	def get_profile_name(self, html):
		'Extract name'
		m = re.search('>[^<]+</a>', html)
		if m == None:
			return 'undetected'
		return m.group()[1:-4]

	def get_profile_path(self, html):
		'Extract path'
		m = re.search(' href="https://www.facebook.com/[^?]+', html)
		if m == None:
			return 'undetected'
		if m.group()[32:] != 'profile.php':
			return m.group()[32:]
		m = re.search(' href="https://www.facebook.com/profile.php\?id=[^&]+', html)
		if m == None:
			return 'undetected'
		return m.group()[47:]

	def get_profile_link(self, html):
		'Extract link to profile'
		m = re.search(' href="https://www.facebook.com/[^?]+', html)
		if m == None:
			return 'undetected'
		if m.group()[32:] != 'profile.php':
			return m.group()[7:]
		m = re.search(' href="https://www.facebook.com/profile.php\?id=[^&]+', html)
		if m == None:
			return 'undetected'
		return m.group()[7:]

	def get_profile(self, html):
		'Extract profile'
		fid = self.get_profile_id(html)
		if fid == None:
			return None
		return {
			'type': 'profile',
			'id': fid,
			'name': self.get_profile_name(html),
			'path': self.get_profile_path(html),
			'link': self.get_profile_link(html)
		}

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

	def rm_left(self):
		'Remove Intro, Photos, Friends etc. on the left'
		self.chrome.rm_outer_html('ClassName', '_1vc-')

	def rm_right(self):
		'Remove stuff right of timeline/posts'
		self.chrome.rm_outer_html_by_id('entity_sidebar')
		self.chrome.rm_outer_html_by_id('pages_side_column')

	def click_translations(self):
		'Find the See Translation buttons and click'
		html = self.chrome.get_inner_html_by_id('recent_capsule_container')
		if html == None:
			html = self.chrome.get_inner_html_by_id('pagelet_timeline_main_column')
		if html == None:
			html = self.chrome.get_inner_html_by_id('pagelett_group_mall')
		if html == None:
			return
		for i in re.findall('<span id="translationSpinnerPlaceholder_[^"]+"', html):
			self.chrome.click_element_by_id(i[10:-1])

	def terminator(self):
		'Check date of posts to abort'
		if self.stop_utc <= 0:
			return False
		for i in self.chrome.get_outer_html('TagName', 'abbr'):
			m = re.search(' data-utime="[0-9]+" ', i)
			try:
				if int(m.group()[13:-2]) <= self.stop_utc:
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
				['ClassName', 'UFICommentLink'],
				['ClassName', ' UFIReplyList']
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
		html = self.chrome.get_inner_html_by_id('fbTimelineHeadline')
		m = re.search('src="[^"]+', html)
		if m != None:
			print(m.group()[5:], 'profile_pic.jpg', self.dirname(account))
			self.storage.download(m.group()[5:], 'profile_pic.jpg', self.dirname(account))	# download profile pic

		self.rm_pagelets()	# remove bluebar etc.
		path_no_ext = self.storage.path('landing', self.dirname(account))
		self.chrome.visible_page_png(path_no_ext)	# save the visible part of the page as png
		self.chrome.page_pdf(path_no_ext)
		return account

	def get_timeline(self, account, expand=False, translate=False, visitors=False, until=ONEYEARAGO, limit=DEFAULT_PAGE_LIMIT):
		'Get timeline'
		if account['type'] == 'pg':
			self.chrome.navigate('https://www.facebook.com/pg/%s/posts' % account['path'])
			path_no_ext = self.storage.path('posts', self.dirname(account))
		else:
			self.chrome.navigate(account['link'])
			path_no_ext = self.storage.path('timeline', self.dirname(account))
		self.rm_profile_cover()
		self.rm_pagelets()
		self.rm_left()
		self.rm_right()
		self.expand_page(path_no_ext=path_no_ext, expand=expand, translate=translate, until=until, limit=limit)	# go through timeline
		self.chrome.page_pdf(path_no_ext)
		if visitors:
			self.get_visitors(account)

	def get_visitors(self, account):
		'Get all visitors who left comments or likes etc. in timeline - timeline has to be open end expand'
		visitors = []	# list to store links to other profiles
		visitor_ids = {account['id']}	# create set to store facebook ids of visitors to get uniq visitors
		actors = self.chrome.get_outer_html('ClassName', ' UFICommentActorName')	# get comment actors
		if actors != None:
			for i in actors:
				visitor = self.get_profile(i)
				if visitor != None and not visitor['id'] in visitor_ids:	# uniq
					visitors.append(visitor)
					visitor_ids.add(visitor['id'])
		for i in re.findall('href="/ufi/reaction/[^"]+"', self.chrome.get_outer_html_by_id('recent_capsule_container')):	# go through reactions
			if self.chrome.stop_check():
				return
			self.chrome.navigate('https://www.facebook.com' + i[6:-1])	# open reaction page
			self.chrome.expand_page(terminator=self.terminator)	# scroll through page
			self.rm_pagelets()	# remove bluebar etc.
			html = self.chrome.get_inner_html_by_id('content')	# get the necessary part of the page
			if html == '':
				continue
			for j in re.findall(' href="https://www\.facebook\.com/[^"]+hc_location=profile_browser" data-hovercard="[^"]+"[^<]+</a>', html):	# get people who reacted
				visitor = self.get_profile(j)
				if visitor != None and not visitor['id'] in visitor_ids:	# uniq
					visitors.append(visitor)
					visitor_ids.add(visitor['id'])
		dirname = self.dirname(account)
		self.storage.write_2d([ [ i[j] for j in self.ACCOUNT ] for i in visitors ], 'visitors.csv', dirname)
		self.storage.write_json(visitors, 'visitors.json', dirname)

	def get_about(self, account):
		'Get About'
		self.chrome.navigate('%s/about' % account['link'])	# go to about
		path_no_ext=self.storage.path('about', self.dirname(account))
		self.rm_pagelets()	# remove bluebar etc.
		self.expand_page(path_no_ext=path_no_ext)
		self.chrome.page_pdf(path_no_ext)

	def get_photos(self, account, expand=False, translate=False, limit=DEFAULT_PAGE_LIMIT):
		'Get Photos'
		if account['type'] == 'pg':
			self.chrome.navigate('https://www.facebook.com/pg/%s/photos' % account['path'])
#		elif account['type'] == 'profile':
#			self.chrome.navigate('https://www.facebook.com/%s/photos_all' % account['path'])
#		else:
#			self.chrome.navigate('https://www.facebook.com/%s/photos' % account['path'])
		else:
			self.chrome.navigate('https://www.facebook.com/%s/photos_all' % account['path'])
		dirname = self.dirname(account)
		path_no_ext = self.storage.path('photos', dirname)
		self.rm_pagelets()	# remove bluebar etc.
		self.rm_right()
		self.expand_page(path_no_ext=path_no_ext, limit=limit)
		self.rm_left()
		self.chrome.page_pdf(path_no_ext)
		html = self.chrome.get_outer_html_by_id('pagelet_timeline_medley_photos')
		if html == None:
			html = self.chrome.get_outer_html_by_id('content_container')
			if html == None:
				return
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

	def get_videos(self, account, limit=DEFAULT_PAGE_LIMIT):
		'Get Videos'
#		if account['type'] == 'pg':
#			self.chrome.navigate('https://www.facebook.com/pg/%s/photos' % account['path'])
#		elif account['type'] == 'profile':
#			self.chrome.navigate('https://www.facebook.com/%s/photos_all' % account['path'])
#		else:
#			self.chrome.navigate('https://www.facebook.com/%s/photos' % account['path'])
#		else:
		self.chrome.navigate('https://www.facebook.com/%s/videos' % account['path'])
		dirname = self.dirname(account)
		path_no_ext = self.storage.path('videos', dirname)
		self.rm_pagelets()	# remove bluebar etc.
		self.rm_right()
		self.expand_page(path_no_ext=path_no_ext, limit=limit)
		self.rm_left()
		self.chrome.page_pdf(path_no_ext)
		html = self.chrome.get_outer_html_by_id('pagelet_timeline_medley_videos')
		if html == None:
			return
		for i in re.findall('' ,html):
			print(i)

	def get_friends(self, account):
		'Get friends list from given user (id or path)'
		dirname = self.dirname(account)
		if account['type'] == 'profile':
			self.chrome.navigate('%s/friends' % account['link'])
			path_no_ext = self.storage.path('friends', dirname)
			self.rm_pagelets()	# remove bluebar etc.
			self.rm_left()
			self.chrome.expand_page(path_no_ext=path_no_ext)	# no limit for friends - it makes no sense not getting all friends
			self.chrome.page_pdf(path_no_ext)
			html = self.chrome.get_inner_html_by_id('pagelet_timeline_medley_friends')	# try to get friends
			if html == None:
				return []	# return empty list if no visible friends
			flist = []	# list to store friends
			for i in re.findall(' href="https://www\.facebook\.com\/[^<]+=friends_tab" [^<]+</a>', html):	# get the links to friends
				friend = self.get_profile(i)
				if friend != None:
					flist.append(friend)	# append to friend list if info was extracted
			self.storage.write_2d([ [ i[j] for j in i] for i in flist ], 'friends.csv', dirname)
			self.storage.write_json(flist, 'friends.json', dirname)
			return flist	# return friends as list
		if account['type'] == 'groups':
			self.chrome.navigate('%s/members' % account['link'])
			path_no_ext = self.storage.path('members', dirname)
			self.rm_pagelets()	# remove bluebar etc.
			self.rm_right()
			self.chrome.expand_page(path_no_ext=path_no_ext)	# no limit for friends - it makes no sense not getting all friends
			self.rm_left()
			self.chrome.page_pdf(path_no_ext)
			html = self.chrome.get_inner_html_by_id('groupsMemberBrowser')	# try to get members
			if html == None:
				return []	# return empty list if no visible friends
			mlist = []	# list to store friends
			for i in re.findall(' href="https://www\.facebook\.com\/[^<]+location=group" [^<]+</a>', html):	# regex vs facebook
				member = self.get_profile(i)
				if member != None:
					mlist.append(member)	# append to friend list if info was extracted
			self.storage.write_2d([ [ i[j] for j in i] for i in mlist ], 'members.csv', dirname)
			self.storage.write_json(mlist, 'members.json', dirname)
			return mlist	# return friends as list
		return []

	def get_network(self, accounts, depth):
		'Get friends and friends of friends and so on to given depth or abort if limit is reached'
		network = dict()	# dictionary to store friend lists
		old_ids = set()	# set to store ids (friend list has been downloaded)
		for i in accounts:	# start with the given target accounts
			if self.chrome.stop_check():
				break
			flist = self.get_friends(i)	# get friend list
			if flist != []:
				network.update({i['id']: [ j['id'] for j in flist ]})
				old_ids.add(i['id'])
		for i in range(depth):	# stay in depth limit and go through friend lists
			if self.chrome.stop_check():
				break
			for j in { k for j in network for k in network[j] } - old_ids:	# work on friend list which have not been downloaded so far
				flist = self.get_friends(self.get_landing(j))	# get friend list
				if flist != []:
					network.update({j: [ k['id'] for k in flist ]})
					old_ids.add(j)
				if self.chrome.stop_check():
					break
		self.storage.write_json(network, 'network.json')
		friends = []	# list to store pairs of befriended accounts (ids only)
		for i in network:
			for j in network[i]:
				if not (i, j) in friends and not (j, i) in friends:
					friends.append((i ,j))
		self.storage.write_2d(friends, 'network.csv') # list of friend connections
