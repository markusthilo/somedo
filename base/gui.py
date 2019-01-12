#!/usr/bin/env python3

from threading import Event, Thread
from functools import partial
from tkinter import Tk, Frame, LabelFrame, Label, Button, Checkbutton, Entry, Text, PhotoImage, StringVar, BooleanVar, IntVar
from tkinter import BOTH, GROOVE, END, W, E, X, LEFT, RIGHT
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from base.storage import Storage
from base.worker import Worker
from base.chrometools import Chrome

class GuiRoot(Tk):
	'Graphic user interface using Tkinter.'

	JOBLISTLENGTH = 10
	BUTTONWIDTH = 16
	BIGENTRY = 120
	PADX = 8
	PADY = 8

	def __init__(self, master, debug=False):
		'Generate object for main / root window.'
		self.debug = debug
		self.storage = Storage()	# object for file system accesss
		self.chrome = Chrome()	# object to work with chrome/chromium
		self.worker = Worker(self.storage, self.chrome, debug=self.debug)	# generate object for the worker (smd_worker.py)
		self.jobs = []	# start with empty list for the jobs
		master.title('Social Media Downloader')	# window title for somedo
		try:
			master.call('wm', 'iconphoto', master._w, PhotoImage(	# give the window manager an application icon
				file='%s%ssomedo.png' % (self.storage.icondir, self.storage.slash)
			))
		except:
			pass
		frame_jobs = LabelFrame(master, text='Jobs')	# in this tk-frame the jobs will be displayed
		frame_jobs.pack(fill=X, expand=True)	# tk-stuff
		self.jobbuttons = []
		for i in range(self.JOBLISTLENGTH):
			frame_job = Frame(frame_jobs)
			frame_job.pack(fill=X, expand=True)
			self.jobbuttons.append(Button(frame_job,
				command=partial(self.__job_check__, i)).pack(side=LEFT, fill=X, expand=True))
			Button(frame_job, text='\u2191', command=partial(self.__job_up__, i)).pack(side=LEFT)
			Button(frame_job, text='\u2193', command=partial(self.__job_down__, i)).pack(side=LEFT)
		frame_row = LabelFrame(master)
		frame_row.pack(fill=BOTH, expand=True)
		Button(frame_row, text="Start jobs", width=self.BUTTONWIDTH,
			command=self.__start_hidden__).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		if self.debug:
			Button(frame_row, text="DEBUG: start visible", width=self.BUTTONWIDTH,
				command=self.__start_visible__).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		Button(frame_row, text="Stop running task", width=self.BUTTONWIDTH,
			command=self.__stop__).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		Button(frame_row, text='Purge job list', width=self.BUTTONWIDTH,
			command=self.__purge_jobs__).pack(side=RIGHT, pady=self.PADY)
		frame_row = LabelFrame(master, text='Add Job')	# add job frame
		frame_row.pack(fill=BOTH, expand=True)
		for i in self.worker.mods:	# generate buttons for the modules
			Button(frame_row, text=i, width=self.BUTTONWIDTH,
				command=partial(self.__add_job__, i)).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		frame_config = LabelFrame(master, text='Configuration')
		frame_config.pack(fill=X, expand=False)
		nb_config = ttk.Notebook(frame_config)	# here is the tk-notebook for the modules
		nb_config.pack(fill=X, expand=False)
		frame_nb = ttk.Frame(nb_config)
		nb_config.add(frame_nb, text='General')
		frame_row = Frame(frame_nb)
		frame_row.pack(fill=BOTH, expand=True)
		Label(frame_row, text='Output directory:', anchor=E, width=self.BUTTONWIDTH).pack(side=LEFT, padx=self.PADX)
		self.outdir_tk = StringVar(frame_row, self.storage.outdir)
		self.outdir_value = Entry(frame_row, textvariable=self.outdir_tk, width=self.BIGENTRY)
		self.outdir_value.pack(side=LEFT)
		Button(frame_row, text='\u261a', command=self.__output_dir__).pack(side=LEFT, padx=self.PADX)
		frame_row = Frame(frame_nb)
		frame_row.pack(fill=BOTH, expand=True)
		Label(frame_row, text='Chrome path:', anchor=E, width=self.BUTTONWIDTH).pack(side=LEFT, padx=self.PADX)
		self.chrome_tk = StringVar(frame_row, self.chrome.path)
		self.chrome_value = Entry(frame_row, textvariable=self.chrome_tk, width=self.BIGENTRY)
		self.chrome_value.pack(side=LEFT)
		Button(frame_row, text='\u261a', command=self.__chrome__).pack(side=LEFT, padx=self.PADX)

		self.tk_logins = dict()	# tkinter: login credentials
		self.tk_logins_hide = dict()	# tkinter: hide login credentials
		self.tk_logins_entry_fields = dict()	# tkinter: this is used for entry filds for login
		for i in self.worker.mods:	# notebook tabs for the module configuration

			if self.worker.logins[i] != []:
				frame_nb = ttk.Frame(nb_config)
				nb_config.add(frame_nb, text=i)
				self.tk_logins[i] = dict()	# login credentials as email and password
				self.tk_logins_hide[i] = dict()
				self.tk_logins_entry_fields[i] = dict()
				for j in self.worker.logins[i]:
					frame_row = Frame(frame_nb)
					frame_row.pack(fill=BOTH, expand=True)
					self.tk_logins[i][j] = StringVar(frame_row, '')
					self.tk_logins_hide[i][j] = BooleanVar(frame_row, True)
					Label(frame_row, text=j + ':', anchor=E, padx=self.PADX, width=self.BUTTONWIDTH, ).pack(side=LEFT)
					
					self.tk_logins_entry_fields[i][j] = Entry(
						frame_row,
						textvariable=self.tk_logins[i][j],
						show='*',
						width=self.BIGENTRY
					)
					self.tk_logins_entry_fields[i][j].pack(side=LEFT)
					Checkbutton(frame_row, text='hide', variable=self.tk_logins_hide[i][j],
						command=partial(self.__hide_login__, i, j)).pack(side=LEFT)
		frame_row = Frame(master)
		frame_row.pack(fill=X, expand=False)
		Button(frame_row, text="Save configuration", width=self.BUTTONWIDTH,
			command=self.__save_config__).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		Button(frame_row, text="Load configuration", width=self.BUTTONWIDTH,
			command=self.__load_config__).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		for i in ('README.md', 'README.txt', 'README.md.txt', 'README'):
			try:
				with open(self.storage.rootdir + self.storage.slash + i, 'r', encoding='utf-8') as f:
					self.about_help = f.read()
					Button(frame_row, text="About / Help", width=self.BUTTONWIDTH,
						command=self.__help__).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
					break
			except:
				continue
		Button(frame_row, text="Quit", width=self.BUTTONWIDTH,
			command=master.quit).pack(side=RIGHT, padx=self.PADX, pady=self.PADY)




	def __add_job__(self, module):
		'Generate dialog to add a job'
		self.nb_modules = ttk.Notebook(self.master)	# here is the tk-notebook for the modules
		self.nb_modules.pack(fill = X, expand = False)	# tk-stuff
		self.tabs = [ ttk.Frame(self.nb_modules) for i in self.worker.mods ]	# notebook-tabs for the modules
		self.tk_targets = dict()	# tkinter: targets
		self.tk_targets_entry_fields = dict()	# tkinter: this is used for entry fields of targets
		self.tk_options = dict()	# tkinter: options
		self.tk_options_entry_fields = dict()	# tkinter: this is used for entry filds of options
		self.tk_logins = dict()	# tkinter: login credentials
		self.tk_logins_hide = dict()	# tkinter: hide login credentials
		self.tk_logins_entry_fields = dict()	# tkinter: this is used for entry filds for login
		tab_cnt = 0
		for i in self.worker.mods:	# generate tabs for the modules
			self.nb_modules.add(self.tabs[tab_cnt], text = i)	# add tab to tk-notebook
			row = 0	# row for grid
			self.tk_targets[i] = StringVar(self.tabs[tab_cnt], '')	# generate field for target(s)
			Label(self.tabs[tab_cnt], text='Target(s):').grid(row=row, column=0, sticky=W, padx=24, pady=2)	# target entry
			self.tk_targets_entry_fields[i] = Entry(self.tabs[tab_cnt], textvariable=self.tk_targets[i], width=144)
			self.tk_targets_entry_fields[i].grid(row=row, column=1, columnspan=100, sticky=W, padx=1, pady=2)
			self.tk_options[i] = dict()	# dicts in dict for the options in each module
			self.tk_options_entry_fields[i] = dict()
			row += 1
			for j in self.worker.opts[i]:	# loop throught option's 1st dimension
				self.tk_options[i][j[0][0]] = dict()
				self.tk_options_entry_fields[i][j[0][0]] = dict()
				column = 0
				for k in j:	# loop throught option's 2nd dimension
					if isinstance(k[1], bool):	# checkbutton for boolean
						self.tk_options[i][j[0][0]][k[0]] = BooleanVar(self.tabs[tab_cnt], k[1])	# create tk-variable in subset (boolean)
						Checkbutton(self.tabs[tab_cnt], text=k[0], variable=self.tk_options[i][j[0][0]][k[0]]).grid(row=row, column=column, sticky=W)
					elif isinstance(k[1], int):	# entry field for integers
						self.tk_options[i][j[0][0]][k[0]] = IntVar(self.tabs[tab_cnt], k[1])	# create tk-variable in subset (integer)
						Label(self.tabs[tab_cnt], text=k[0]+':').grid(row=row, column=column)
						column += 1
						self.tk_options_entry_fields[i][j[0][0]][k[0]] = Entry(self.tabs[tab_cnt], textvariable=self.tk_options[i][j[0][0]][k[0]], width=8)
						self.tk_options_entry_fields[i][j[0][0]][k[0]].grid(row=row, column=column, sticky=W, pady=1)
					elif isinstance(k[1], str):	# entry field for strings
						self.tk_options[i][j[0][0]][k[0]] = StringVar(self.tabs[tab_cnt], k[1])	# create tk-variable in subset (integer)
						Label(self.tabs[tab_cnt], text=k[0]+':').grid(row=row, column=column)
						column += 1
						self.tk_options_entry_fields[i][j[0][0]][k[0]] = Entry(self.tabs[tab_cnt], textvariable=self.tk_options[i][j[0][0]][k[0]], width=len(k[1]))
						self.tk_options_entry_fields[i][j[0][0]][k[0]].grid(row=row, column=column, sticky=W, pady=1)
					column +=1
				row += 1
			Button(self.tabs[tab_cnt], text='Add job', width=16, command=partial(self.__add_job__, i)).grid(row=row, column=0, pady=2)
			
			row += 1
			if self.worker.logins[i] != []:
				Label(self.tabs[tab_cnt], text='Login').grid(row=row, column=0, sticky=W, padx=2, pady=2)
				row += 1
				self.tk_logins[i] = dict()	# login credentials as email and password
				self.tk_logins_hide[i] = dict()
				self.tk_logins_entry_fields[i] = dict()
				for j in self.worker.logins[i]:
					self.tk_logins[i][j] = StringVar(self.tabs[tab_cnt], '')
					self.tk_logins_hide[i][j] = BooleanVar(self.tabs[tab_cnt], True)
					Label(self.tabs[tab_cnt], text=j + ':').grid(row=row, column=0, sticky=E, padx=2, pady=2)
					Checkbutton(self.tabs[tab_cnt], text='hide', variable=self.tk_logins_hide[i][j],
						command=partial(self.__hide_login__, i, j)).grid(row=row, column=1,sticky=E,  pady=2)
					self.tk_logins_entry_fields[i][j] = Entry(self.tabs[tab_cnt], textvariable=self.tk_logins[i][j], show='*', width=120)
					self.tk_logins_entry_fields[i][j].grid(row=row, column=2, columnspan=100, sticky=W, padx=2, pady=2)
					row += 1
			tab_cnt += 1

	def __hide_login__(self, module, item):
		'Toggle hidden login credentials'
		if self.tk_logins_hide[module][item].get():
			self.tk_logins_entry_fields[module][item].config(show='*')
		else:
			self.tk_logins_entry_fields[module][item].config(show='')

	def __add_job__(self, module):
		'Add job to list'
		if len(self.jobs) < 10 and self.tk_targets[module].get() != '':	# if free space in job list and target(s) are not empty
			self.jobs.append([ module, self.tk_targets[module].get(), dict() ])	# append new job to the job list
			for i in self.tk_options[module]:	# insert options
				if self.tk_options[module][i][i].get():
					self.jobs[-1][2][i] = dict()
					for j in self.tk_options[module][i]:
						if j != i:
							self.jobs[-1][2][i][j] = self.tk_options[module][i][j].get()
			self.__update_joblist__()

	def __purge_jobs__(self):
		'Purge job list'
		if messagebox.askyesno('Purge job list', 'Are you sure?'):
			self.jobs = []
			self.__update_joblist__()

	def __job_label__(self, row):
		'Generate labes for the job list'
		if row < len(self.jobs):
			text = '%02d - %s' % ((row + 1), self.jobs[row][0])
			for i in self.jobs[row][2]:
				text += ' %s,' % i
			self.__tk_labels__[row].set(text.rstrip(',') + ': %s' % self.jobs[row][1])
		else:
			self.__tk_labels__[row].set("")

	def __job_info__(self, row):
		if row >= len(self.jobs):
			return 'Empty / no job'
		text = '%s\n' % self.jobs[row][0]
		text += '%s\n' % self.jobs[row][1]
		for i in self.jobs[row][2]:
			text += i
			for j in self.jobs[row][2][i]:
				text += ' - %s' % j
				if not isinstance(self.jobs[row][2][i][j], bool):
					text += ': %s' % str(self.jobs[row][2][i][j])
			text += '\n'
		return text

	def __update_joblist__(self):
		'Update the list of jobs'
		for i in range(10):
			self.__job_label__(i)

	def __job_up__(self, position):
		'Move job up in list'
		if position > 0:
			self.jobs[position], self.jobs[position-1] = self.jobs[position-1], self.jobs[position]
			self.__update_joblist__()

	def __job_down__(self, position):
		'Move job down in list'
		if position < ( len(self.jobs) - 1 ) :
			self.jobs[position], self.jobs[position+1] = self.jobs[position+1], self.jobs[position]
			self.__update_joblist__()

	def __job_check__(self, position):
		'Check or maybe remove job'
		if position < len(self.jobs):
			self.job_win = Tk()
			self.job_win.wm_title('Job %02d' % (position+1))
			text = Text(self.job_win, padx=2, pady=2, height=20, width=80)
			text.bind("<Key>", lambda e: "break")
			text.insert(END, self.__job_info__(position))
			text.pack(padx=2, pady=2)
			Button(self.job_win, text="Remove job", width=10, command=partial(self.__job_remove__, position)).pack(padx=2, pady=2, side=LEFT)
			Button(self.job_win, text="Close / Do not remove", width=20, command=self.job_win.destroy).pack(padx=2, pady=2, side=RIGHT)

	def __job_remove__(self, position):
		'Remove job from list'
		self.job_win.destroy()
		if messagebox.askyesno('Job %02d' % (position+1), 'Remove job from list?'):
			self.jobs.pop(position)
			self.__update_joblist__()
			self.__job_label__(len(self.jobs))

	def __output_dir__(self):
		'Set path to output directory.'
		outdir = filedialog.askdirectory(initialdir="~/",title='Destination directory')
		if outdir != ():
			self.outdir_value.delete(0, END)
			self.outdir_value.insert(0, outdir)
			self.storage.outdir = outdir

	def __chrome__(self):
		'Set path to chrome.'
		filename = filedialog.askopenfilename(title = 'chrome', filetypes = [('All files', '*.*')])
		if filename != () and filename !=  '':
			self.chrome_value.delete(0, END)
			self.chrome_value.insert(0, filename)

	def __get_config__(self):
		'Put configuration in a dict'
		config = {'Output directory': self.outdir_value.get(), 'Chrome': self.chrome_value.get()}
		for i in self.worker.mods:
			config[i] = dict()
			for j in self.worker.logins[i]:
				config[i][j] = self.tk_logins[i][j].get()
		return config

	def __save_config__(self):
		'Save configuration to file.'
		filename = filedialog.asksaveasfilename(title = 'Configuration file', filetypes = [('Somedo configuration files', '*.smdc')])
		if filename[-5:] != '.smdc':
			filename += '.smdc'
		try:
			self.storage.json_dump(self.__get_config__(), filename)
		except:
			messagebox.showerror('Error', 'Could not save configuration file')

	def __load_config__(self):
		'Load configuration from file.'
		filename = filedialog.askopenfilename(title = 'Configuration file', filetypes = [('Somedo configuration files', '*.smdc'), ('All files', '*.*')])
		if filename != () and filename !=  '':
			try:
				config = self.storage.json_load(filename)
			except:
				messagebox.showerror('Error', 'Could not load configuration file')
				return
			self.outdir_value.delete(0, END)
			self.outdir_value.insert(0, config['Output directory'])
			self.chrome_value.delete(0, END)
			self.chrome_value.insert(0, config['Chrome'])
			self.storage.outdir = config['Output directory']
			for i in self.worker.mods:
				if i in config:
					try:
						for j in self.tk_logins_entry_fields[i]:
							self.tk_logins_entry_fields[i][j].delete(0, END)
							self.tk_logins_entry_fields[i][j].insert(0, config[i][j])
					except:
						pass

	def __help__(self):
		'Open window to show About / Help'
		help_win = Tk()
		help_win.wm_title('About / Help')
		text = Text(help_win, padx=2, pady=2, height=35, width=160)
		text.bind("<Key>", lambda e: "break")
		text.insert(END, self.about_help)
		text.pack(padx=2, pady=2)
		Button(help_win, text="Close", width=6, command=help_win.destroy).pack(padx=2, pady=2, side=RIGHT)

	def __start_visible__(self):
		'Start working with Chrome'
		if len(self.jobs) > 0:
			try:	# check if task is running
				if self.thread.isAlive():
					return
			except:
				pass
			self.__running_label__.config(background='green')
			self.__tk_running__.set("Running...")
			self.headless = False	# chrome will be visible
			self.stop = Event()	# to stop main thread
			self.thread = Thread(target=self.__thread__)	# define main thread
			self.thread.start()	# start thread
		else:
			messagebox.showerror('Error', 'Nothing to do')

	def __start_hidden__(self):
		'Start working with Chrome in headless mode'
		if len(self.jobs) > 0:
			try:	# check if task is running
				if self.thread.isAlive():
					return
			except:
				pass
			self.__running_label__.config(background='red')
			self.__tk_running__.set("Running...")
			self.headless = True	# chrome will be started with option --headless
			self.stop = Event()	# to stop main thread
			self.thread = Thread(target=self.__thread__)	# define main thread
			self.thread.start()	# start thread
		else:
			messagebox.showerror('Error', 'Nothing to do')

	def __stop__(self):
		'Stop running job but give results based on so far sucked data'
		try:	# check if task is running
			if self.thread.isAlive() and messagebox.askyesno('Somedo', 'Stop running task?'):
				self.stop.set()
		except:
			pass

	def __thread__(self):
		'Execute jobs'
		msg = self.worker.execute(self.jobs, self.__get_config__(), headless=self.headless, stop=self.stop)
		self.__tk_running__.set("")
		self.__running_label__.config(background='white')
		messagebox.showinfo('Done', msg)

if __name__ == '__main__':	# start here if called as program / app
	rootwindow = Tk()
	GuiRoot(rootwindow)
	rootwindow.mainloop()