#!/usr/bin/env python3

from datetime import datetime, timedelta
from time import sleep as tsleep
from random import uniform as runiform
from re import sub as rsub
from re import search as rsearch
from re import findall as rfindall
from base.chrometools import Chrome
from base.cutter import Cutter
from base.logger import DEBUG
from vis.netvis import NetVis

class Facebook:
	'Downloader for Facebook Accounts'

	ACCOUNT = ('type', 'id', 'name', 'path', 'link')
	ONEYEARAGO  = ( datetime.now() - timedelta(days=366) ).strftime('%Y-%m-%d')
	DEFAULTPAGELIMIT = 50
	DEFAULTNETWORKDEPTH = 1	# network: 1 = get the friends of the target accounts
	NEWLOGINAFTER = 100	# network: close browser and login again after a limited number of profile / landing visits
	OPTIONS = {
		'name': 'Facebook',
		'login': ('Email', 'Password'),
		'options': {
			'Posts': {'name': 'Get Posts', 'default': False, 'row': 0, 'column': 0},
			'extendPosts': {'name': 'Get Reactions and Comments', 'default': False, 'row': 0, 'column': 1},
			'untilPosts': {'name': 'Stop on Date', 'default': ONEYEARAGO, 'row': 0, 'column': 2},
			'limitPosts': {'name': 'Max. Number of Posts', 'default': DEFAULTPAGELIMIT, 'row': 0, 'column': 3},
			'About': {'name': 'Get About', 'default': False, 'row': 1, 'column': 0},
			'Photos': {'name': 'Get Photos', 'default': False, 'row': 2, 'column': 0},
			'limitPhotos': {'name': 'Max. number of Photos', 'default': DEFAULTPAGELIMIT, 'row': 2, 'column': 1},
			'Network': {'name': 'Network of Friends', 'default': False, 'row': 3, 'column': 0},
			'depthNetwork': {'name': 'Depth of recursion', 'default': DEFAULTNETWORKDEPTH, 'row': 3,'column': 1},
			'extendNetwork': {'name': 'incl. Responses to Posts', 'default': False, 'row': 3, 'column': 2}
		}
	}

	def __init__(self, job, storage, chrome, stop=None):
		'Generate object for Facebook by giving the needed parameters'
		self.storage = storage
		self.chrome = chrome
		self.logger = self.storage.logger
		self.stop = stop
		self.stop_check = self.chrome.stop_check
		self.options = job['options']
		self.ct = Cutter()
		self.emails = self.ct.split(job['login']['Email'])
		self.passwords = self.ct.split(job['login']['Password'])
		self.passwords += [ self.passwords[-1] for i in range(len(self.emails)-len(self.passwords)) ]	# same password
		if self.emails == [] or self.passwords == []:
			raise RuntimeError('At least one login account is needed for the Facebook module.')
		self.loginrevolver = -1	# for multiple investigator accounts
		targets = self.extract_paths(job['target'])
		self.logger.debug('Facebook: targets: %s' % targets)
		if self.options['Network']:
				accounts = self.get_network(targets)
		if self.options['Network'] and self.options['extendNetwork']:
			check4tasks = ('About', 'Photos')
		else:
			check4tasks = ('About', 'Photos', 'Posts')
		for i in targets:	# one target after the other
			if self.stop_check():
				break
			self.logger.debug('Facebook: now working on target: %s' % i)
			if self.options['Network']:	# if networrk option has been proceeded already
				account = accounts[i]	# the profiles have already been fetched
			else:
				if self.logger.level <= DEBUG:	# fragile on debug or lower logging level
					account = self.get_landing(i)	# get profiles / landing page
				else:	# error robust by default
					try:
						account = self.get_landing(i)
					except:
						self.logger.warning('Facebook: account undetected "%s"' % i)
						continue
			for j in check4tasks:	# run other desired tasks
				if self.stop_check():
					break
				if self.options[j]:
					cmd = 'self.get_%s(account)' % j.lower()
					if self.logger.level <= DEBUG:
						exec(cmd)
					else:
						try:
							exec(cmd)
						except:
							self.logger.warning('Facebook: could not execute "%s"' % cmd)
							continue
		if self.chrome.chrome_proc != None:
			if self.logger.level < DEBUG:
				self.logger.trace('Facebook: finished, now sleeping for 10 seconds')
				tsleep(10)
			self.chrome.close()
		if self.chrome.is_running():
			self.logger.warning('Facebook: Chrome/Chromium was still running finishing jobs')
			if self.logger.level < DEBUG:
				self.logger.trace('Facebook: now sleeping for 5 seconds before closing Chrome/Chromium')
				sleep(5)
			self.chrome.close()		
		self.logger.debug('Facebook: done!')

	def sleep(self, t):
		'Sleep a slightly ranomized time'
		tsleep(t + runiform(0, 0.1))

	def extract_paths(self, target):
		'Extract facebook paths from target that might be urls'
		l= []	# list for the target users (id or path)
		for i in self.ct.split(target):
			i = rsub('^.*facebook.com/', '', i.rstrip('/'))
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

	def get_profile_name(self, html):
		'Extract name'
		m = rsearch('>[^<]+</a>', html)
		if m != None:
			return m.group()[1:-4]
		m = rsearch('>[^<]+<span[^>]*>[^<]+</span>[^<]*</a>', html)
		if m != None:
			return rsub('<[^>]+>', '', m.group()[1:-4])
		return 'undetected'

	def extract_coverinfo(self):
		'Get information about given user (id or path) out of targeted profile cover'
		html = self.chrome.get_inner_html_by_id('fbProfileCover')
		if html == None:	# exit if no cover ProfileCover
			return None
		account = {'type': 'profile'}
		fid = self.ct.search(' data-referrerid="[0-9]+" ', html)	# try to get facebook id
		if fid == None:
			account['id'] = 'undetected'
		else:
			account['id'] = fid[18:-2]
		html = self.chrome.get_inner_html_by_id('fb-timeline-cover-name')
		account['name'] = self.get_profile_name(html)	# try to cut out displayed name (e.g. John McLane)
		html = self.chrome.get_inner_html_by_id('fbTimelineHeadline')	# try to get path
		path = self.ct.search(' data-tab-key="timeline" href="https://www\.facebook\.com/profile\.php\?id=[0-9]+', html)
		if path != None:
			account['path'] = path[71:]
		else:
			path = self.ct.search(' data-tab-key="timeline" href="https://www\.facebook\.com/[^"?/]+', html)
			if path == None:
				return None
			account['path'] = path[56:]
		account['link'] = 'https://www.facebook.com/' + account['path']
		return account

	def extract_seo_h1_tag(self):
		'Get infos from seo_h1_tag'
		html = self.chrome.get_inner_html_by_id('seo_h1_tag')
		if html == None:	# no seo_h1_tag?
			return None
		name = rsub('"[^"]*"', '', html)
		name = rsub('<[^>]*>', '', name)
		if 	name != '':
			account = {'name': name}
		else:
			account = {'name': 'undetected'}
		href = self.ct.search(' href="https://www\.facebook\.com/[^/?"]+', html)
		if href != None:
			account['type'] = 'pg'
			account['path'] = href[32:]
			account['link'] = href[7:]
			account['id'] = 'undetected'
		else:
			href = self.ct.search(' href="/groups/[^/?"]+', html)
			if href != None:
				account['type'] = 'groups'
				account['path'] = 'groups_' + href[15:]
				account['link'] = 'https://facebook.com' + href[7:]
				account['id'] = 'undetected'
			else:
				return None
		return account

	def extract_profileactions(self):
		'Get infos from pagelet_timeline_profile_actions'
		html = self.chrome.get_inner_html_by_id('pagelet_timeline_profile_actions')
		if html == None:	# exit if no profile actions
			return None
		html = self.ct.search('id&quot;:[0-9]+', html)
		if html == None:	# exit if no id was found
			return None
		return html[9:]

	def get_account(self, path):
		'Get account data and write information as CSV and JSON file if not alredy done'
		account = self.extract_coverinfo()	# try to get facebook id, path/url and name from profile page
		if account == None:
			account = self.extract_seo_h1_tag()	# try to get account info from facebook pages or groups
		if account == None:
			return {
				'type': 'undetected', 
				'id': 'undetected',
				'name': 'undetected',
				'path': path.replace('/', '_'),
				'link': 'https://www.facebook.com/%s' % path
			}
		return account

	def link2account(self, html):
		'Extract account infos from Facebook link, e.g. in friend lists'
		if self.ct.search(' href="', html) == None:
			return None
		account = {'type': 'undetected'}
		for i in (	#	(regex, offset for account, account type)
			(' href="https://www\.facebook\.com/profile\.php\?id=[0-9]+', 47, 'profile'),
			(' href="https://www\.facebook\.com/pg/[^"/?]+', 35, 'pg'),
			(' href="https://www\.facebook\.com/groups/[^"/?]+', 39, 'groups'),
			(' href="https://www\.facebook\.com/[^"/?]+', 32, 'profile'),
			(' href="/profile\.php\?id=[0-9]+', 23, 'profile'),
			(' href="/pg/[^"/?]+', 11, 'pg'),
			(' href="/groups/[^"/?]+', 15, 'groups'),
			(' href="/[^"/?]+', 8, 'profile')
		):
			href = self.ct.search(i[0], html)
			if href != None:
				account['path'] = href[i[1]:]
				account['type'] = i[2]
				break
		if account['type'] == 'groups':
			account['link'] = 'https://www.facebook.com/groups/' + account['path']
			account['path'] = 'groups_' + account['path']
		else:
			account['link'] = 'https://www.facebook.com/' + account['path']
		fid = self.ct.search('id=[0-9]+', html)[3:]
		if fid != None:
			account['id'] = fid
		elif self.ct.search('[0-9]+', account['path']) == account['path']:	# path is facebook id?
			account['id'] = account['path']
		else:
			account['id'] = 'undetected'
		account['name'] = self.get_profile_name(html)
		return account

	def rm_personal_pagelets(self):
		'Remove elements with IDs pagelet_bluebar, ChatTabsPagelet and BuddylistPagelet'
		self.chrome.rm_outer_html_by_id('pagelet_bluebar')
		self.chrome.rm_outer_html_by_id('pagelet_ego_pane')
		self.chrome.rm_outer_html_by_id('ChatTabsPagelet')
		self.chrome.rm_outer_html_by_id('BuddylistPagelet')

	def rm_profile_cover(self):
		'Remove element with ID fbProfileCover'
		self.chrome.rm_outer_html_by_id('fbProfileCover')

	def rm_suggestions(self):
		'Remove elements with IDs fbSuggestionsPlaceHolder and pagelet_escape_hatch'
		self.chrome.rm_outer_html_by_id('fbSuggestionsPlaceHolder')
		self.chrome.rm_outer_html_by_id('pagelet_escape_hatch')

	def rm_small_column(self):
		'Remove left of profile timeline'
		self.chrome.rm_outer_html_by_id('timeline_small_column')

	def rm_pagelets(self):
		'Remove bluebar and other unwanted pagelets'
		self.chrome.rm_outer_html_by_id('pagelet_sidebar')
		self.chrome.rm_outer_html_by_id('pagelet_dock')
		self.chrome.rm_outer_html_by_id('pagelet_escape_hatch')	# remove "Do you know ...?"
		self.chrome.rm_outer_html_by_id('pagelet_ego_pane')	# remove "Suggested Groups"
		self.chrome.rm_outer_html_by_id('pagelet_rhc_footer')
		self.chrome.rm_outer_html_by_id('pagelet_page_cover')
		self.chrome.rm_outer_html_by_id('pagelet_timeline_composer')
		self.chrome.rm_outer_html_by_id('PageComposerPagelet_')

	def rm_header_area(self):
		'Remove header area of groups'
		self.chrome.rm_outer_html_by_id('headerArea')

	def rm_left(self):
		'Remove Intro, Photos, Friends etc. on the left'
		self.chrome.rm_outer_html('ClassName', '_1vc-')
		self.chrome.rm_outer_html_by_id('timeline_small_column')

	def rm_left_col(self):
		'Remove left column from groups'
		self.chrome.rm_outer_html_by_id('leftCol')

	def rm_right(self):
		'Remove stuff right of timeline/posts'
		self.chrome.rm_outer_html_by_id('entity_sidebar')
		self.chrome.rm_outer_html_by_id('pages_side_column')
		self.chrome.rm_outer_html_by_id('rightCol')

	def rm_right_of_activity(self):
		self.chrome.rm_outer_html_by_id('pagelet_group_rhc')
		self.chrome.rm_outer_html_by_id('pages_side_column')

	def rm_write_comment(self):
		'Remove Write a comment...'
		self.chrome.rm_outer_html('ClassName', 'UFIList')

	def rm_left_of_posts(self):
		'Remove left column in pg posts'
		self.chrome.rm_outer_html_by_regex_id('content_container', 'id="PageTimelineSearchPagelet_[^"]+', 4, 0)
		self.chrome.rm_outer_html_by_regex_id('content_container', 'id="PagePostsByOthersPagelet_[^"]+', 4, 0)

	def rm_rhc_footer(self):
		'Remove pagelet_rhc_footer'
		self.chrome.rm_outer_html_by_id('pagelet_rhc_footer')

	def rm_composer_pagelet(self):
		'Remove PageComposerPagelet_'
		self.chrome.rm_outer_html_by_id('PageComposerPagelet_')

	def rm_add_comment(self):
		'Remove addComment'
		self.chrome.rm_outer_html_by_regex_id('content_container', 'id="addComment_[^"]+', 4, 0)

	def rm_u_fetchstream(self):
		'Remove u_fetchstream_'
		html = self.chrome.get_inner_html_by_id('content_container')
		self.chrome.rm_outer_html_by_regex_id('content_container', 'id="u_fetchstream_[^"]+', 4, 0)

	def rm_m_top_of_posts(self):
		'Remove all above Posts in mobile version'
		self.chrome.rm_outer_html_by_id('header')
		self.chrome.rm_outer_html_by_id('m-timeline-cover-section')
		self.chrome.rm_outer_html_by_id('timelineProfileTiles')

	def rm_forms(self):
		'Remove form html elements'
		self.chrome.rm_outer_html('TagName', 'FORM')

	def click_timeline_translations(self):
		'Find the See Translation buttons and click'
		for i in range(5):	# try 5 times to
			html = self.chrome.get_inner_html_by_id('recent_capsule_container')
			if html == None:
				html = self.chrome.get_inner_html_by_id('pagelet_timeline_main_column')
			if html == None:
				html = self.chrome.get_inner_html_by_id('pagelett_group_mall')
			if html == None:
				return
			self.chrome.click_elements('ClassName', 'UFITranslateLink')
		
		for i in rfindall('<span id="translationSpinnerPlaceholder_[^"]+"', html):
			self.chrome.click_element_by_id(i[10:-1])

	def click_timeline_comments(self):
		'Find comments and replies to expanding page by clicking them'
		self.chrome.click_elements('ClassName', 'see_more_link')
		self.chrome.click_elements('ClassName', 'UFIPagerLink')
		self.chrome.click_elements('ClassName', 'UFICommentLink')
		self.chrome.click_elements('ClassName', ' UFIReplyList')


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

	def account2html(self, account):
		'Write account info as html file'
		html = '<!doctype html>\n<html>\n<head>\n\t<title>Somed0 | Facebook Account | '
		html += account['name']
		html += '</title>\n\t<style type="text/css">\n\t\tbody {font-family: Sans-Serif;}\n\t</style>\n</head>\n<body>\n\t<h1>'
		html += account['name']
		html += '</h1><h2>Facebook ID: '
		html += account['id']
		html += ', Account Type: '
		html += account['type']
		html += '</h2>\n\t<h2>'
		html += account['link']
		html += '</h2>\n\t<h2><a href="'
		html += account['link']
		html += '" style="color: red; border-style: solid; padding: 0.2em;">Warning: Link to online Facebook account!!!</a>'
		html += '</h2></br>\n\t<img src="./account.png" alt="" style="border: solid;"\>\n</body>\n</html>'
		self.storage.write_xml(html, account['path'], 'account.html')

	def login(self):
		'Login to Facebook'
		self.chrome.open(stop=self.stop)
		self.chrome.navigate('https://www.facebook.com/login')	# go to facebook login
		for i in range(len(self.emails) * 10):	# try 10x all accounts
			if self.chrome.stop_check():
				return
			self.loginrevolver += 1
			if self.loginrevolver == len(self.emails):
				self.loginrevolver = 0
			self.sleep(1)
			self.logger.info('Facebook: Login with %s' % self.emails[self.loginrevolver])
			try:
				self.chrome.insert_element_by_id('email', self.emails[self.loginrevolver])	# login with email
				self.chrome.insert_element_by_id('pass', self.passwords[self.loginrevolver])	# and password
				self.chrome.click_element_by_id('loginbutton')	# click login
			except:
				pass
			for j in range(10):	# try for 10 seconds ig login was succesful
				self.sleep(1)
				if self.chrome.get_inner_html_by_id('pagelet_sidebar') != None:
					return
		self.chrome.visible_page_png(self.storage.modpath('login'))
		raise Exception('Could not login to Facebook.')

	def navigate(self, url):
		'Navigate to given URL. Open Chrome/Chromium and/or login if needed.'
		if not self.chrome.is_running():
			self.logger.debug('Facebook: Chrome/Chromium is not running!')
			self.login()
		self.logger.debug('Facebook: navigate to: %s' % url)
		self.chrome.navigate(url)	# go to page
		self.sleep(1)

	def get_landing(self, path):
		'Get screenshot from start page about given user (id or path)'
		self.logger.info('Facebook: Visiting %s', path)
		self.navigate('https://www.facebook.com/%s' % path)	# go to landing page of the given faebook account
		account = self.get_account(path)	# get account infos if not already done
		self.logger.info('Facebook: Data will be stored to: %s' % self.storage.mksubdir(account['path']))	# generate the subdiroctory
		self.storage.write_dicts(account, self.ACCOUNT, account['path'], 'account.csv')	# write account infos
		self.storage.write_json(account, account['path'], 'account.json')
		try:	# try to download profile photo
			self.storage.download(self.ct.src(self.chrome.get_inner_html_by_id('fbTimelineHeadline')), account['path'], 'profile.jpg')
		except:
			pass
		self.rm_personal_pagelets()	# do not show investigator account
		if account['type'] == 'profile':
			self.rm_suggestions()
		elif account['type'] == 'pg':
			self.rm_write_comment()
		elif account['type'] == 'groups':
			pass
		
		path_no_ext = self.storage.modpath(account['path'], 'account')	# generate a file path for screenshot and pdf
		self.chrome.visible_page_png(path_no_ext)	# save the visible part of the page as png
		self.chrome.page_pdf(path_no_ext)	# and as pdf (when headless)
		self.account2html(account)
		return account	# give back the targeted account

	def stop_post_date(self):
		'Check date of posts to abort'
		if self.stop_utc <= 0:
			return False
		for i in self.chrome.get_outer_html('TagName', 'abbr'):
			m = rsearch(' data-utime="[0-9]+" ', i)
			try:
				if datetime.strptime(m.group()[13:-2], '%Y-%m-%d') <= self.stop_utc:
					return True
			except:
				pass
		return False

	def get_posts(self, account):
		'Get timeline'
		visitors = []	# list to store links to other profiles
		visitor_ids = {account['id']}	# create set to store facebook ids of visitors to get uniq visitors
		self.stop_utc = self.get_utc(self.options['untilPosts'])
		self.logger.debug('Facebook: getting Posts: %s' % account['path'])
		self.logger.debug('Facebook: stop at %d UTC, take %d screenshots max.' % (self.stop_utc, self.options['limitPosts']))
		self.navigate('https://m.facebook.com/%s' % account['path'])
		self.rm_m_top_of_posts()	# romve all above posts
		if account['type'] == 'profile':
			path_no_ext = self.storage.modpath(account['path'], 'posts')
		self.chrome.expand_page(
			terminator = self.stop_post_date,
			limit = self.options['limitPosts'],
			path_no_ext = path_no_ext
		)	# scroll through posts in mobile version
		self.chrome.page_pdf(path_no_ext)
		if account['type'] == 'profile' and self.options['extendPosts']:	# get reactions and comments
			cnt = 1
			for i in self.chrome.get_outer_html('TagName', 'article'):	# go post by post
				if cnt > 99999:
					break
				href = self.ct.search(' href="/story.php\?[^"]+">', i)
				if href == None:
					continue
				self.navigate('https://m.facebook.com/%s' % self.ct.href(href))
				self.rm_forms()	# do not show investigator account
				path_no_ext = self.storage.modpath(account['path'], 'post_%05d' % cnt)
				cnt += 1
				self.chrome.expand_page(path_no_ext=path_no_ext, per_page_actions=[self.rm_forms])	# scroll through one post/story
				self.rm_forms()
				self.chrome.page_pdf(path_no_ext)
				for j in self.chrome.get_outer_html('ClassNAme', '_2b00'):	# check all profiles on page
					href = self.ct.search(' href="/[^"?/]+">', i)
					if href == None:
						continue
					


		return visitors

