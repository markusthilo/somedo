#!/usr/bin/env python3

from time import sleep
from threading import Event, Thread
from functools import partial
from tkinter import Tk, Frame, LabelFrame, Label, Button, Checkbutton, Entry
from tkinter import Text, PhotoImage, StringVar, BooleanVar, IntVar
from tkinter import BOTH, GROOVE, END, W, E, N, S, X, LEFT, RIGHT, DISABLED
from tkinter import ttk, filedialog, messagebox, scrolledtext
from logging import Handler, DEBUG
from base.storage import Storage
from base.worker import Worker
from base.chrometools import Chrome

class GUI(Tk):
	'Graphic user interface using Tkinter, main / root window'

	def __init__(self, root, logger):
		'Generate object for main / root window.'
		self.root = root
		self.logger = logger
		self.storage = Storage()	# object for file system accesss
		### "constants" for the gui ###
		if self.storage.windows:
			self.JOBLISTLENGTH = 10
			self.BUTTONWIDTH = 16
			self.BIGENTRYWIDTH = 128
			self.INTWIDTH = 6
			self.TARGETWIDTH = 160
			self.PADX = 8
			self.PADY = 8
			self.OPTPADX = 6
			self.CHNGWIDTH = 160
			self.CHNGHEIGHT = 10
			self.MSGHEIGHT = 8
		else:
			self.JOBLISTLENGTH = 10
			self.BUTTONWIDTH = 16
			self.BIGENTRYWIDTH = 96
			self.INTWIDTH = 6
			self.TARGETWIDTH = 120
			self.PADX = 8
			self.PADY = 8
			self.OPTPADX = 6
			self.CHNGWIDTH = 123
			self.CHNGHEIGHT = 14
			self.MSGHEIGHT = 8
		###############################
		self.chrome = Chrome()	# object to work with chrome/chromium
		self.worker = Worker(self.storage, self.chrome, self.logger)	# generate object for the worker (smd_worker.py)
		self.__close2quit__()	# handle closing of root window
		self.jobs = []	# start with empty list for the jobs
		self.root.title('Social Media Downloader')	# window title for somedo
		self.__set_icon__(self.root)	# give the window manager an application icon
		frame_jobs = LabelFrame(self.root, text=' \u25a4 Jobs ')	# in this tk-frame the jobs will be displayed
		frame_jobs.pack(fill=X, expand=True)
		frame_jobs_inner = Frame(frame_jobs)
		frame_jobs_inner.pack(fill=X, expand=True, padx=self.PADX, pady=self.PADY)
		self.tk_jobbuttons = []
		self.jobbuttons = []
		self.upbuttons = []
		self.downbuttons = []
		for i in range(self.JOBLISTLENGTH):
			frame_row = Frame(frame_jobs_inner)
			frame_row.pack(fill=X, expand=True)
			self.tk_jobbuttons.append(StringVar(frame_row))
			self.jobbuttons.append(Button(frame_row, textvariable=self.tk_jobbuttons[i], anchor=W,
				command=partial(self.__job_edit__, i)))
			self.jobbuttons[i].pack(side=LEFT, fill=X, expand=True)
			self.upbuttons.append(Button(frame_row, text='\u2191', command=partial(self.__job_up__, i)))
			self.upbuttons[i].pack(side=LEFT)
			self.downbuttons.append(Button(frame_row, text='\u2193', command=partial(self.__job_down__, i)))
			self.downbuttons[i].pack(side=LEFT)
		frame_row = Frame(frame_jobs_inner)
		frame_row.pack(fill=BOTH, expand=True)
		self.startbutton = Button(frame_row, text="Start jobs", width=self.BUTTONWIDTH,
			command=self.__start_hidden__)
		self.startbutton.pack(side=LEFT, pady=self.PADY)
		if self.logger.level <= DEBUG:
			self.startbutton_hidden = Button(frame_row, text="DEBUG: start visible", width=self.BUTTONWIDTH,
				command=self.__start_visible__)
			self.startbutton_hidden.pack(side=LEFT, padx=self.PADX*2, pady=self.PADY)
		self.stopbutton = Button(frame_row, text="Stop / Abort", width=self.BUTTONWIDTH, state = DISABLED,
			command=self.__stop__)
		self.stopbutton.pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		self.purgebutton = Button(frame_row, text='Purge job list', width=self.BUTTONWIDTH,
			command=self.__purge_jobs__)
		self.purgebutton.pack(side=RIGHT, pady=self.PADY)
		frame_row = LabelFrame(self.root, text=' + Add Job ')	# add job frame
		frame_row.pack(fill=X, expand=True)
		self.modulebuttons = dict()
		for i in self.worker.modulenames:	# generate buttons for the modules
			self.modulebuttons[i] = Button(frame_row, text=i, font='bold', height=3,
				command=partial(self.__new_job__, i))
			self.modulebuttons[i].pack(side=LEFT, fill=BOTH, expand=True, padx=self.PADX, pady=self.PADY)
		self.frame_changeling = LabelFrame(self.root)	# frame for configuration or messages
		self.frame_changeling.pack(fill=BOTH, expand=True)
		self.frame_messages = Frame(self.frame_changeling)	# message frame
		self.text_messages = scrolledtext.ScrolledText(
			self.frame_messages,
			padx = self.PADX,
			pady = self.PADY,
			height = self.MSGHEIGHT
		)
		self.text_messages.pack(fill=BOTH, expand=True, padx=self.PADX, pady=self.PADY)
		self.text_messages.bind("<Key>", lambda e: "break")
		self.worker.loghandler = LogHandler(self.text_messages)	# give tk loghandler to worker
		self.frame_config = Frame(self.frame_changeling)	# config frame
		nb_config = ttk.Notebook(self.frame_config)	# here is the tk-notebook for the modules
		nb_config.pack(padx=self.PADX, pady=self.PADY)
		frame_nb = ttk.Frame(nb_config)
		nb_config.add(frame_nb, text='General')
		frame_row = Frame(frame_nb)
		frame_row.pack(fill=BOTH, expand=True)
		Label(frame_row, text='Output directory:', anchor=E, width=self.BUTTONWIDTH).pack(side=LEFT, padx=self.PADX)
		self.tk_outdir = StringVar(frame_row, self.storage.outdir)
		self.tk_outdir_entry = Entry(frame_row, textvariable=self.tk_outdir, width=self.BIGENTRYWIDTH)
		self.tk_outdir_entry.pack(side=LEFT)
		Button(frame_row, text='...', command=self.__output_dir__).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		frame_row = Frame(frame_nb)
		frame_row.pack(fill=BOTH, expand=True)
		Label(frame_row, text='Chrome path:', anchor=E, width=self.BUTTONWIDTH).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		self.tk_chrome = StringVar(frame_row, self.chrome.path)
		self.tk_chrome_entry = Entry(frame_row, textvariable=self.tk_chrome, width=self.BIGENTRYWIDTH)
		self.tk_chrome_entry.pack(side=LEFT)
		Button(frame_row, text='...', command=self.__chrome__).pack(side=LEFT, padx=self.PADX)
		self.tk_logins = dict()	# login credentials
		self.tk_login_entries = dict()
		for i in self.worker.MODULES:	# notebook tabs for the module configuration
			if i['login'] != None:
				frame_nb = ttk.Frame(nb_config)
				nb_config.add(frame_nb, text=i['name'])
				self.tk_logins[i['name']], self.tk_login_entries[i['name']] = self.__login_frame__(
					frame_nb, i['name'], self.worker.logins[i['name']]
				)
		frame_row = LabelFrame(self.frame_config, text=' \u2196\u2198 ')
		frame_row.pack(fill=X, expand=True, padx=self.PADX, pady=self.PADY)
		Button(frame_row, text="Save configuration", width=self.BUTTONWIDTH,
			command=self.__save_config__).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		Button(frame_row, text="Load configuration", width=self.BUTTONWIDTH,
			command=self.__load_config__).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		Label(self.frame_changeling, width=self.CHNGWIDTH).grid(row=1, column=0)
		Label(self.frame_changeling, height=self.CHNGHEIGHT).grid(row=0, column=1)
		self.button_toggle = Button(self.frame_changeling,
			command=self.__toggle_config__, width=self.BUTTONWIDTH)
		self.button_toggle.grid(row=2, column=0, padx=self.PADX, pady=self.PADY, sticky=W)
		self.__enable_config__()
		frame_row = Frame(self.root)
		frame_row.pack(fill=X, expand=True)
		for i in ('README.md', 'README.txt', 'README.md.txt', 'README'):
			try:
				with open(self.storage.rootdir + self.storage.slash + i, 'r', encoding='utf-8') as f:
					self.about_help = f.read()
					Button(frame_row, text="About / Help", width=self.BUTTONWIDTH,
						command=self.__help__).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
					break
			except:
				continue
		self.quitbutton = Button(frame_row, text="Quit", width=self.BUTTONWIDTH, command=self.__quit__)
		self.quitbutton.pack(side=RIGHT, padx=self.PADX, pady=self.PADY)

	def __set_icon__(self, master):
		'Try to Somedo icon for the window'
		try:
			master.call('wm', 'iconphoto', master._w, PhotoImage(
				file='%s%ssomedo.png' % (self.storage.icondir, self.storage.slash)
			))
		except:
			pass

	def __quit__(self):
		'Close the app'
		if messagebox.askyesno('Quit', 'Close this Application?'):
			self.root.quit()

	def __close2quit__(self):
		'Ask to quit on close windows by "X"'
		self.root.protocol("WM_DELETE_WINDOW", self.__quit__)

	def __close2stop__(self):
		'Ask to stop job(s) on close windows by "X"'
		self.root.protocol("WM_DELETE_WINDOW", self.__stop__)

	def __close2kill__(self):
		'Ask to kill Somedo immediatly on close windows by "X"'
		self.root.protocol("WM_DELETE_WINDOW", self.__kill__)

	def __login_frame__(self, frame, module, login):
		'Create Tk Frame for login credentials'
		tk_login = dict()
		tk_login_entry = dict()
		for i in login:
			frame_row = Frame(frame)
			frame_row.pack(fill=BOTH, expand=True)
			Label(frame_row, text=i, anchor=E, padx=self.PADX, width=self.BUTTONWIDTH).pack(side=LEFT)
			tk_login[i] = StringVar(frame_row)
			if self.worker.logins[module] != None:
				tk_login[i].set(login[i])
			tk_login_entry[i] = Entry(frame_row, textvariable=tk_login[i], show='*', width=self.BIGENTRYWIDTH)
			tk_login_entry[i].pack(side=LEFT)
			tk_hide = BooleanVar(frame_row, True)
			Checkbutton(frame_row, text='hide', variable=tk_hide,
					command=partial(self.__hide_entry__, tk_login_entry[i], tk_hide)).pack(side=LEFT)
		return tk_login, tk_login_entry

	def __hide_entry__(self, entry, check):
		'Toggle hidden login credentials'
		if check.get():
			entry.config(show='*')
		else:
			entry.config(show='')

	def __job_dialog__(self, job, row):
		'Open window to edit a job'
		self.__disable_jobbuttons__()
		self.job_dialog_root.title(job['module'])
		frame_row = LabelFrame(self.job_dialog_root, text=' \u229a Target(s) ')
		frame_row.pack(fill=BOTH, expand=True, padx=self.PADX, pady=self.PADY)
		tk_job = {'module': job['module'], 'target': StringVar(frame_row, job['target'])}	# tk variables for the job configuration
		tk_target_entry = Entry(frame_row, textvariable=tk_job['target'], width=self.TARGETWIDTH)
		tk_target_entry.pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		tk_job['options'] = dict()	# tk variables for the options
		if job['options'] != None:
			frame_grid = LabelFrame(self.job_dialog_root, text=' \u2714 Options ')
			frame_grid.pack(fill=BOTH, expand=True, padx=self.PADX, pady=self.PADY)
			for i in self.worker.options[job['module']]:
				definition = self.worker.options[job['module']][i]
				value = job['options'][i]
				Label(frame_grid, text=definition['name']).grid(
					row=definition['row'], column=definition['column']*2, sticky=E, pady=self.PADY
				)
				if isinstance(value, bool):	# checkbutton for boolean
					tk_job['options'][i] = BooleanVar(frame_grid, value)
					Checkbutton(frame_grid, variable=tk_job['options'][i]).grid(
						row=definition['row'], column=definition['column']*2+1, sticky=W
					)
					width = 0
				elif isinstance(value, int):	# integer
					tk_job['options'][i] = IntVar(frame_grid, value)
					width = self.INTWIDTH
				elif isinstance(value, str): # string
					tk_job['options'][i] = StringVar(frame_grid, value)
					width = self.BUTTONWIDTH
				if width != 0:
					Entry(frame_grid, textvariable=tk_job['options'][i], width=width).grid(
						row=definition['row'], column=definition['column']*2+1, sticky=W, padx=self.OPTPADX
					)
		if job['login'] != None:
			frame_login = LabelFrame(self.job_dialog_root, text=' \u2737 Login')
			frame_login.pack(fill=BOTH, expand=True, padx=self.PADX, pady=self.PADY)
			tk_job['login'], dummy = self.__login_frame__(frame_login, job['module'], job['login'])
		frame_row = Frame(self.job_dialog_root)
		frame_row.pack(fill=BOTH, expand=True)
		if row == len(self.jobs):
			Button(frame_row, text="Add job", width=self.BUTTONWIDTH,
				command=partial(self.__add_job__, tk_job)).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		else:
			Button(frame_row, text="Update job", width=self.BUTTONWIDTH,
				command=partial(self.__update_job__, tk_job, row)).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
			Button(frame_row, text="Remove job", width=self.BUTTONWIDTH,
				command=partial(self.__remove_job__, row)).pack(side=LEFT, padx=self.PADX, pady=self.PADY)
		Button(frame_row, text="Quit, do nothing", width=self.BUTTONWIDTH,
			command=self.__quit_job_dialog__).pack(side=RIGHT, padx=self.PADX, pady=self.PADY)

	def __quit_job_dialog__(self):
		'Close the job configuration window'
		self.job_dialog_root.destroy()
		self.__enable_jobbuttons__()

	def __get_login__(self, module):
		'Get login credentials for a module from root window'
		if self.worker.logins[module] == None:
			return None
		return { i: self.tk_logins[module][i].get() for i in self.worker.logins[module] }

	def __new_job__(self, module):
		'Create new job to add to job list'
		if len(self.jobs) == self.JOBLISTLENGTH - 1:	# check if free space in job list
			return
		job = self.worker.new_job(module)
		if self.worker.logins[module] != None:
			job['login'] = self.__get_login__(module)
		self.job_dialog_root = Tk()
		self.__job_dialog__(job, len(self.jobs))

	def __job_edit__(self, row):
		'Edit or remove jobin job list'
		if row >= len(self.jobs):
			return
		self.job_dialog_root = Tk()
		self.__job_dialog__(self.jobs[row], row)

	def __tk2job__(self, tk_job):
		'Get Tk values for a job'
		job = {
			'module': tk_job['module'],
			'target': tk_job['target'].get(),
			'options': { i: tk_job['options'][i].get() for i in tk_job['options'] }
		}
		try:
			job['login'] = { i: tk_job['login'][i].get() for i in tk_job['login'] }
		except:
			job['login'] = None
		return job

	def __add_job__(self, tk_job):
		'Add job to list'
		if tk_job['target'].get() == '':	# no target, no job
			return
		self.job_dialog_root.destroy()
		self.__enable_jobbuttons__()
		self.jobs.append(self.__tk2job__(tk_job))
		self.__update_joblist__()

	def __update_job__(self, tk_job, row):
		'Update job in list'
		if tk_job['target'].get() == '':	# no target, no job
			return
		self.job_dialog_root.destroy()
		self.__enable_jobbuttons__()
		self.jobs[row] = self.__tk2job__(tk_job)
		self.__update_joblist__()

	def __purge_jobs__(self):
		'Purge job list'
		if len(self.jobs) < 1:
			return
		if messagebox.askyesno('Purge job list', 'Are you sure to remove all jobs fromk list?'):
			self.jobs = []
			self.__update_joblist__()

	def __job_text__(self, row):
		'Generate string for one job button'
		if row >= len(self.jobs):
			return ''
		return '%s - %s' % (self.jobs[row]['module'], self.jobs[row]['target'])

	def __update_joblist__(self):
		'Update the list of jobs'
		for i in range(self.JOBLISTLENGTH):
			self.tk_jobbuttons[i].set(self.__job_text__(i))

	def __job_up__(self, row):
		'Move job up in list'
		if row > 0:
			self.jobs[row], self.jobs[row-1] = self.jobs[row-1], self.jobs[row]
			self.__update_joblist__()

	def __job_down__(self, row):
		'Move job down in list'
		if row < ( len(self.jobs) - 1 ) :
			self.jobs[row], self.jobs[row+1] = self.jobs[row+1], self.jobs[row]
			self.__update_joblist__()

	def __remove_job__(self, row):
		'Remove job from list'
		if messagebox.askyesno('Remove job', 'Are you sure?'):
			self.job_dialog_root.destroy()
			self.__enable_jobbuttons__()
			self.jobs.pop(row)
			self.__update_joblist__()

	def __output_dir__(self):
		'Set path to output directory.'
		path = filedialog.askdirectory(initialdir="~/",title='Destination directory')
		if path != ():
			self.tk_outdir_entry.delete(0, END)
			self.tk_outdir_entry.insert(0, path)
			self.storage.outdir = path

	def __chrome__(self):
		'Set path to chrome.'
		path = filedialog.askopenfilename(title = 'chrome', filetypes = [('All files', '*.*')])
		if path != () and path !=  '':
			self.tk_chrome_entry.delete(0, END)
			self.tk_chrome_entry.insert(0, path)
			self.chrome.path = path

	def __save_config__(self):
		'Save configuration to file.'
		path = filedialog.asksaveasfilename(title = 'Configuration file', filetypes = [('Somedo configuration files', '*.smdc')])
		if path[-5:] != '.smdc':
			path += '.smdc'
		try:
			self.storage.json_dump({
				'Output': self.tk_outdir.get(),
				'Chrome': self.tk_chrome.get(),
				'Modules': { i: self.__get_login__(i) for i in self.worker.modulenames if self.worker.logins[i] != None }
			}, path)
		except:
			messagebox.showerror('Error', 'Could not save configuration file')

	def __load_config__(self):
		'Load configuration from file.'
		path = filedialog.askopenfilename(title = 'Configuration file', filetypes = [('Somedo configuration files', '*.smdc'), ('All files', '*.*')])
		if path != () and path !=  '':
			try:
				config = self.storage.json_load(path)
			except:
				messagebox.showerror('Error', 'Could not load configuration file')
				return
			try:
				self.tk_outdir_entry.delete(0, END)
				self.tk_outdir_entry.insert(0, config['Output'])
				self.storage.outdir = config['Output']
				self.tk_chrome_entry.delete(0, END)
				self.tk_chrome_entry.insert(0, config['Chrome'])
				self.chrome.path = config['Chrome']
				for i in config['Modules']:
					for j in config['Modules'][i]:
						self.tk_login_entries[i][j].delete(0, END)
						self.tk_login_entries[i][j].insert(0, config['Modules'][i][j])
			except:
				messagebox.showerror('Error', 'Could not decode configuration file')

	def __help__(self):
		'Open window to show About / Help'
		help_win = Tk()
		help_win.wm_title('About / Help')
		text = scrolledtext.ScrolledText(help_win, padx=self.PADX, pady=self.PADY, width=self.TARGETWIDTH)
		text.bind("<Key>", lambda e: "break")
		text.insert(END, self.about_help)
		text.pack()
		Button(help_win, text="Close", width=self.BUTTONWIDTH,
			command=help_win.destroy).pack(padx=self.PADX, pady=self.PADY, side=RIGHT)

	def __start_visible__(self):
		'Start the jobs visible in DEBUG mode'
		self.headless = False	# start chrome visible for debugging
		self.__start__()

	def __start_hidden__(self):
		'Start the jobs'
		self.headless = True	# chrome will be started with option --headless
		self.__start__()

	def __disable_jobbuttons__(self):
		'Disable the job related buttons except Abort'
		for i in range(self.JOBLISTLENGTH):
			self.jobbuttons[i].config(state=DISABLED)
			self.upbuttons[i].config(state=DISABLED)
			self.downbuttons[i].config(state=DISABLED)
		self.startbutton.config(state=DISABLED)
		if self.logger.level <= DEBUG:
			self.startbutton_hidden.config(state=DISABLED)
		self.purgebutton.config(state=DISABLED)
		for i in self.worker.modulenames:
			self.modulebuttons[i].config(state=DISABLED)

	def __enable_jobbuttons__(self):
		'Enable the job related buttons except Abort'
		for i in range(self.JOBLISTLENGTH):
			self.jobbuttons[i].config(state='normal')
			self.upbuttons[i].config(state='normal')
			self.downbuttons[i].config(state='normal')
		self.startbutton.config(state='normal')
		if self.logger.level <= DEBUG:
			self.startbutton_hidden.config(state='normal')
		self.purgebutton.config(state='normal')
		for i in self.worker.modulenames:
			self.modulebuttons[i].config(state='normal')

	def __disable_quitbutton__(self):
		'Disable the button Quit and enable Abort'
		self.quitbutton.config(state=DISABLED)
		self.stopbutton.config(state='normal')

	def __enable_quitbutton__(self):
		'Enable the button Quit and disable Abort'
		self.quitbutton.config(state='normal')
		self.stopbutton.config(state=DISABLED)

	def __enable_config__(self):
		'Enable configuration frame'
		self.config_visible = True
		self.frame_changeling.config(text=' \u2737 Configuration ')
		self.frame_config.grid(row=0, column=0, sticky=W+E+N+S)
		self.frame_messages.grid_remove()
		self.button_toggle.config(text='Show Messages')

	def __enable_messages__(self):
		'Enable configuration frame'
		self.config_visible = False
		self.frame_changeling.config(text=' \u2709 Messages')
		self.frame_config.grid_remove()
		self.frame_messages.grid(row=0, column=0, sticky=W+E+N+S)
		self.button_toggle.config(text='Show Configuration')

	def __toggle_config__(self):
		'Toggle Configuration / Messages'
		if self.config_visible:
			self.__enable_messages__()
		else:
			self.__enable_config__()

	def __start__(self):
		'Start the jobs'
		if len(self.jobs) < 1:
			messagebox.showerror('Error', 'Nothing to do')
			return
		try:	# check if task is running
			if self.thread_worker.isAlive():
				return
		except:
			pass
		self.__disable_jobbuttons__()
		self.__disable_quitbutton__()
		self.__enable_messages__()
		self.__close2stop__()
		self.stop = Event()	# to stop working thread
		self.stop_set = False
		self.thread_worker = Thread(target=self.__worker__)
		self.thread_worker.start()	# start work
		self.thread_showjob = Thread(target=self.__showjob__)
		self.thread_showjob.start()	# start work

	def __stop__(self):
		'Stop running job but give results based on already optained data'
		if self.stop_set:
			self.__kill__()
			return
		try:	# check if task is running
			if self.thread_worker.isAlive() and messagebox.askyesno('Somedo', 'Stop running task?'):
				self.stop.set()
		except:
			pass
		self.running_job = -1
		self.stop_set = True

	def __kill__(self):
		'Kill Somedo immediatly'
		if messagebox.askyesno('Somedo', 'Kill Somedo as fast as possible?\n\nAlready downloaded data mightbe lost!'):
			self.root.quit()

	def __worker__(self):
		'Execute jobs'
		for self.running_job in range(len(self.jobs)):
			self.worker.execute_job(
				self.jobs[self.running_job],
				headless=self.headless,
				stop=self.stop
			)
		self.running_job = -1
		self.__close2quit__()
		self.__enable_jobbuttons__()
		self.__enable_quitbutton__()

	def __showjob__(self):
		'Show what the worker is doing'
		fg = self.jobbuttons[self.running_job].cget('fg')
		bg = self.jobbuttons[self.running_job].cget('bg')
		while self.running_job >= 0:
			running = self.running_job
			self.jobbuttons[running].config(fg=bg)
			self.jobbuttons[running].config(bg=fg)
			sleep(0.75)
			self.jobbuttons[running].config(fg=fg)
			self.jobbuttons[running].config(bg=bg)
			sleep(0.75)

class LogHandler(Handler):
	'Logging to GUI'

	def __init__(self, text_msg):
		'Generate Handler from logging.Handler'
		super().__init__()
		self.text_msg = text_msg

	def emit(self, msg):
		'Overload logging.emit'
		msg = self.format(msg)
		def append():
			self.text_msg.configure(state='normal')
			self.text_msg.insert(END, msg + '\n')
#			self.text_msg.configure(state='disabled')
			self.text_msg.yview(END)
		self.text_msg.after(0, append)
