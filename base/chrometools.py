#!/usr/bin/env python3

import os
import time
import json
import subprocess
import requests
from websocket import create_connection
from base64 import b64decode

class Chrome:
	'Tools around the Chromedriver'

	SCROLL_RATIO = 0.85	# ratio to scroll in relation to window/screenshot height

	def __init__(self, path=None, port=9222, headless=True, stop=None, window_width=960, window_height=1040, debug=False):
		'Open Chrome session'
		self.debug = debug
		if path == None or not os.path.isfile(path):
			cp = ChromePath()	# find chrome browser
			path = cp.path
		chrome_cmd = [	# chrome with parameters
			path,
			'--window-size=%d,%d' % (window_width, window_height),	# try to set windows dimensions - might not work right now
			'--remote-debugging-port=%d' % port,
			'--incognito',
			'--disable-gpu'	# might be needed for windows
		]
		if headless:	# start invisble/headless if desired (default)
			chrome_cmd.append('--headless')
		self.headless = headless
		self.stop = stop	# to abort if user hits the stop button
		self.chrome_proc = subprocess.Popen(chrome_cmd)	# start chrome browser
		wait_seconds = 10.0
		while wait_seconds > 0:	# connect to chrome
			try:
				response = requests.get('http://127.0.0.1:%d/json' % port).json()
				self.conn = create_connection(response[0]['webSocketDebuggerUrl'])
				self.request_id = 0
				self.x = 0
				return
			except requests.exceptions.ConnectionError:
				time.sleep(0.25)
				wait_seconds -= 0.25
		raise Exception('Unable to connect to Chrome')

	def send_cmd(self, method, **kwargs):
		'Send command to Chrome'
		self.request_id += 1
		self.conn.send(json.dumps({'method': method, 'id': self.request_id, 'params': kwargs}))	# send command
		for i in range(100000):	# wait for response
			message = json.loads(self.conn.recv())
			if message.get('id') == self.request_id:
				return message
			if i > 1000:
				time.sleep(0.1)
		return None

	def runtime_eval(self, js):
		'Send JavaScript code with method Runtume.evaluate to Chrome'
		message = self.send_cmd('Runtime.evaluate', expression=js)
		try:
			return json.loads(message['result']['result']['value'])
		except:
			return None

	def navigate(self, url):
		'Go to URL'
		self.send_cmd('Page.navigate', url=url)
		time.sleep(2)
		self.wait_expand_end()

	def go_back(self):
		'Go to previous page'
		self.runtime_eval('window.history.go(-1)')
		time.sleep(1)
		self.wait_expand_end()

	def click_elements(self, element_type, selector):
		'Click all elements by given type and selector'
		return int(self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			for (var i=0;i<elements.length; i++) { elements[i].click() }
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
			for (var i=0;i<elements.length; i++) { html.push(elements[i].outerHTML) }
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
			for (var i=0;i<elements.length; i++) { html.push(elements[i].innerHTML) }
			JSON.stringify(html);
		''' % (element_type, selector))

	def get_inner_html_by_id(self, selector):
		'Get innerHTML of element selected by ID'
		return self.runtime_eval('JSON.stringify(document.getElementById("%s").innerHTML)' % selector)

	def rm_outer_html(self, element_type, selector):
		'Remove outerHTML of all elements by given type and selector'
		self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			for (var i=0;i<elements.length; i++) { elements[i].outerHTML = "" }
		''' % (element_type, selector))

	def rm_inner_html(self, element_type, selector):
		'Remove innerHTML of all elements by given type and selector'
		self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			for (var i=0;i<elements.length; i++) { elements[i].innerHTML = "" }
		''' % (element_type, selector))

	def rm_outer_html_by_id(self, selector):
		'Remove outerHTML of element selected by ID'
		self.runtime_eval('document.getElementById("%s").outerHTML = ""' % selector)

	def rm_inner_html_by_id(self, selector):
		'Remove innerHTML of element selected by ID'
		self.runtime_eval('document.getElementById("%s").innerHTML = ""' % selector)

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
				time.sleep(0.1)
		raise Exception('Could not get window height.')

	def get_window_width(self):
		'Get visible height of the window'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(window.innerWidth)'))
			except TypeError:
				time.sleep(0.1)
		raise Exception('Could not get window width.')

	def get_page_height(self):
		'Get page height'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(document.body.scrollHeight)'))
			except TypeError:
				time.sleep(0.1)
		raise Exception('Could not get page height.')

	def get_page_width(self):
		'Get page width'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(document.body.scrollWidth)'))
			except TypeError:
				time.sleep(0.1)
		raise Exception('Could not get page width.')

	def get_x_position(self):
		'Get x scroll position'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(document.body.scrollLeft)'))
			except TypeError:
				time.sleep(0.1)
		raise Exception('Could not get x position.')

	def get_y_position(self):
		'Get y scroll position'
		for i in range(600):
			try:
				return int(self.runtime_eval('JSON.stringify(document.body.scrollTop)'))
			except TypeError:
				time.sleep(0.1)
		raise Exception('Could not get page y position.')

	def set_position(self, y):
		'Scroll to given position - x has to be stored in object'
		self.runtime_eval('window.scrollTo(%d, %d);' % (self.x, y))

	def set_x_left(self):
		'Horizontally focus to left of page an go to top'
		self.x = 0
		self.set_position(0)

	def set_x_right(self):
		'Horizontally focus to right of page an go to top'
		self.x = self.get_page_width() - self.get_window_width()
		self.set_position(0)

	def set_x_center(self):
		'Horizontally focus to center of page an go to top'
		self.x = self.get_page_width() - int( self.get_window_width() / 2 )
		self.set_position(0)

	def get_scroll_height(self):
		'Calculate scroll height based on the window height'
		return int(self.get_window_height() * self.SCROLL_RATIO)

	def close(self):
		'Close session/browser'
		self.chrome_proc.kill()

	def page_pdf(self, path_no_ext):
		'Save page to pdf'
		if not self.headless:	# only works with --headless according to the google developers
			return
		try:
			with open('%s.pdf' % path_no_ext, 'wb') as f:
				f.write(b64decode(self.send_cmd('Page.printToPDF')['result']['data']))
		except:
			raise Exception('Unable to save page as PDF')

	def stop_check(self, terminator=None):
		'Check if User wants to abort running task'
		try:
			return self.stop.isSet()
		except:
			return False

	def __terminator_check__(self):
		'Check criteria to abort extraction'
		try:
			return self.terminator()
		except:
			return False

	def wait_expand_end(self):
		'Wait for page not expanding anymore'
		time.sleep(0.2)
		old_height = self.get_page_height()
		for i in range(5000):
			time.sleep(0.1)
			new_height = self.get_page_height()
			if new_height == old_height:
				return new_height
			old_height = new_height

	def click_page(self, click_elements_by):
		'Clicking on elements stored in a list of lists: e.g. [["ClassName", "UFIPagerLink"], ["ClassName", "UFICommentLInk"]]'
		if click_elements_by != None:	# do not click if no elements are given
			for i in range(5):	# try several times to click on all elements
				for j in click_elements_by:	# go throught dictionary containing pairs of element type and selector
					self.click_elements(j[0], j[1])
		return self.wait_expand_end()

	def __per_page__(self, per_page_action):
		'Execute this function on every visible page'
		if per_page_action != None:
			per_page_action()

	def visible_page_png(self, path_no_ext):
		'Take screenshot of the visible area of the web page'
		if path_no_ext == '':	# no screenshot on empty path
			return
		try:
			with open('%s.png' % path_no_ext, 'wb') as f:
				f.write(b64decode(self.send_cmd('Page.captureScreenshot', format='png')['result']['data']))
		except:
			raise Exception('Unable to save visible part of page as PNG')
		return

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

	def expand_page(self, path_no_ext='', click_elements_by=[], terminator=None, per_page_action=None, limit=200):
		'Expand page by scrolling and optional clicking. If path is given, screenshots are taken on the way.'
		self.terminator = terminator
		self.wait_expand_end()	# do not start while page is still expanding
		scroll_height = self.get_scroll_height()
		view_height = self.get_window_height()
		old_y = 0	# vertical position
		old_height = self.get_page_height()	# to check if page is still expanding
		cnt = 1
		print('############## limit:', limit)
		while cnt < limit:
			self.set_position(old_y)
			if self.stop_check() or self.__terminator_check__():
				break
			self.click_page(click_elements_by)	# expand page by clicking on elments
			self.__per_page__(per_page_action)	# execute per page action
			self.wait_expand_end()
			new_y = old_y + scroll_height
			self.set_position(new_y) 	# scroll down
			new_height = self.wait_expand_end()	# get new height of page when expanding is over
			y_bottom = old_y + view_height
			if new_height <= old_height and y_bottom >= new_height:
				time.sleep(2)	# wait 2 seconds - page might load some more
				new_height = self.wait_expand_end()
				if new_height <= old_height and y_bottom >= new_height:	# check again
					break	# exit
			if path_no_ext != '':
				self.set_position(old_y)	# go back to old y in case expanding changed the position
				self.visible_page_png('%s_%05d' % (path_no_ext, cnt)) # store screenshot
				cnt += 1
			old_y = new_y
			old_height = new_height
		if path_no_ext != '':
			if cnt > 1:
				path_no_ext += '_%05d' % cnt
			self.visible_page_png(path_no_ext) # store screenshot

class ChromePath:
	'Set the path to Chrome/Chromium'

	def __init__(self, *args):
		'Open web session. It is possible to give the path to the Chrome/Chromium.'
		if len(args) == 1 and isinstance(args[0], str):
			self.path = args[0]
		elif len(args) == 0:
			if os.name == 'nt':
				self.path = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
				if not os.path.isfile(self.path):
					raise FileNotFoundError('Did not find Chrome.')
			else:
				self.path = ''
				for i in [
					'google-chrome',
					'/usr/bin/chromium',
					'/usr/bin/chromium-browser',
					'/usr/bin/google-chrome'
				]:
					if os.path.isfile(i):
						self.path = i
						break
				if self.path == '':
					raise FileNotFoundError('Did not find Chrome/Chromium.')
		else:
			raise Exception('The path to Chrome/Chromium is the only possible argument.')
