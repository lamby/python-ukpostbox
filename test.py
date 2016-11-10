#!/usr/bin/env python3

import os
import re
import sys
import requests
import itertools

from urllib.parse import urlencode
from http.cookiejar import CookieJar

re_pdf = re.compile(r'\?t=(?P<filename>[^\.]+)\.pdf')

username, password, dir_ = sys.argv[1:]

jar = CookieJar()
s = requests.Session()

r = s.post('https://client.ipostalmail.net/sec_login.aspx', data={
    'UserName': username,
    'Password': password,
}, cookies=jar)
r.raise_for_status()

r = s.get('https://client.ipostalmail.net/Mail', cookies=jar)
r.raise_for_status()

r = s.get('https://client.ipostalmail.net/divClientMailBoxAll.aspx?tp=1&p=1&_=1478274598252', cookies=jar)
r.raise_for_status()

ids = set()
for x in re_pdf.findall(r.text):
    ids.add(x)

for tracking_id in ids:
    for page in itertools.count(1):
        target = os.path.join(dir_, '{0}_{1:02d}.jpg'.format(
            tracking_id.replace(' ', '_'),
            page,
        ))

        if os.path.exists(target):
            break

        url = 'https://client.ipostalmail.net/ViewPDF?{}'.format(urlencode({
            'file': '{}.pdf'.format(tracking_id),
            'page': page,
        }))

        r = s.get(url, cookies=jar)
        r.raise_for_status()

        if r.headers['content-type'] != 'image/jpeg':
            break

        print("Saving {} -> {}".format(url, target))
        with open(target, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
