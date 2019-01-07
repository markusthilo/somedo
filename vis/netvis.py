#!/usr/bin/env python3

from re import sub

class NetVis:
	'Network visualisation using Vis.js'

	def __init__(self, storage):
		'Build object to generate HTML/CSS/JavaScript site and GEXF file'
		self.storage = storage
		self.nodes_js = ''
		self.edges_js = ''
		self.nodes_gexf = ''
		self.edges_gexf = ''
		self.edge_id = 0

	def add_node(self, node_id, image='', alt_image='', label='', title=''):
		self.nodes_js += "\n\t\t\t\t{id: '%s'" % node_id
		self.nodes_gexf += '\n\t\t\t<node id="%s"' % node_id
		if image != '':
			self.nodes_js += ", shape: 'image', image: '%s'" % image
		if alt_image != '':
			self.nodes_js += ", brokenImage: '%s'" % alt_image
		if label != '':
			self.nodes_js += ", label: '%s'" % label
			self.nodes_gexf += ' label="%s"' % label
		else:
			self.nodes_js += ", label: '%s'" % node_id
			self.nodes_gexf += ' label="%s"' % node_id
		if title != '':
			self.nodes_js += ", title: '%s'" % title
		self.nodes_js += "},"
		self.nodes_gexf += ' />'

	def add_edge(self, from_id, to_id, arrow=False, dashes=False):
		self.edges_js += "\n\t\t\t\t{from: '%s', to: '%s'" % (from_id, to_id)
		self.edges_gexf += '\n\t\t\t<edge id="%d" source="%s" target="%s"' % (self.edge_id, from_id, to_id)
		if arrow:
			self.edges_js += ", arrows: 'to'"
			self.edges_gexf += ' type="directed"'
		if dashes:
			self.edges_js += ", dashes: true"
		self.edges_js += "},"
		self.edges_gexf += ' />'
		self.edge_id += 1

	def write(self, doubleclick=''):
		'Write HTML/CSS/JavaScript'
		self.storage.cptree2moddir('vis', 'Network')
		html = self.storage.read_static('vis', 'skeleton.html')
		html = sub('</nodes>', self.nodes_js.rstrip(','), html)
		html = sub('</edges>', self.edges_js.rstrip(','), html)
		html = sub('</doubleclick>', doubleclick, html)
		self.storage.write_str(html, 'Network', 'network.html')
		gexf = self.storage.read_static('vis', 'skeleton.gexf')
		gexf = sub('#today#', self.storage.today(), gexf)
		gexf = sub('#nodes#', self.nodes_gexf, gexf)
		gexf = sub('#edges#', self.edges_gexf, gexf)
		self.storage.write_html(gexf, 'Network', 'network.gexf')
