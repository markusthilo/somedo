#!/usr/bin/env python3

from re import sub

class NetVis:
	'Network visualisation using Vis.js'

	def __init__(self, storage):
		'Build object to generate HTML/CSS/JavaScript site'
		self.storage = storage
		self.nodes_js = ''
		self.edges_js = ''

	def add_node(self, node_id, image, alt_image, label):
		self.nodes_js += '''
				{id: '%s',  shape: 'image', image: '%s', brokenImage: '%s', label: '%s'},''' % (node_id, image, alt_image, label)

	def add_edge(self, from_id, to_id, arrows='', dashes=False):
		if dashes = True:
			dashes = 'true'
		else:
			dashes = 'false'
		self.edges_js += '''
				{from: '%s', to: '%s', arrows: '%s', dashes: '%s'},''' % (from_id, to_id, arrows, dashes)

	def write(self):
		'Write HTML/CSS/JavaScript'
		self.storage.cptree2moddir('vis', 'netvis')
		html = self.storage.read_static('vis', 'skeleton.html')
		html = sub('</nodes>', self.nodes_js.rstrip(',') + '\n')
		html = sub('</edges>', self.edges_js.rstrip(',') + '\n')
		self.storage.write_str(html, 'netvis', 'index.html')
