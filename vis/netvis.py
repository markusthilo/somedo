#!/usr/bin/env python3

from os import path

class NetVis:
	'Network visualisation jusing Vis.js'

	def __init__(self, storage):
		'Build object to generate HTML/CSS/JavaScript site'
		self.storage = storage	
		with open('%s%svis%sskeleton.html' % (path.realpath(__file__), storage.slash,storage.slash), 'r', encoding='utf-8') as f:
			skeleton = f.read()
