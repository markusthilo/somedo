#!/usr/bin/env python3

from datetime import datetime, timedelta
from time import sleep as tsleep
from random import uniform as runiform
from re import sub as rsub
from re import search as rsearch
from re import findall as rfindall
from base.cutter import Cutter
from vis.netvis import NetVis

class Facebook:
	'Downloader for Facebook Accounts'

	ONEYEARAGO  = ( datetime.now() - timedelta(days=366) ).strftime('%Y-%m-%d')
	DEFAULT_PAGE_LIMIT = 200
	DEFINITION = [
		'Facebook',
		['Email', 'Password'],
		[
			[
				['Timeline', True],
				['Expand', False],
				['Translate', False],
				['Visitors', False],
				['Until', ONEYEARAGO],
				['Limit', DEFAULT_PAGE_LIMIT]
			],
			[
				['About', False]
			],
			[
				['Photos', False],
				['Expand', False],
				['Translate', False],
				['Limit', DEFAULT_PAGE_LIMIT]
			],
			[
				['Friends', False]
			],
			[
				['Network', False],
				['Depth', 1],
				['Visitors', False],
				['Limit', DEFAULT_PAGE_LIMIT]
			]
		]
	]

	ACCOUNT = ('type', 'id', 'name', 'path', 'link')

	def __init__(self, target, options, login, chrome, storage):
		'Generate object for Facebook by giving the needed parameters'
		self.storage = storage
		self.ct = Cutter()
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
				self.chrome.visible_page_png(self.storage.modpath('login'))
				raise Exception('Could not login to Facebook.')
		if self.chrome.debug:	# abort on errors in debug mode
			accounts = [ self.get_landing(i) for i in self.extract_paths(target) ]	# get account infos with a first visit
			if 'Network' in options:
				self.get_network(
					accounts,
					options['Network']['Depth'],
					extended = options['Network']['Visitors'],
					limit = options['Network']['Limit']
				)
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
						expand = options['Photos']['Expand'],
						translate = options['Photos']['Translate'],
						limit = options['Photos']['Limit']
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
						expand = options['Timeline']['Expand'],
						translate = options['Timeline']['Translate'],
						visitors =  options['Timeline']['Visitors'],
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
					self.get_network(
						accounts,
						options['Network']['Depth'],
						extended = options['Network']['Visitors'],
						limit = options['Network']['Limit']
					)
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
							expand = options['Photos']['Expand'],
							translate = options['Photos']['Translate'],
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
							expand = options['Timeline']['Expand'],
							translate = options['Timeline']['Translate'],
							visitors = options['Timeline']['Visitors'],
							until = self.get_utc(options['Timeline']['Until']),
							limit = options['Timeline']['Limit']
						)
					except:
						errors += ' %s/Timeline,' % i
			if errors != '':
				raise Exception('The following Facebook account(s)/action(s) returned errors: %s' % errors[:-1])

	def sleep(self, t):
		'Sleep a slightly ranomized time'
		tsleep(t + runiform(0, 0.1))

	def extract_paths(self, target):
		'Extract facebook paths from target that might be urls'
		l= []	# list for the target users (id or path)
		for i in target.split(';'):
			i = rsub('^.*facebook.com/', '', i.strip().rstrip().rstrip('/'))
			i = rsub('&.*$', '', i)
			if i != '':
				l.append(i)
		return l

	def get_utc(self, date_str):
		'Convert date given as string (e.g. "2018-02-01") to utc as seconds since 01.01.1970'
		l = date_str.split('-')
		try:
			return int(datetime(int(l[0]),int(l[1]),int(l[2]),0,0).timestamp())
		except:
			return 0

	def dirname(self, account):
		'Generate dirname to store Screenshots, PDFs, JSON, CSV etc.'
		m = rsearch('profile\.php\?id=[0-9]+', account['path'])
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
		m = rsearch(' data-referrerid="[0-9]+" ', html)	# get id
		try:
			account['id'] = m.group()[18:-2]
		except:
			account['id'] = None
		html = self.chrome.get_inner_html_by_id('fb-timeline-cover-name')
		m = rsearch('">[^<]+</a>', html)	# try to cut out displayed name (e.g. John McLane)
		try:
			account['name'] = m.group()[2:-4]
		except:
			m = rsearch('href="https://www\.facebook\.com/[^"]+"><span>[^<]+<', html)
			try:
				account['name'] = m.group().split('>')[2][:-1]
			except:
				account['name'] = 'undetected'
		html = self.chrome.get_inner_html_by_id('fbTimelineHeadline')
		m = rsearch(' data-tab-key="timeline" href="https://www\.facebook\.com/[^"]+[?&]lst=', html)
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
		m = rsearch(' href="https://www\.facebook\.com/[^"]+"><span>[^<]+', html)
		try:
			account['name'] = m.group().rsplit('>', 1)[1]
			account['path'] = m.group().rsplit('/', 2)[1]
			account['link'] = m.group()[7:].split('"')[0][:-1]
		except:
			account['name'] = 'undetected'
			account['path'] = None
			account['link'] = None
		m = rsearch(' aria-label="Profile picture" class="[^"]+" href="/[0-9]+', html)
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
		m = rsearch('<a href="/[^"]+">[^<]+', html)
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
		if account['id'] == None:
			account['id'] = account['path']
		return account

	def get_profile_id(self, html):
		'Extract id'
		return self.ct.search('id=[0-9]+', html)[3:]

	def get_profile_name(self, html):
		'Extract name'
		html = self.ct.search('>[^<]+</a>', html)
		if html == None:
			return 'undetected'
		return html[1:-4]

	def get_profile_path(self, html):
		'Extract path'
		if self.ct.search(' href="', html) == '':
			return 'undetected'
		path = self.ct.search(' href="https://www.facebook.com/profile.php\?id=[0-9]+', html)
		if path != None:
			return path[47:]
		path = self.ct.search(' href="https://www.facebook.com/[^?/"&]+', html)
		if path != None:
			return path[32:]
		path = self.ct.search(' href="/profile.php\?id=[0-9]+', html)
		if path != None:
			return path[8:]
		path = self.ct.search(' href="/[^?/"&]+', html)
		if path != None:
			return path[8:]
		return 'undetected'

	def get_profile_link(self, html):
		'Extract link to profile'
		path = self.get_profile_path(html)
		if path == 'undetected':
			return path
		return 'https://www.facebook.com/' + path

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
		self.chrome.rm_outer_html_by_id('timeline_small_column')

	def rm_right(self):
		'Remove stuff right of timeline/posts'
		self.chrome.rm_outer_html_by_id('entity_sidebar')
		self.chrome.rm_outer_html_by_id('pages_side_column')
		self.chrome.rm_outer_html_by_id('rightCol')

	def click_translations(self):
		'Find the See Translation buttons and click'
		html = self.chrome.get_inner_html_by_id('recent_capsule_container')
		if html == None:
			html = self.chrome.get_inner_html_by_id('pagelet_timeline_main_column')
		if html == None:
			html = self.chrome.get_inner_html_by_id('pagelett_group_mall')
		if html == None:
			return
		for i in rfindall('<span id="translationSpinnerPlaceholder_[^"]+"', html):
			self.chrome.click_element_by_id(i[10:-1])

	def terminator(self):
		'Check date of posts to abort'
		if self.stop_utc <= 0:
			return False
		for i in self.chrome.get_outer_html('TagName', 'abbr'):
			m = rsearch(' data-utime="[0-9]+" ', i)
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
		account = self.get_account(path)# get account infos if not already done
		dirname = self.dirname(account)	# generate a name for the account's subdirectory
		self.storage.mksubdir(dirname)	# as landing is the first task to perform, generate the subdiroctory here
		self.storage.write_dicts(account, self.ACCOUNT, dirname, 'account.csv')	# write account infos
		self.storage.write_json(account, dirname, 'account.json')
		try:	# try to download profile photo
			self.storage.download(self.ct.src(self.chrome.get_inner_html_by_id('fbTimelineHeadline')), dirname, 'profile.jpg')
		except:
			pass
		self.rm_pagelets()	# remove bluebar etc.
		path_no_ext = self.storage.modpath(dirname, 'landing')	# generate a file path for screenshot and pdf
		self.chrome.visible_page_png(path_no_ext)	# save the visible part of the page as png
		self.chrome.page_pdf(path_no_ext)	# and as pdf (when headless)
		return account# give back the targeted account

	def get_timeline(self, account, expand=False, translate=False, visitors=False, until=ONEYEARAGO, limit=DEFAULT_PAGE_LIMIT, dontsave=False):
		'Get timeline'
		if account['type'] == 'pg':
			self.chrome.navigate('https://www.facebook.com/pg/%s/posts' % account['path'])
			path_no_ext = self.storage.modpath(self.dirname(account), 'posts')
		else:
			self.chrome.navigate(account['link'])
			path_no_ext = self.storage.modpath(self.dirname(account), 'timeline')
		if dontsave:
			path_no_ext = ''
		self.rm_profile_cover()
		self.rm_pagelets()
		self.rm_left()
		self.rm_right()
		self.expand_page(path_no_ext=path_no_ext, expand=expand, translate=translate, until=until, limit=limit)	# go through timeline
		self.chrome.page_pdf(path_no_ext)
		if visitors:
			return self.get_visitors(account)
		else:
			return None

	def get_visitors(self, account):
		'Get all visitors who left comments or likes etc. in timeline - timeline has to be open end expand'
		visitors = []	# list to store links to other profiles
		visitor_ids = {account['id']}	# create set to store facebook ids of visitors to get uniq visitors
		items = self.chrome.get_outer_html('ClassName', 'commentable_item')	# get commentable items
		for i in items:
			for j in rfindall('<a class="[^"]+" data-hovercard="/ajax/hovercard/user\.php\?id=[^"]+" href="[^"]+"[^>]*>[^<]+</a>', i):	# get comment authors
				visitor = self.get_profile(j)
				if not visitor['id'] in visitor_ids:	# uniq
					visitors.append(visitor)
					visitor_ids.add(visitor['id'])
			href = self.ct.search('href="/ufi/reaction/profile/browser/[^"]+', i)		# get reactions
			if href != None:
				if self.chrome.stop_check():
					return
				self.chrome.navigate('https://www.facebook.com' + href[6:])	# open reaction page
				self.chrome.expand_page(terminator=self.terminator)	# scroll through page
				self.rm_pagelets()	# remove bluebar etc.
				html = self.chrome.get_inner_html_by_id('content')	# get the necessary part of the page
				for j in rfindall(
					' href="https://www\.facebook\.com/[^"]+" data-hovercard="/ajax/hovercard/user\.php\?id=[^"]+" data-hovercard-prefer-more-content-show="1"[^<]+</a>',
					html
				):
					visitor = self.get_profile(j)
					if visitor != None and not visitor['id'] in visitor_ids:	# uniq
						visitors.append(visitor)
						visitor_ids.add(visitor['id'])
		dirname = self.dirname(account)
		self.storage.write_2d([ [ i[j] for j in self.ACCOUNT ] for i in visitors ], dirname, 'visitors.csv')
		self.storage.write_json(visitors, dirname, 'visitors.json')
		return { i['id'] for i in visitors }	# return visitors ids as set

	def get_about(self, account):
		'Get About'
		self.chrome.navigate('%s/about' % account['link'])	# go to about
		path_no_ext=self.storage.modpath(self.dirname(account), 'about')
		self.rm_pagelets()	# remove bluebar etc.
		self.expand_page(path_no_ext=path_no_ext)
		self.chrome.page_pdf(path_no_ext)

	def get_photos(self, account, expand=False, translate=False, limit=DEFAULT_PAGE_LIMIT):
		'Get Photos'
		if account['type'] == 'pg':
			self.chrome.navigate('https://www.facebook.com/pg/%s/photos' % account['path'])
		if account['type'] == 'group':
			self.chrome.navigate('https://www.facebook.com/groups/%s/photos' % account['path'])
		else:
			self.chrome.navigate('https://www.facebook.com/%s/photos_all' % account['path'])
		dirname = self.dirname(account)
		path_no_ext = self.storage.modpath(dirname, 'photos')
		self.rm_pagelets()	# remove bluebar etc.
		self.rm_right()
		self.expand_page(path_no_ext=path_no_ext, limit=limit)
		self.rm_left()
		self.chrome.page_pdf(path_no_ext)
		cnt = 1	# to number screenshots
		if account['type'] == 'pg':
			html = self.chrome.get_inner_html_by_id('content_container')
			for i in rfindall('<a href="https://www.facebook.com/[^"]+/photos/[^"]+', html):
				if self.chrome.stop_check():
					return
				self.chrome.navigate(i[9:])
				self.chrome.rm_outer_html_by_id('photos_snowlift')	# show page with comments
				path_no_ext = self.storage.modpath(dirname, '%05d_photo' % cnt)
				self.rm_pagelets()	# remove bluebar etc.
				self.expand_page(path_no_ext=path_no_ext, limit=limit, expand=expand, translate=translate)	# expand photo comments
				self.chrome.page_pdf(path_no_ext)
				try:
					self.storage.download(
						self.ct.src(self.chrome.get_outer_html('ClassName', 'scaledImageFitWidth img')[0]),
						dirname,
						'%05d_image.jpg' % cnt
					)
				except:
					pass
				cnt += 1
				if cnt == 100000:
					break
				self.chrome.go_back()
		elif account['type'] == 'group':
			html = self.chrome.get_inner_html_by_id('pagelet_group_photos')
			for i in rfindall(' href="https://www.facebook.com/photo\.php\?[^"]+', html):
				if self.chrome.stop_check():
					return
				self.chrome.navigate(i[7:])
				self.chrome.rm_outer_html_by_id('photos_snowlift')	# show page with comments
				path_no_ext = self.storage.modpath(dirname, '%05d_photo' % cnt)
				self.rm_pagelets()	# remove bluebar etc.
				self.expand_page(path_no_ext=path_no_ext, limit=limit, expand=expand, translate=translate)	# expand photo comments
				self.chrome.page_pdf(path_no_ext)
				try:
					self.storage.download(
						self.ct.src(self.chrome.get_outer_html('ClassName', 'scaledImageFitWidth img')[0]),
						dirname,
						'%05d_image.jpg' % cnt
					)
				except:
					pass
				cnt += 1
				if cnt == 100000:
					break
				self.chrome.go_back()
		else:
			html = self.chrome.get_inner_html_by_id('pagelet_timeline_medley_photos')
			for i in rfindall('ajaxify="https://www\.facebook\.com/photo\.php?[^"]*"', html):	# loop through photos
				if self.chrome.stop_check():
					return
				self.chrome.navigate(i[8:])
				self.chrome.rm_outer_html_by_id('photos_snowlift')	# show page with comments
				path_no_ext = self.storage.modpath(dirname, '%05d_photo' % cnt)
				self.rm_pagelets()	# remove bluebar etc.
				self.expand_page(path_no_ext=path_no_ext, limit=limit, expand=expand, translate=translate)	# expand photo comments
				self.chrome.page_pdf(path_no_ext)
				try:
					self.storage.download(
						self.ct.src(self.chrome.get_outer_html('ClassName', 'scaledImageFitWidth img')[0]),
						dirname,
						'%05d_image.jpg' % cnt
					)
				except:
					pass
				cnt += 1
				if cnt == 100000:
					break
				self.chrome.go_back()

	def get_friends(self, account):
		'Get friends list from given user (id or path)'
		dirname = self.dirname(account)
		if account['type'] == 'profile':
			self.chrome.navigate('%s/friends' % account['link'])
			path_no_ext = self.storage.modpath(dirname, 'friends')
			self.rm_pagelets()	# remove bluebar etc.
			self.rm_left()
			self.chrome.expand_page(path_no_ext=path_no_ext)	# no limit for friends - it makes no sense not getting all friends
			self.chrome.page_pdf(path_no_ext)
			html = self.chrome.get_inner_html_by_id('pagelet_timeline_medley_friends')	# try to get friends
			if html == None:
				return []	# return empty list if no visible friends
			flist = []	# list to store friends
			for i in rfindall(' href="https://www\.facebook\.com\/[^<]+=friends_tab" [^<]+</a>', html):	# get the links to friends
				friend = self.get_profile(i)
				if friend != None:
					flist.append(friend)	# append to friend list if info was extracted
			self.storage.write_2d([ [ i[j] for j in self.ACCOUNT] for i in flist ], dirname, 'friends.csv')
			self.storage.write_json(flist, dirname, 'friends.json')
			return { i['id'] for i in flist }	# return friends ids as set
		if account['type'] == 'groups':
			self.chrome.navigate('%s/members' % account['link'])
			path_no_ext = self.storage.modpath(dirname, 'members')
			self.rm_pagelets()	# remove bluebar etc.
			self.rm_right()
			self.chrome.expand_page(path_no_ext=path_no_ext)	# no limit for friends - it makes no sense not getting all friends
			self.rm_left()
			self.chrome.page_pdf(path_no_ext)
			html = self.chrome.get_inner_html_by_id('groupsMemberBrowser')	# try to get members
			if html == None:
				return []	# return empty list if no visible friends
			mlist = []	# list to store friends
			for i in rfindall(' href="https://www\.facebook\.com\/[^<]+location=group" [^<]+</a>', html):	# regex vs facebook
				member = self.get_profile(i)
				if member != None:
					mlist.append(member)	# append to friend list if info was extracted
			self.storage.write_2d([ [ i[j] for j in self.ACCOUNT] for i in mlist ], dirname, 'members.csv')
			self.storage.write_json(mlist, dirname, 'members.json')
			return { i['id'] for i in mlist }	# return members ids as set
		return set()

	def get_network(self, accounts, depth, extended=False, limit=DEFAULT_PAGE_LIMIT):
		'Get friends and friends of friends and so on to given depth or abort if limit is reached'
		network = dict()	# dictionary to store friend lists
		old_ids = set()	# set to store ids already got handled
		all_ids = set() # set for all ids
		for i in accounts:	# start with the given target accounts
			if self.chrome.stop_check():
				break
			friends = self.get_friends(i)
			network.update({i['id']: {	# add friends
				'type': i['type'],
				'name': i['name'],
				'path': i['path'],
				'link': i['link'],
				'friends': friends
			}})
			old_ids.add(i['id'])	# remember already handled accounts
			all_ids.add(i['id'])	# update set of all ids
			all_ids |= friends
			if extended:	# also add visitors to network if desired
				visitors = self.get_timeline(
					i,
					expand=True,
					translate=False,
					visitors=True,
					until=0,
					limit=limit,
					dontsave=True
				)
				network[i['id']]['visitors'] = visitors
				all_ids |= visitors
			else:
				network[i['id']]['visitors'] = set()	# empty set if extended option is false
		if depth < 1:	# less than 1 makes no sense
			depth = 1
		for i in range(depth):	# stay in depth limit and go through friend lists
			if self.chrome.stop_check():
				break
			for j in all_ids - old_ids:	# work on friend list which have not been handled so far
				account = self.get_landing(j)
				network.update({account['id']: {	# add new account
					'type': account['type'],
					'name': account['name'],
					'path': account['path'],
					'link': account['link'],
					'friends': set(),
					'visitors': set()
				}})
				if i < depth - 1:	# on last recusion level do not get the friend lists anymore
					if self.chrome.stop_check():
						break
					network[j]['friends'] = self.get_friends(account)
					if extended:
						network[j]['visitors'] = self.get_timeline(
							i,
							expand=True,
							translate=False,
							visitors=True,
							until=0,
							limit=limit,
							dontsave=True
						)
					else:
						network[j]['visitors'] = set()

		print(network)

		netvis = NetVis(self.storage)	# create network visualisation object
		friend_edges = set()	# generate edges for facebook friends excluding doubles
		for i in network:
			netvis.add_node(
				i,
				image = '../%s/profile.jpg' % network[i]['path'],
				alt_image = './pixmaps/profile.jpg',
				label = network[i]['name'],
				title = network[i]['link']
			)
			for j in network[i]['friends']:
				if not '%s %s' % (i, j) in friend_edges:
					friend_edges.add('%s %s' % (j, i))
		for i in friend_edges:
			ids = i.split(' ')
			netvis.add_edge(ids[0], ids[1])
		if extended:	# on extended create edges for the visitors as arrows
			visitor_edges = { '%s %s' % (j, i) for i in network for j in network[i]['visitors'] }
			for i in visitor_edges:
				ids = i.split(' ')
				netvis.add_edge(ids[0], ids[1], arrow=True, dashes=True)

		netvis.write()
		


