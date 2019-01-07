1 Introduction

Somedo is a downloader for Social Media Platforms such as Facebook.
The downloaded sites/profiles are mainly stored as screenshots (PNG) and PDF files.
Additional data can also be found in other files such as CSV, JSON etc.
The goal is to provide an usable tool to download open content from social media
platforms. Somedo has a modular structure. So far, Somedo is usable for Facebook,
Instagram an Twitter. Somedo ist in alpha state and might never leave beta.


2 Quick Start Guide

Install EXE on Windows

Download somedo_win_v*.zip from https://sourceforge.net/projects/somedo/files/
and unzip it in some folder. To run Somedo Google Chrome or Chromium has to be
installed. Before running Somedo, you should close all Chrome/Chromium instances.
Start Somedo by double clicking somedo.exe. Do not remove directories or files that
come within the zip file.


Install on Linux

Download somedo_v*.zip from https://sourceforge.net/projects/somedo/files/
and unzip it in some folder. For Somedo the Chromium Browser or Google Chrome has
to be installed. The code should work on any current Python 3 which should come
with your distro. You should manually install the following libraries:

TkInter library
(e.g. pip install tkinter or apt install python3-tk)

Requests library
(e.g. pip install requests or apt install python3-requests)

WebSocket client library
(e.g. pip install websocket-client or apt install python3-websocket)

Htm2text library
(e.g. pip install html2text or apt install python3-html2text)

The easiest way ist to start somedo is by executing the file (bash script) somedo
by clicking in a file browser or start from a terminal with:

$./somedo

Using Python directly also works:
$ python3 somedo.py


Use

The GUI allows to add jobs that can be executed with Start jobs. If Chrome/Chromium
was not fount automatically, hit the Chrome button. You can save the configuration
such as the output directory, path to Chrome/Chromium, user names, passwords etc. to
a config file to load it after a new launch of Somedo using Load configuration.
A running task can be aborted by the user hitting Stop running task (as the already
obtained data is stored, it might take a while before All done is reported).
You have to create jobs and add them to the jobs list with Add job. In general more
than one Target account per job can be set (exception e.g.: Twitter Search ).
Limit counts the screenshots. The number of PDF pages may differ. If the limit is set
too high, Chrome/Chromium might not be able to handle the page.
It might be a good idea to observer the progress by looking into the target directories.
Chrome/Chromium ist started headless so you will not see anything while Somedo is
executing the given jobs. As Somedo does not use APIs but opens the pages as a human
user would do, it does not work very fast.


3 Modules

Facebook

A Facebook account is needed to login. Several target Facebook accounts can be specified.
In the GUI these are separated by semicolon. For example, Target account(s): might look like
this:

1000023456789; holly.gennaro

It is recommended to use Facebook IDs. From complete URLs, Somedo tries to filter
out the ID. The displayed Facebook name of a Facebook account is not individual and does
not indicate a certain account.
A target directory is automatically proposed, in which the obtained screenshots are stored.
The screenshots should be printable on letter size or DIN A4. In addition, text files are
generated (for most actions).
The Option Timeline downloads the Facebook timeline on personal profiles or Facebook groups.
If target is a rpfessional account ("pg"), the posts are downloaded instead. With this option
you can specify, if you want to unfold comments etc. and/or translations. It is also possible
to get the Visitors (Facebook users that left comments, likes. etc.) as a CSV and a JSON file.
Until sets a date (year-month-day) when to abort expanding the timeline (default is 1 year in
the past). Facebook uses UTC, so somedo does too.
The option About downloads the About section of the targeted Facebook account. Photos tries
to take screenshots from the pictures in the Photop section. For the comments Expand and
Translate and is available like in Timeline.
The option Friends should store friend lists to as CSV and JSON (or members on Group of group
accounts) and create in addition to screenshots. Network gets friends of friends and so on.
The recursion is limited by Recursion depth (default is 1 = friends of targets, 2 = friends of
friends). It seems Facebook does not like unlicensed data mining, so while using Network your
investigator account might get blocked for a while.


Instagram

Landing gets the head of an Instagrm Web page. Media downloads Ohotos and Videos.


Twitter

User targets Twitter Accounts. Search takes Target(s) as search pattern. You cannot use both
in one job.


4 Development and License

The use, development, distribution, etc. of the script is subject to the restrictions of
GPL Version 3.
If you are interested in the code, visit the project on Github:

https://github.com/markusthilo/somedo

The network visualisation uses Vis.js which is dual licensed under both Apache 2.0 and MIT:

http://visjs.org
http://www.apache.org/licenses/LICENSE-2.0
http://opensource.org/licenses/MIT

The tool is in alpha state and propably will not be stable enough to have a final release
ever. Constant changes and inhomogeneity of pages require permanent adaptation and development.
The completeness and correctness of the information obtained can never be guaranteed.
The developer is not responsible for the use of the tool.
You are welcome to participate or donate to the development. Feel free to report bugs or
give suggestions by email to:

markus.thilo@gmail.com


