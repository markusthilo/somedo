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

	WINDOW_WIDTH = 640
	WINDOW_HEIGHT = 1040	# it seems, right now it is the limit for headless chrome
	SCROLL_HEIGHT = 960
	MAX_HEIGHT = 9999 * WINDOW_HEIGHT	# at 10000 screenshots you would run aut of counter if nothing else bad happened so far

	def __init__(self, path=None, port=9222, headless=False, stop=None):
		'Open Chrome session'
		if path == None:
			cp = ChromePath()	# find chrome browser
			path = cp.path
		chrome_cmd = [	# chrome with parameters
			path,
			'--remote-debugging-port=%d' % port,
			'--incognito',
			'--disable-gpu'	# might be needed for windows
		]
		if headless:	# start invisble/headless if desired
			chrome_cmd.append('--headless')
		else:	# this still don't work on headless chrome
			chrome_cmd.append('--window-size="%d,%d"' % (self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
		self.stop = stop	# to abort if user hits the stop button
		self.chrome_proc = subprocess.Popen(chrome_cmd)	# start chrome browser
		wait_seconds = 10.0
		while wait_seconds > 0:	# connect to chrome
			try:
				response = requests.get('http://127.0.0.1:%d/json' % port).json()
				self.conn = create_connection(response[0]['webSocketDebuggerUrl'])
				self.request_id = 0
#				self.send_cmd('DOM.enable')	# enable to interact with page
#				self.send_cmd('Network.enable')
#				self.runtime_eval('window.innerWidth = %d; window.innerHeight = %d' % (self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
#				self.runtime_eval('window.resizeTo(%d, %d)' % (self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
				if headless:		# found this on the net but it seems to do nothing
					self.send_cmd('''
						Page.setDeviceMetricsOverride({
							'width': %d,
							'height':%d,
							'deviceScaleFactor': 1,
							'mobile': false
						});
					''' % (self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
				return
			except requests.exceptions.ConnectionError:
				time.sleep(0.25)
				wait_seconds -= 0.25
		raise Exception('Unable to connect to Chrome')

	def send_cmd(self, method, **kwargs):
		'Send command to Chrome'
		self.request_id += 1
		self.conn.send(json.dumps({'method': method, 'id': self.request_id, 'params': kwargs}))	# send command
		while True:	# wait for response
			message = json.loads(self.conn.recv())
			if message.get('id') == self.request_id:
				return message

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
		time.sleep(1)
		self.wait_expand_end()

	def go_back(self):
		'Go to previous page'
		self.runtime_eval('window.history.go(-1)')
		time.sleep(1)
		self.wait_expand_end()

	def click_elements(self, element_type, selector):
		'Click all elements by given type and selector'
		return self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			for (var i=0;i<elements.length; i++) { elements[i].click() }
			JSON.stringify(elements.length);
		''' % (element_type, selector))

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
		return self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			for (var i=0;i<elements.length; i++) { elements[i].outerHTML = "" }
			JSON.stringify(elements.length);
		''' % (element_type, selector))

	def rm_inner_html(self, element_type, selector):
		'Remove innerHTML of all elements by given type and selector'
		return self.runtime_eval('''
			var elements = document.getElementsBy%s("%s");
			for (var i=0;i<elements.length; i++) { elements[i].innerHTML = "" }
			JSON.stringify(elements.length);
		''' % (element_type, selector))

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

	def get_height(self):
		'Get page height'
		return self.runtime_eval('JSON.stringify(document.body.scrollHeight)')

	def get_position(self):
		'Get scroll position'
		return self.runtime_eval('JSON.stringify(document.body.scrollTop)')

	def set_position(self, y):
		'Scroll to given position'
		self.runtime_eval('window.scrollTo(0, %s);' % y )

	def wait_expand_end(self):
		'Wait for page not expanding anymore'
		old_height = self.get_height()
		while True:
			time.sleep(0.1)
			new_height = self.get_height()
			if new_height == old_height:
				return new_height
			old_height = new_height

	def visible_page_png(self, path_no_ext):
		'Take screenshot of the visible area of the web page'
		try:
			with open('%s.png' % path_no_ext, 'wb') as f:
				f.write(b64decode(self.send_cmd('Page.captureScreenshot', format='png')['result']['data']))
		except:
			raise Exception('Unable to save visible part of page as PNG')

	def entire_page_png(self, path_no_ext):
		'Take screenshots of the entire page by scrolling through'
		self.wait_expand_end()	# do not start while page is still expanding
		cnt = 1	# counter to number shots
		for y in range(0, self.get_height(), self.SCROLL_HEIGHT):
			self.set_position(y) 	# scroll down
			self.visible_page_png('%s_%04d.png' % (path_no_ext, cnt))	# store screenshot
			cnt += 1	# increase counter

	def expand_page(self, click_elements_by=[], path_no_ext='', terminator=None):
		'Expand page by clicking and scrolling. If path is given, screenshots are taken on the way.'
		self.wait_expand_end()	# do not start while page is still expanding
		cnt = 1	# counter to number shots
		self.set_position(0)
		y = 0	# vertical position
		old_height = self.get_height()	# to check if page is still expanding
		while True:
			if click_elements_by != []:
				self.click_page(click_elements_by, y)
			self.wait_expand_end()	# do not start while page is still expanding
			if path_no_ext != '':
				self.visible_page_png('%s_%04d' % (path_no_ext, cnt))	# store screenshot
			cnt += 1
			y += self.SCROLL_HEIGHT
			self.set_position(y) 	# scroll down
			new_height = self.wait_expand_end()	# get new height of page when expanding is over
			if new_height <= old_height and new_height <= y + self.SCROLL_HEIGHT:	# check for end of page
				return	# exit if page did not change
			old_height = new_height
			if self.stop_check(terminator=terminator):	# chech for criteria to abort
				return

	def click_page(self, click_elements_by, y):
		'Expand page by clicking on elements stored in a list of lists: e.g. [["ClassName", "UFIPagerLink"], ["ClassName", "UFICommentLInk"]]'
		if click_elements_by == dict():	# do nothing if no elements to click are given
			return
		for i in range(5):	# try several times to click on all elements
			for j in click_elements_by:	# go throught dictionary containing pairs of element type and selector
				self.click_elements(j[0], j[1])
			time.sleep(0.1)	# give the page a brief short moment to react
			self.wait_expand_end()	# do not continue while page is still expanding
		self.set_position(y)	# go back to y because clicking might have changed the position in the page
		time.sleep(0.2)

	def page_pdf(self, path_no_ext):
		'Save page to pdf'
		try:	# right now pagetopdf does not work on my stable debian chrome
			with open('%s.pdf' % path_no_ext, 'wb') as f:
				f.write(b64decode(self.send_cmd('Page.printToPDF')))
		except:
			pass
#			raise Exception('Unable to save page as PDF')

	def stop_check(self, terminator=None):
		'Check if User wants to abort running task'
		if terminator != None:
			if terminator():
				return True
		if self.stop == None:
			return False
		try:
			return self.stop.isSet()
		except:
			return False

	def close(self):
		'Close session/browser'
		self.chrome_proc.kill()

class ChromePath:
	'Set the path to the Chromedriver for Selenium'

	def __init__(self, *args):
		'Open web session. It is possible to give the path to the Chromedriver.'
		if len(args) == 1 and isinstance(args[0], str):
			self.path = args[0]
		elif len(args) == 0:
			if os.name == 'nt':
				self.path = 'chrome.exe'
				if not os.path.isfile(self.path):
					raise FileNotFoundError('Did not find Chrome')
			else:
				self.path = ''
				for i in [
					'google-chrome',
					'/usr/bin/google-chrome',
					'/usr/bin/chromium',
				]:
					if os.path.isfile(i):
						self.path = i
						break
				if self.path == '':
					raise FileNotFoundError('Did not find Chrome/Chromium')
		else:
			raise Exception('The path to Chrome is the only possible argument.')
