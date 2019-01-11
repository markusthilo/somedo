#!/usr/bin/env python3

from tkinter import Tk
from base.gui import GuiRoot

if __name__ == '__main__':	# start here if called as program / app
	rootwindow = Tk()	# create gui
	GuiRoot(rootwindow, debug=True)
#	GuiRoot(rootwindow)
	rootwindow.mainloop()
else:
	raise NotImplementedError('Somedo has to be started as application in a graphical environment.')
