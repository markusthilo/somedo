#!/usr/bin/env python3

from tkinter import Tk
from os import getcwd, path, name
from base.tkgui import *

if __name__ == '__main__':	# start here if called as program / app
	rootwindow = Tk()
	if name == 'nt':  # slash to build paths
		slash = '\\'  # backslash for windows
	else:
		slash = '/'  # the real slash for real operating systems :-)
	GuiRoot(rootwindow, getcwd(), path.dirname(path.realpath(__file__)), slash)
	rootwindow.mainloop()
else:
	raise NotImplementedError('Somedo has to be started as application in a graphical environment.')
