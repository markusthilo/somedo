#!/usr/bin/env python3

from re import sub as rsub
from re import search as rsearch
from re import findall as rfindall

class Cutter:
	'Tools to cut out desired parts out of HTML, URLs etc.'

	def search(self, pattern, string):
		'Makes re.search usable'
		if string == None:
			return None
		m = rsearch(pattern, string)
		if m == None:
			return None
		return m.group()

	def href(self, html):
		'Search href='
		try:
			return rsub('&amp;', '&', self.search(' href="[^"]+', html)[7:])
		except:
			return None

	def src(self, html):
		'Get src='
		try:
			return rsub('&amp;', '&', self.search(' src="[^"]+', html)[6:])
		except:
			return None

	def ext(self, url):
		'Cut file extension out of media URL'
		try:
			return '.' + url.rsplit('/', 1)[-1].split('?', 1)[0].rsplit('.', 1)[1]
		except:
			return ''

	def split(self, string):
		'Split string at semicolons and remove whitespaces'
		return [ i.strip(' ') for i in string.replace(',', ';').split(';') if i.strip(' ') != '' ]
