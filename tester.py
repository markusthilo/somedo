#!/usr/bin/env python3
from base.worker import *

#jobs = [['Facebook', 'steffi.li.white', {'Timeline': {'Expand': True, 'Translate': True, 'Visitors': True, 'Until': '2000-01-01', 'Limit': 50}}]]

#jobs = [['Facebook', 'annoba', {'Timeline': {'Expand': True, 'Translate': False, 'Visitors': True, 'Until': '2000-01-01', 'Limit': 10}, 'About': {}}]]

jobs = [['Facebook', 'annoba', {'Friends': {}}]]

config = {'Output directory': '/home/user/Downloads', 'Chrome': '/usr/bin/chromium', 'Facebook': {'Email': 'hans.gruber@mail.de', 'Password': 'johnmclane'}, 'Instagram': {}, 'Twitter': {}}
worker = Worker()
message = worker.execute(jobs, config, headless=False)
print(message)