#!/usr/bin/env python3

from os import name as os_name
from os import path as os_path
from time import sleep
from json import loads as jloads
from json import dumps as jdumps
from subprocess import Popen
from socket import socket, AF_INET, SOCK_STREAM
from requests import get as rq_get
from requests import exceptions as rq_exceptions
from websocket import create_connection
from base64 import b64decode
from re import findall
from base.logger import DEBUG

class Chrome:
	'Class around the Chrome/Chromium using the Developers Tools'

	SCROLL_RATIO = 0.85	# ratio to scroll in relation to window/screenshot height
	DEFAULT_PAGE_LIMIT = 100	# default limit for page expansion
	DEFAULT_WINDOW_WIDTH = 1024	# default chrome/chromium window width
	DEFAULT_WINDOW_HEIGHT = 1280	# default window height

	def __init__(self, logger, path=None, port=None):
		'Create object. It is possible to give the path to the Chrome/Chromium.'
		self.logger = logger
		if path == None or path == '':	# set path to chrome/chromium
			if os_name == 'nt':
				self.path = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
			else:
				self.path = ''
				for i in [
					'google-chrome',
					'/usr/bin/chromium',
					'/usr/bin/chromium-browser',
					'/usr/bin/google-chrome'
				]:
					if os_path.isfile(i):
						self.path = i
						break
		if not os_path.isfile(self.path):
			self.path = None
		if port == None:	# set port
			self.port = 9222
			while self.port <= 10222:
				with socket(AF_INET, SOCK_STREAM) as so:	# check if port is unused
					if so.connect_ex(('localhost', self.port)) != 0:
						return
				self.port += 1
		else:
			with socket(AF_INET, SOCK_STREAM) as so:	# check if given port is unused
				if so.connect_ex(('localhost', port)) == 0:
					raise Exception('Port %d is in use' % port)
			self.port = port
			return
		raise Exception('Could not find an unused port to control Chrome/Chromium')

	def open(self, window_width=DEFAULT_WINDOW_WIDTH, window_height=DEFAULT_WINDOW_HEIGHT, stop=None):
		'Open Chrome/Chromium session'
		if self.is_running():
			self.logger.debug('Closing Chrome/Chromium')
			self.close()
		cmd = [	# chrome with parameters
			self.path,
			'--window-size=%d,%d' % (window_width, window_height),	# try to set windows dimensions - might not work right now
			'--remote-debugging-port=%d' % self.port,
			'--incognito',
			'--disable-gpu'	# might be needed for windows
		]
		self.stop = stop	# to abort if user hits the stop button
		if self.logger.level >= DEBUG:	# start invisble/headless if desired (default)
			cmd.append('--headless')
		self.logger.debug('Starting Chrome/Chromium with: %s' % cmd)
		self.chrome_proc = Popen(cmd)	# start chrome browser
		for i in range(100):	# connect to chrome (try 10 seconds before throwing error)
			try:
				response = rq_get('http://127.0.0.1:%d/json' % self.port).json()
				self.conn = create_connection(response[0]['webSocketDebuggerUrl'])
				self.request_id = 0
				self.x = 0
				self.logger.info('Chrome/Chromium is running and listening on port %d' % self.port)
				return
			except rq_exceptions.ConnectionError:
				sleep(0.1)
		raise Exception('Unable to connect to Chrome')

	def close(self):
		'Close session/browser'
		self.chrome_proc.kill()
		for i in range(600):
			if self.chrome_proc.poll() != None:
				return
			sleep(0.1)
		raise Exception('Unable to close Chrome/Chromium')

	def is_running(self):
		'Check if Chrome/Chromium is running'
		try:
			if self.chrome_proc.poll() == None:
				return True
		except:
			pass
		return False

	def send_cmd(self, method, **kwargs):
		'Send command to Chrome'
		self.request_id += 1
		self.conn.send(jdumps({'method': method, 'id': self.request_id, 'params': kwargs}))	# send command
		for i in range(100000):	# wait for response
			message = jloads(self.conn.recv())
			if message.get('id') == self.request_id:
				return message
			if i > 600:
				sleep(0.1)
		return None

	def runtime_eval(self, js):
		'Send JavaScript code with method Runtume.evaluate to Chrome'
		message = self.send_cmd('Runtime.evaluate', expression=js)
		try:
			return jloads(message['result']['result']['value'])
		except:
			return None

	def navigate(self, url):
		'Go to URL'
		self.send_cmd('Page.navigate', url=url)
		sleep(2)
		self.wait_expand_end()

	def go_back(self):
		'Go to previous page'
		self.runtime_eval('window.history.go(-1)')
		sleep(1)
		self.wait_expand_end()

	def click_elements(self, element_type, selector):
		'Click all elements by given type and selector'
		return int(self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			for (var i=0; i<elements.length; i++) { elements[i].click() }
			JSON.stringify(elements.length);
		''' % (element_type, selector)))

	def click_element(self, element_type, selector, n):
		'Click one elements by given type, selector and number'
		self.runtime_eval('document.getElementsBy%s("%s")[%d].click()' % (element_type, selector, n))

	def click_element_by_id(self, selector):
		'Click elements by given ID'
		self.runtime_eval('document.getElementById("%s").click()' % selector)

	def insert_element(self, element_type, selector, n, value):
		'Insert value into one element by given type, selector and number'
		self.runtime_eval('document.getElementsBy%s("%s")[%d].value = "%s"' % (element_type, selector, n, value))

	def insert_element_by_id(self, selector, value):
		'Insert value into element selected by ID'
		self.runtime_eval('document.getElementById("%s").value = "%s"' % (selector, value))

	def get_outer_html(self, element_type, selector):
		'Get outerHTML of elements as a list'
		return self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			var html = new Array();
			for (var i=0; i<elements.length; i++) { html.push(elements[i].outerHTML) }
			JSON.stringify(html);
		''' % (element_type, selector))

	def get_outer_html_by_id(self, selector):
		'Get outerHTML of element selected by ID'
		return self.runtime_eval('JSON.stringify(document.getElementById("%s").outerHTML)' % selector)

	def get_inner_html(self, element_type, selector):
		'Get innerHTML of elements as a list'
		return self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			var html = new Array();
			for (var i=0; i<elements.length; i++) { html.push(elements[i].innerHTML) }
			JSON.stringify(html);
		''' % (element_type, selector))

	def get_inner_html_by_id(self, selector):
		'Get innerHTML of element selected by ID'
		return self.runtime_eval('JSON.stringify(document.getElementById("%s").innerHTML)' % selector)

	def rm_outer_html(self, element_type, selector):
		'Remove outerHTML of all elements by given type and selector'
		self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			for (var i=0; i<elements.length; i++) { elements[i].outerHTML = "" }
		''' % (element_type, selector))

	def rm_inner_html(self, element_type, selector):
		'Remove innerHTML of all elements by given type and selector'
		self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			for (var i=0; i<elements.length; i++) { elements[i].innerHTML = "" }
		''' % (element_type, selector))

	def rm_outer_html_by_id(self, selector):
		'Remove outerHTML of element selected by ID'
		self.runtime_eval('document.getElementById("%s").outerHTML = ""' % selector)

	def rm_inner_html_by_id(self, selector):
		'Remove innerHTML of element selected by ID'
		self.runtime_eval('document.getElementById("%s").innerHTML = ""' % selector)

	def rm_outer_html_by_regex_id(self, base_id, regex_id, lcut, rcut):
		'Remove all outerHTML/elements by matching ids'
		for i in findall(regex_id, self.get_outer_html_by_id(base_id)):
			self.rm_outer_html_by_id(i[lcut:rcut])

	def rm_inner_html_by_regex_id(self, base_id, regex_id, lcut, rcut):
		'Remove all innerHTML/elements by matching ids'
		for i in findall(regex_id, self.get_outer_html_by_id(base_id)):
			self.rm_inner_html_by_id(i[lcut:rcut])

	def set_outer_html(self, element_type, selector, n, html):
		'Set outerHTML of element n'
		self.runtime_eval('document.getElementsBy%s("%s")[%d].outerHTML = "%s"' % (element_type, selector, n, html))

	def set_outer_html_by_id(self, selector, html):
		'Set outerHTML of element selected by ID'
		self.runtime_eval('document.getElementById("%s").outerHTML = "%s"' % (selector, html))

	def set_inner_html(self, element_type, selector, n, html):
		'Set innerHTML of element n'
		self.runtime_eval('document.getElementsBy%s("%s")[%d].innerHTML = "%s"' % (element_type, selector, n, html))

	def set_inner_html_by_id(self, selector, html):
		'Set innerHTML of element selected by ID'
		self.runtime_eval('document.getElementById("%s").innerHTML = "%s"' % (selector, html))

	def get_window_height(self):
		'Get visible height of the window'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(window.innerHeight)'))
			except TypeError:
				sleep(0.1)
		raise Exception('Could not get window height.')

	def get_window_width(self):
		'Get visible height of the window'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(window.innerWidth)'))
			except TypeError:
				sleep(0.1)
		raise Exception('Could not get window width.')

	def get_page_height(self):
		'Get page height'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(document.body.scrollHeight)'))
			except TypeError:
				sleep(0.1)
		raise Exception('Could not get page height.')

	def get_page_width(self):
		'Get page width'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(document.body.scrollWidth)'))
			except TypeError:
				sleep(0.1)
		raise Exception('Could not get page width.')

	def get_x_position(self):
		'Get x scroll position'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(document.body.scrollLeft)'))
			except TypeError:
				sleep(0.1)
		raise Exception('Could not get x position.')

	def get_y_position(self):
		'Get y scroll position'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(document.body.scrollTop)'))
			except TypeError:
				sleep(0.1)
		raise Exception('Could not get page y position.')

	def set_position(self, y):
		'Scroll to given position - x has to be stored in object'
		self.runtime_eval('window.scrollTo(%d, %d);' % (self.x, y))

	def set_x_left(self):
		'Horizontally focus to left of page an go to top'
		self.x = 0

	def set_x_right(self):
		'Horizontally focus to right of page an go to top'
		self.x = self.get_page_width() - self.get_window_width()

	def set_x_center(self):
		'Horizontally focus to center of page an go to top'
		self.x = self.get_page_width() - int( self.get_window_width() / 2 )

	def get_scroll_height(self):
		'Calculate scroll height based on the window height'
		return int(self.get_window_height() * self.SCROLL_RATIO)

	def download(self, url, path):
		'Download file'
		self.runtime_eval('''
			var a = document.createElement('a');
			a.href = "%s";
			a.download = "%s";
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
		''' % (url, path))

	def page_pdf(self, path_no_ext):
		'Save page to pdf'
		if self.logger.level >= DEBUG:
			try:
				with open('%s.pdf' % path_no_ext, 'wb') as f:
					f.write(b64decode(self.send_cmd('Page.printToPDF')['result']['data']))
			except:
				pass

	def stop_check(self, terminator=None):
		'Check if User wants to abort running task'
		try:
			return self.stop.isSet()
		except:
			return False

	def wait_expand_end(self):
		'Wait for page not expanding anymore'
		sleep(0.2)
		old_height = self.get_page_height()
		for i in range(5000):
			sleep(0.1)
			new_height = self.get_page_height()
			if new_height == old_height:
				return new_height
			old_height = new_height

	def visible_page_png(self, path_no_ext):
		'Take screenshot of the visible area of the web page'
		if path_no_ext == '':	# no screenshot on empty path
			return
		try:
			with open('%s.png' % path_no_ext, 'wb') as f:
				f.write(b64decode(self.send_cmd('Page.captureScreenshot', format='png')['result']['data']))
		except:
			raise Exception('Unable to save visible part of page as PNG')

	def entire_page_png(self, path_no_ext):
		'Take screenshots of the entire page by scrolling through'
		self.wait_expand_end()	# do not start while page is still expanding
		self.set_position(0) 	# go to top of page
		page_height = self.get_page_height()
		scroll_height = self.get_scroll_height()
		if scroll_height >= page_height:	# just one screen
			self.visible_page_png(path_no_ext)	# store screenshot
		else:	# multiple screenshots
			cnt = 1	# counter to number shots
			for y in range(0, self.get_page_height(), self.get_scroll_height()):
				self.set_position(y) 	# scroll down
				self.visible_page_png('%s_%05d' % (path_no_ext, cnt))	# store screenshot
				cnt += 1	# increase counter
				if cnt == 100000:	# 99999 screenshots max
					return

	def execute_per_page(self, actions):
		'Execute this on each visible page'
		if actions != None or actions != []:
			for i in actions:
				if i():
					return True
		return False

	def expand_page(self, path_no_ext='', per_page_actions=[], limit=DEFAULT_PAGE_LIMIT):
		'Expand page by scrolling and optional clicking. If path is given, screenshots are taken on the way.'
		self.wait_expand_end()	# do not start while page is still expanding
		scroll_height = self.get_scroll_height()
		view_height = self.get_window_height()
		old_y = 0	# vertical position
		old_height = self.get_page_height()	# to check if page is still expanding
		if limit < 1:
			limit = 1
		cnt = 0
		while True:
			if self.stop_check():
				break
			cnt += 1
			self.set_position(old_y)
			if self.execute_per_page(per_page_actions):	# execute per page actions
				break
			self.wait_expand_end()
			if cnt == limit:
				self.set_position(old_y)
				break
			new_y = old_y + scroll_height
			self.set_position(new_y) 	# scroll down
			new_height = self.wait_expand_end()	# get new height of page when expanding is over
			y_bottom = old_y + view_height
			if new_height <= old_height and y_bottom >= new_height:
				sleep(2)	# wait 2 seconds - page might load some more
				new_height = self.wait_expand_end()
				if new_height <= old_height and y_bottom >= new_height:	# check again
					break	# exit
			if path_no_ext != '':
				self.set_position(old_y)	# go back to old y in case expanding changed the position
				self.visible_page_png('%s_%05d' % (path_no_ext, cnt)) # store screenshot
			old_y = new_y
			old_height = new_height
		if path_no_ext != '':
			if cnt > 1:
				path_no_ext += '_%05d' % cnt
			self.visible_page_png(path_no_ext) # store screenshot
