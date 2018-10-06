#!/usr/bin/env python3

import re, time, datetime

class Instagram:
	'Downloader for Instagram'

	DEFINITION = ['Instagram', [],	[] ]

	def __init__(self, target, options, login, chrome, storage):
		'Generate object for Instagram'
		self.storage = storage
		self.chrome = chrome
		for i in self.extract_targets(target):
			self.get_main(i)

	def extract_targets(self, target):
		'Extract paths (= URLs without ...instagram.com/) from given targets'
		l= []	# list for the target users (id or path)
		for i in target.split(';'):
			i = re.sub('^.*instagram\.com/', '', i)
			i = re.sub('/.*$', '', i)
			i = i.lstrip(' ').rstrip(' ')
			if i != '' and i != 'p':
				l.append(i)
		return l

	def rm_banner(self):
		'Remove redundant parts of the page'
		self.chrome.rm_outer_html('TagName', 'nav')
		self.chrome.rm_outer_html('TagName', 'footer')

	def get_main(self, path):
		'Scroll through main page and get images'
		self.chrome.navigate('http:www.instagram.com/%s' % path)
		time.sleep(0.5)
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
		self.chrome.drive_by_png(	# scroll through page and take screenshots
			path_no_ext = self.storage.path('main', path),
			per_page_action = self.get_links
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

	def get_links(self):
		'Extract links from tag "article"'
		for i in re.findall('<a href="/p/[^"]+', self.chrome.get_outer_html('TagName', 'article')[0]):	# go through links
			if not i[9:] in self.links:
				self.links.append(i[9:])

	def cut_ext(self, url):
		'Cut file extension out of media URL'
		try:
			ext = re.findall('\.[^.]+$', re.sub('\?.*$', '', url))[-1]
		except:
			ext = ''
		return ext