#			for j in rfindall('<a class="[^"]+" data-hovercard="/ajax/hovercard/user\.php\?id=[^"]+" href="[^"]+"[^>]*>[^<]+</a>', i):	# get comment authors
#				visitor = self.link2account(j)
#				if not visitor['id'] in visitor_ids:	# uniq
#					visitors.append(visitor)
#					visitor_ids.add(visitor['id'])
#			href = self.ct.search('href="/ufi/reaction/profile/browser/[^"]+', i)		# get reactions
#			if href != None:
#				if self.chrome.stop_check():
#					return
#				self.navigate('https://www.facebook.com' + href[6:])	# open reaction page
#				self.chrome.expand_page(terminator=self.terminator)	# scroll through page
#				self.rm_pagelets()	# remove bluebar etc.
#				html = self.chrome.get_inner_html_by_id('content')	# get the necessary part of the page
#				for j in rfindall(
#					' href="https://www\.facebook\.com/[^"]+" data-hovercard="/ajax/hovercard/user\.php\?id=[^"]+" data-hovercard-prefer-more-content-show="1"[^<]+</a>',
#					html
#				):
#					visitor = self.link2account(j)
#					if visitor != None and not visitor['id'] in visitor_ids:	# uniq
#						visitors.append(visitor)
#						visitor_ids.add(visitor['id'])
#		self.storage.write_2d([ [ i[j] for j in self.ACCOUNT ] for i in visitors ], account['path'], 'visitors.csv')
#		self.storage.write_json(visitors, account['path'], 'visitors.json')
#		return { i['path'] for i in visitors }	# return visitors ids as set			
#			
#			
#
#
#			for i in rfindall(' id="jumper_[^"]+', self.chrome.get_outer_html_by_id('timeline_story_column'))
#				try:
#					post = i.split(':')[2]
#				except:
#					continue
#				
#			
#			if self.options['expandTimeline'] or self.options['translateTimeline']:	# 1. scroll, 2. expand/translate
#				self.chrome.expand_page(
#					click_elements_by = clicks,
#					per_page_actions = [],
#					terminator=self.stop_post_date,
#					limit=limit
#				)
#				
#				self.stop_utc = until
#			self.chrome.expand_page(
#				path_no_ext = path_no_ext,
#				click_elements_by = clicks,
#				per_page_action = action,
#				terminator=self.terminator,
#				limit=limit
#			)	
#				
#				
#			self.expand_page(	# go through timeline
#				path_no_ext=path_no_ext,
#				limit=self.options['limitTimeline'],
#				until=self.options['untilTimeline'],
#				expand=self.options['expandTimeline'],
#				translate=self.options['translateTimeline']
#			)
#			self.chrome.page_pdf(path_no_ext)
#
#			path_no_ext = self.storage.modpath(account['path'], 'timeline')
#			self.rm_profile_cover()
#			self.rm_pagelets()
#			self.rm_left()
#			self.rm_right()
#			self.until_utc = self.options['untilTimeline']
#			if self.options['expandTimeline'] or self.options['translateTimeline']:	# 1. scroll, 2. expand/translate
#				self.chrome.expand_page(
#					click_elements_by = clicks,
#					per_page_actions = [],
#					terminator=self.stop_post_date,
#					limit=limit
#				)
#				
#					self.stop_utc = until
#		self.chrome.expand_page(
#			path_no_ext = path_no_ext,
#			click_elements_by = clicks,
#			per_page_action = action,
#			terminator=self.terminator,
#			limit=limit
#		)	
#				
#				
#					self.expand_page(	# go through timeline
#			path_no_ext=path_no_ext,
#			limit=self.options['limitTimeline'],
#			until=self.options['untilTimeline'],
#			expand=self.options['expandTimeline'],
#			translate=self.options['translateTimeline']
#		)
#		self.chrome.page_pdf(path_no_ext)		
#			self.expand_timeline(path_no_ext)	# go through timeline

		if account['type'] == 'groups':
			self.logger.debug('Facebook: getting activity: %s' % account['path'])
			self.navigate(account['link'])
			path_no_ext = self.storage.modpath(account['path'], 'activity')
			self.rm_header_area()
			self.rm_pagelets()
			self.rm_left_col()
			self.rm_right_of_activity()
			self.expand_timeline(path_no_ext)
		elif account['type'] == 'pg':
			self.logger.debug('Facebook: getting posts: %s' % account['path'])
			self.navigate('https://www.facebook.com/pg/%s/posts' % account['path'])
			path_no_ext = self.storage.modpath(account['path'], 'posts')
			self.rm_profile_cover()
			self.rm_pagelets()
			self.rm_composer_pagelet()
			self.rm_add_comment()
			self.rm_left_of_posts()
			self.rm_rhc_footer()
			self.expand_timeline(path_no_ext)	# go through posts
			self.logger.debug('Facebook: getting community: %s' % account['path'])
			self.navigate('https://www.facebook.com/pg/%s/community' % account['path'])
			path_no_ext = self.storage.modpath(account['path'], 'community')
			self.rm_profile_cover()
			self.rm_pagelets()
			self.rm_u_fetchstream()
			self.rm_rhc_footer()
			self.expand_timeline(path_no_ext)	# go through community section
		else:
			self.logger.debug('Facebook: unknown type, trying to get content anyway: %s' % account['path'])
			self.navigate(account['link'])
			path_no_ext = self.storage.modpath(account['path'], 'timeline')
			self.rm_profile_cover()
			self.rm_pagelets()
			self.rm_left()
			self.rm_right()
			self.expand_timeline(path_no_ext)

	def get_about(self, account):
		'Get About'
		self.navigate('%s/about' % account['link'])	# go to about
		path_no_ext=self.storage.modpath(account['path'], 'about')
		self.rm_pagelets()	# remove bluebar etc.
		self.expand_page(path_no_ext=path_no_ext)
		self.chrome.page_pdf(path_no_ext)

	def get_photos(self, account):
		'Get Photos'
		if account['type'] == 'pg':
			self.navigate('https://www.facebook.com/pg/%s/photos' % account['path'])
		elif account['type'] == 'groups':
			self.navigate(account['link'] + '/photos')
		else:
			self.navigate(account['link'] + '/photos_all')
		path_no_ext = self.storage.modpath(account['path'], 'photos')
		self.rm_pagelets()	# remove bluebar etc.
		self.rm_right()
		self.expand_page(path_no_ext=path_no_ext, limit=self.options['limitPhotos'])
		self.rm_left()
		self.chrome.page_pdf(path_no_ext)
		cnt = 1	# to number screenshots
		if account['type'] == 'pg':
			html = self.chrome.get_inner_html_by_id('content_container')
			if html != None:
				for i in rfindall('<a href="https://www\.facebook\.com/[^"]+/photos/[^"]+" rel="theater">', html):
					if self.chrome.stop_check():
						return
					self.navigate(i[9:-16])
					self.chrome.rm_outer_html_by_id('photos_snowlift')	# show page with comments
					path_no_ext = self.storage.modpath(account['path'], '%05d_photo' % cnt)
					self.rm_pagelets()	# remove bluebar etc.
					self.expand_page(
						path_no_ext=path_no_ext,
						limit=self.options['limitPhotos'],
						expand=self.options['expandPhotos'],
						translate=self.options['translatePhotos']
					)
					self.chrome.page_pdf(path_no_ext)
					try:
						self.storage.download(
							self.ct.src(self.chrome.get_outer_html('ClassName', 'scaledImageFitWidth img')[0]),
							account['path'],
							'%05d_image.jpg' % cnt
						)
					except:
						pass
					cnt += 1
					if cnt == 100000:
						break
					self.chrome.go_back()
		elif account['type'] == 'groups':
			html = self.chrome.get_inner_html_by_id('pagelet_group_photos')
			if html != None:
				for i in rfindall(' href="https://www.facebook.com/photo\.php\?[^"]+', html):
					if self.chrome.stop_check():
						return
					self.navigate(i[7:])
					self.chrome.rm_outer_html_by_id('photos_snowlift')	# show page with comments
					path_no_ext = self.storage.modpath(account['path'], '%05d_photo' % cnt)
					self.rm_pagelets()	# remove bluebar etc.
					self.expand_page(
						path_no_ext=path_no_ext,
						limit=self.options['limitPhotos'],
						expand=self.options['expandPhotos'],
						translate=self.options['translatePhotos']
					)
					self.chrome.page_pdf(path_no_ext)
					try:
						self.storage.download(
							self.ct.src(self.chrome.get_outer_html('ClassName', 'scaledImageFitWidth img')[0]),
							account['path'],
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
			if html != None:
				for i in rfindall('ajaxify="https://www\.facebook\.com/photo\.php?[^"]*"', html):	# loop through photos
					if self.chrome.stop_check():
						return
					self.navigate(i[9:-1])
					self.chrome.rm_outer_html_by_id('photos_snowlift')	# show page with comments
					path_no_ext = self.storage.modpath(account['path'], '%05d_photo' % cnt)
					self.rm_pagelets()	# remove bluebar etc.
					self.expand_page(
						path_no_ext=path_no_ext,
						limit=self.options['limitPhotos'],
						expand=self.options['expandPhotos'],
						translate=self.options['translatePhotos']
					)
					self.chrome.page_pdf(path_no_ext)
					try:
						self.storage.download(
							self.ct.src(self.chrome.get_outer_html('ClassName', 'scaledImageFitWidth img')[0]),
							account['path'],
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
		if account['type'] == 'profile':
			self.navigate('%s/friends' % account['link'])
			path_no_ext = self.storage.modpath(account['path'], 'friends')
			self.rm_pagelets()	# remove bluebar etc.
			self.rm_left()
			self.chrome.expand_page(path_no_ext=path_no_ext)	# no limit for friends - it makes no sense not getting all friends
			self.chrome.page_pdf(path_no_ext)
			html = self.chrome.get_inner_html_by_id('pagelet_timeline_medley_friends')	# try to get friends
			if html == None:
				return []	# return empty list if no visible friends
			flist = []	# list to store friends
			for i in rfindall(' href="https://www\.facebook\.com\/[^<]+=friends_tab" [^<]+</a>', html):	# get the links to friends
				friend = self.link2account(i)
				if friend != None:
					flist.append(friend)	# append to friend list if info was extracted
			self.storage.write_2d([ [ i[j] for j in self.ACCOUNT] for i in flist ], account['path'], 'friends.csv')
			self.storage.write_json(flist, account['path'], 'friends.json')
			return { i['path'] for i in flist }	# return friends as set
		if account['type'] == 'groups':
			self.navigate('%s/members' % account['link'])
			path_no_ext = self.storage.modpath(account['path'], 'members')
			self.rm_pagelets()	# remove bluebar etc.
			self.rm_right()
			self.chrome.set_x_left()
			self.chrome.expand_page(path_no_ext=path_no_ext)	# no limit for friends - it makes no sense not getting all friends
			self.rm_left()
			self.chrome.page_pdf(path_no_ext)
			html = self.chrome.get_inner_html_by_id('groupsMemberBrowser')	# try to get members
			if html == None:
				return []	# return empty list if no visible friends
			mlist = []	# list to store friends
			for i in rfindall(' href="https://www\.facebook\.com\/[^<]+location=group" [^<]+</a>', html):	# regex vs facebook
				member = self.link2account(i)
				if member != None:
					mlist.append(member)	# append to friend list if info was extracted
			self.storage.write_2d([ [ i[j] for j in self.ACCOUNT] for i in mlist ], account['path'], 'members.csv')
			self.storage.write_json(mlist, account['path'], 'members.json')
			return { i['path'] for i in mlist }	# return members as set
		return set()

	def get_visitors(self, account):
		'Get all visitors who left comments or likes etc. in timeline - timeline has to be open end expand'
		self.get_timeline(account)
		visitors = []	# list to store links to other profiles
		visitor_ids = {account['id']}	# create set to store facebook ids of visitors to get uniq visitors
		items = self.chrome.get_outer_html('ClassName', 'commentable_item')	# get commentable items
		for i in items:
			for j in rfindall('<a class="[^"]+" data-hovercard="/ajax/hovercard/user\.php\?id=[^"]+" href="[^"]+"[^>]*>[^<]+</a>', i):	# get comment authors
				visitor = self.link2account(j)
				if not visitor['id'] in visitor_ids:	# uniq
					visitors.append(visitor)
					visitor_ids.add(visitor['id'])
			href = self.ct.search('href="/ufi/reaction/profile/browser/[^"]+', i)		# get reactions
			if href != None:
				if self.chrome.stop_check():
					return
				self.navigate('https://www.facebook.com' + href[6:])	# open reaction page
				self.chrome.expand_page(terminator=self.terminator)	# scroll through page
				self.rm_pagelets()	# remove bluebar etc.
				html = self.chrome.get_inner_html_by_id('content')	# get the necessary part of the page
				for j in rfindall(
					' href="https://www\.facebook\.com/[^"]+" data-hovercard="/ajax/hovercard/user\.php\?id=[^"]+" data-hovercard-prefer-more-content-show="1"[^<]+</a>',
					html
				):
					visitor = self.link2account(j)
					if visitor != None and not visitor['id'] in visitor_ids:	# uniq
						visitors.append(visitor)
						visitor_ids.add(visitor['id'])
		self.storage.write_2d([ [ i[j] for j in self.ACCOUNT ] for i in visitors ], account['path'], 'visitors.csv')
		self.storage.write_json(visitors, account['path'], 'visitors.json')
		return { i['path'] for i in visitors }	# return visitors ids as set

	def add2network(self, account, final=False):
		'Add account with friends (and visitorson extendNetwork) to network'
		self.network.update({account['path']: {	# add new account
			'id': account['id'],
			'type': account['type'],
			'name': account['name'],
			'link': account['link'],
			'friends': set(),
			'visitors': set()
		}})
		if final or self.stop_check():	# on last recusion level do not get the friend lists anymore
			return set()
		friends = self.get_friends(account)
		self.network[account['path']]['friends'] = friends
		if not self.options['extendNetwork']:
			return friends
		visitors = self.get_visitors(account)
		self.network[account['path']]['visitors'] = visitors
		return friends | visitors

	def get_network(self, targets):
		'Get friends and friends of friends and so on to given depth or abort if limit is reached'	
		if self.options['extendNetwork']:	# on extendNetwork no extra timeline visit is needed
			self.options['Timeline'] = False
		accounts = {}	# set of the targeted accounts as return value for further action
		self.network = dict()	# dictionary to store friend lists
		old_profs = set()	# set to store profiles  that already got handled
		all_profs = set() # set for all profiles
		for i in targets:	# first get landing pages and account data of the targets
			if self.stop_check():
				break
			self.logger.debug('Facebook: Network: 1st loop, target: %s' % i)
			account = self.get_landing(i)
			accounts[i] = account	# to return later
			old_profs.add(account['path'])	# update set of already handled profiles
			all_profs |= self.add2network(account)
		if self.options['depthNetwork'] < 1:	# on 0 only get friend list(s)
			self.logger.debug('Facebook: Network: done after fetching friend list(s)')
			return accounts
		landing_cnt = 0	# to re-login after getting only landings to avoid blocking by facebook
		for i in range(self.options['depthNetwork']):	# stay in depth limit and go through friend lists
			profile_cnt = 0
			new_profs = all_profs - old_profs	# friend list which have not been handled so far
			sum_new_profs = len(new_profs)
			for j in new_profs:	# work on new friends
				if self.stop_check():
					break
				profile_cnt += 1
				self.logger.info('Facebook: Network recursion level %d of %d, account %d of %d' % (
					i+1,
					self.options['depthNetwork'],
					profile_cnt,
					sum_new_profs
				))
				account = self.get_landing(j)
				if self.stop_check():
					break
				old_profs.add(account['path'])	# update set of already handled profiles
				if i == self.options['depthNetwork'] - 1:	# on last recusion level do not get the friend lists anymore
					all_profs |= self.add2network(account, final=True)
					landing_cnt += 1
					if landing_cnt == self.NEWLOGINAFTER:
						self.login()
						landing_cnt = 0
				else:
					all_profs |= self.add2network(account)
		netvis = NetVis(self.storage)	# create network visualisation object
		friend_edges = set()	# generate edges for facebook friends excluding doubles
		for i in self.network:
			netvis.add_node(
				i,
				image = '../%s/profile.jpg' % i,
				alt_image = './pixmaps/profile.jpg',
				label = self.network[i]['name'],
				title = '<img src="../%s/account.png" alt="%s" style="width: 24em;"/>' % (i, i)
			)
			for j in self.network[i]['friends']:
				if not '%s %s' % (i, j) in friend_edges:
					friend_edges.add('%s %s' % (j, i))
		for i in friend_edges:
			ids = i.split(' ')
			netvis.add_edge(ids[0], ids[1])
		if self.options['extendNetwork']:	# on extended create edges for the visitors as arrows
			visitor_edges = { '%s %s' % (j, i) for i in self.network for j in self.network[i]['visitors'] }
			for i in visitor_edges:
				ids = i.split(' ')
				netvis.add_edge(ids[0], ids[1], arrow=True, dashes=True)
		netvis.write(doubleclick="window.open('../' + params.nodes[0] + '/account.html')")
		return accounts
