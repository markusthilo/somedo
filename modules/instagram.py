#!/usr/bin/env python3

from re import sub as rsub
from re import findall as rfindall
from time import sleep
from datetime import datetime
from base.cutter import Cutter
from base.logger import DEBUG

class Instagram:
	'Downloader for Instagram'

	DEFAULTPAGELIMIT = 20

	def __init__(self, job, storage, chrome, stop=None):
		'Generate object for Instagram'
		self.storage = storage
		self.chrome = chrome
		self.ct = Cutter()
		self.logger = self.storage.logger
		self.options = job['options']
		self.chrome.open(stop=stop)
		for i in self.extract_targets(job['target']):
			self.get_main(i)
		if self.logger.level < DEBUG:
			self.logger.visible('Instagram: finished, now sleeping for 5 seconds until closing browser')
			sleep(5)
		self.chrome.close()
		self.logger.debug('Facebook: done!')

	def extract_targets(self, target):
		'Extract paths (= URLs without ...instagram.com/) from given targets'
		l= []	# list for the target users (id or path)
		for i in self.ct.split(target):
			i = rsub('^.*instagram\.com/', '', i)
			i = rsub('/.*$', '', i)
			if i != '' and i != 'p':
				l.append(i)
		return l

	def rm_banner(self):
		'Remove redundant parts of the page'
		self.chrome.rm_outer_html('TagName', 'nav')
		self.chrome.rm_outer_html('TagName', 'footer')

	def get_main(self, path):
		'Scroll through main page and get images'
		self.chrome.navigate('http://www.instagram.com/%s' % path)
		sleep(0.5)
		try:
			name = self.chrome.get_inner_html('TagName', 'h1')[0]
		except:
			name = 'Undetected'
		self.storage.mksubdir(path)
		self.storage.write_str('%s\thttp://www.instagram.com/%s' % (name, path), path, 'account.csv')	# write information as file
		self.storage.write_json({'name': name, 'link': 'http://www.instagram.com/%s' % path}, path, 'account.json')	# write as json file
		try:	# try to download profile picture
			url = self.ct.src(self.chrome.get_outer_html('TagName', 'img')[0])
			self.storage.download(url, path, 'profile' + self.ct.ext(url))	# download media file using the right file extension
		except:
			pass
		self.rm_banner()
		self.chrome.set_x_center()
		self.links = []
		path_no_ext = self.storage.modpath(path, 'main')
		self.chrome.expand_page(	# scroll through page and take screenshots
			path_no_ext = path_no_ext,
			per_page_action = self.get_links,
			limit = self.options['limitPages']
		)
		minfo = []	# list for media info
		cnt = 1	# counter for the images/videos
		for i in self.links:	# go through links
			if self.chrome.stop_check():
				break
			self.chrome.navigate('http:www.instagram.com/%s' % i)
			sleep(0.2)
			self.rm_banner()
			store_path = self.storage.modpath(path, '%05d_page' % cnt)
			self.chrome.visible_page_png(store_path)	# save page as png
			self.chrome.page_pdf(store_path)	# save as pdf
			self.storage.write_text(self.chrome.get_inner_html('TagName', 'article')[0], path, '%05d_page.txt' % cnt)	# write comments
			if self.options['Media']:
				tags = self.chrome.get_outer_html('TagName', 'video')
				if tags != []:
					url = self.ct.src(tags[0])
					ftype = 'video'
				else:
					tags = self.chrome.get_outer_html('TagName', 'img')
					if len(tags) == 1:
						url = self.ct.src(tags[0])
						ftype = 'image'
					elif len(tags) > 1:
						url = self.ct.src(tags[1])
						ftype = 'image'
					else:
						ftype = None
				if ftype != None:
					fname = '%05d_%s%s' % (cnt, ftype, self.ct.ext(url))
					try:
						self.storage.download(url, path, fname)	# try to download media file
						minfo.append({	# store counter, media type and url to media info list
							'type': ftype,
							'file':	fname,
							'time':	datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
							'url':	url
						})
					except:
						pass
			cnt += 1
			if minfo != []:
				self.storage.write_dicts(minfo,('type', 'file','time','url'), path , 'media.csv')
				self.storage.write_json(minfo, path, 'media.json')

	def get_links(self):
		'Extract links from tag "article"'
		try:
			for i in rfindall('<a href="/p/[^"]+', self.chrome.get_outer_html('TagName', 'article')[0]):	# go through links
				if not i[9:] in self.links:
					self.links.append(i[9:])
		except:
			pass
