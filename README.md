Somedo Version 0.6.0 Alpha 2019-01-20


1 Introduction

Somedo is a downloader for social media platforms such as Facebook. The
downloaded sites/profiles are mainly stored as screenshots (PNG) and PDF files.
Additional data can also be found in other files such as CSV, JSON, HTML etc.

Somedo is designed for open source intelligence and law enforcement but it might be
helpful in other fileds too. Somedo has a modular structure. Modules for Facebook,
Instagram an Twitter are implemented so far.

Somedo ist in alpha state and might never leave beta due to constant development of
the social media platforms.

There are socialmedia platforms that require an account for the investigator to see
anything. Facebook is one of them. Register one or more accounts avoiding giving
away any real personal data. Set the privacy level and options for the accounts to
the maximum. The accepted accounts can then be used to optain data.

Make sure this is leagel for you in your country/state etc. I, Markus Thilo, the
developer of this open source software, is and will never be responsable for any
use of my tiny one man show development. Somedo is intended to protect the law
and may help aquiring information for journalistic or other goals that do
not interfere with legislation, privacy and human rights.


2 Use

You need Googel Chrome or Chromium to be installed.

As the downloads might take a while the idea is to add jobs to a list and start the
execution when you know what you want. The investigator can use the browser of his
choice to detect the targeted account(s) or criterias to download.

The modules should by default take several accounts as targets. Seperate them with
am comma or semicolon in the target(s) field.

You can add jobs hitting the large Buttons for Facebook, Instagram or Twitter. To
edit click the job in the list. The job list can be resetted usind "Purge jobs". Make
shure that in Configuration is the correct path of Google's Chrome or the open
version Chromium. You can change the file path (write it into the field or use the
hand symbol button). In addition you might want to change to directory where the
optained data will be stored by setting "Output directory".

Before launching make sure the used browser (Chrome/Chromium) is not running. Somedo
will hide the Google browser (in DEBUG mode you are able to see the browser working
but no PDF files will be created due to limitations of the browser's abilities -
info for developers only).

The jobs are execute by hitting "Start jobs". At this point the browser used by
Somedo has to be closes (if you use Chromium for Somedo, you can still work with
Chrome).

A running task can be aborted by the user hitting Stop running task (as the already
obtained data is stored, it might take a while before All done is reported).

It might be a good idea to observer the progress by looking into the target directories.
Chrome/Chromium ist started headless so you will not see anything while Somedo is
executing the given jobs. As Somedo does not use APIs but opens the pages as a human
user would do, it does not work very fast. The job which is currently executed is
shown by flashing of the list entry.

The login credentials can set in the Options field. These and the paths to Chrome/
Chromium and the output directory can be saved to file an loaded to avoid typing
marathons.

You can save the configuration
such as the output directory, path to Chrome/Chromium, user names, passwords etc. to
a config file to load it after a new launch of Somedo using Load configuration.


3 Modules

3.1 Facebook

At least one valid Facebook account is needed to login. You can use several accounts.
Especially with the Network option, it is likely that Facebook will block an account.
Somedo then will switch to the next geven credentials. In the fields Email and Password
you have to seperate email addresses (or phone numbers) are seperated by comma or
semicolon (e.g. "hans.gruber@mail.de, johnmclane@lapd.gov" / "hecklerandkoch, beretta").
If all investigator accounts have the same password, it does not to be repeated.

Targets might look like this: "1000023456789; holly.gennero". It is recommended to use
Facebook IDs. From complete URLs, Somedo tries to filter out the ID. The displayed
Facebook name is not individual and does not indicate a certain account. Somedo is NOT a
tool to search for an individual account.

Somedo might download data from your targeted accounts including befriendet or related
accounts. 

Limits are set as a lot of accounts are to large to get completely. A directory to store
the obtained data (creenshots, PDF, CSV, HTML etc.) is proposed but can be set (klick on
the hand symbol right to entry field. The screenshots are designed to fit on letter size
or DIN A4. Data is only obtained on the number screenshotted pages so the max. number of
screenshots also limits downloaded photos and the Extend Network option.

The Network option will try to get the Facebook Friends and on Extend Network accounts
that left comments or likes. Network Depth 0 downloads the Friend lists of the targets.
Depth 1 will should you a network visualisation. Look in the directory "Facebook/Network".
"Facebook/Network/network.html" will show Facebook Friendships with solid lines and
commentors/likers with dashed arrows. You can click on the nodes to get account infos.

If target is a Page ("pg") or a Facebook Group ("groups"), Somedo tries to aquire data but
this does not work very relieable. E.g. getting all members of large Facebook groups is
impossible. The possible number of screenshots is not only limited by Chrome/Chromium but
also by the Facebook servers. If there is no response from server Somedo will just abort
and go on to the next task.


3.2 Instagram

Landing gets the head of an Instagrm Web page. Media downloads photos and Videos. The
Max. number of screenshots will also limit the downloaded files (be aware that the max.
number of screenshots is NOT the number of files to download)


3.3 Twitter

By default the targets are Twitter accounts. the Search option takes Target(s) as search
pattern. You cannot use both in one job.


4. CLI

The CLI does not work when you are using the EXE file. In general I would recommend to use
install Python on your machine and also run the GUI with "python somedo.py".

Examples of commmand line use:

"python somedo.py Facebook -t holly.gennero -l Email=gruber@mail.de,mclane@lapd.gov Password=nakatomi -o Timeline=True"

It is possible to use a file which defines the jobs:

jobfile.txt

Facebook -l Email=hans.gruber@mail.de,johnmclane@lapd.gov Password=nakatomi -o Photos=True
Instagram -t karl,tony,theo -o Media=True

Start the jobs with "python somedo.py -f jobfile.txt".

Here are tho possible options/parameters

Facebook
	--target, -t
		string
	--login, -l
		Email=string
		Password=string
	--options, -o
		Timeline=bool (True or False)
		expandTimeline=bool
		translateTimeline=bool
		untilTimeline=string (format: Y-m-d, e.g. 2017-12-31)
		limitTimeline=int (e.g. 50)
		About=bool
		Photos=bool
		expandPhotos=bool
		translatePhotos=bool
		limitPhotos=int
		Network=bool
		depthNetwork=int
		extendNetwork=bool
				
Instagram
	--options, -o
		Media=bool
		limitPages=int

Twitter',
	--options, -o
		Search=bool
		Photos=bool
		limitPages=int


5 Development and License

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

