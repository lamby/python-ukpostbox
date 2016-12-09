#!/usr/bin/env python3

import os
import re
import sys
import requests
import itertools

from urllib.parse import urlencode
from http.cookiejar import CookieJar

class UKPostbox(object):
    """
    Thinking of Signing up? Please use my referral URL:

        https://client.ipostalmail.net/About?Referrer=773f41c4fa4b4661bb8052955b34a261
    """

    re_pdf = re.compile(r'\?t=(?P<filename>[^\.]+)\.pdf')

    def __init__(self):
        self.session = requests.Session()
        self.cookies = CookieJar()

    def login(self, username, password):
        r = self.session.post('https://client.ipostalmail.net/sec_login.aspx', data={
            'UserName': username,
            'Password': password,
        }, cookies=self.cookies)

        r.raise_for_status()

    def get_ids(self):
        r = self.session.get(
            'https://client.ipostalmail.net/Mail',
            cookies=self.cookies,
        )
        r.raise_for_status()

        r = self.session.get(
            'https://client.ipostalmail.net/divClientMailBoxAll.aspx?tp=1&p=1',
            cookies=self.cookies,
        )
        r.raise_for_status()

        return {x for x in self.re_pdf.findall(r.text)}

    def get_page(self, tracking_id, page):
        url = 'https://client.ipostalmail.net/ViewPDF?{}'.format(urlencode({
            'file': '{}.pdf'.format(tracking_id),
            'page': page,
        }))

        r = self.session.get(url, cookies=self.cookies, stream=True)
        r.raise_for_status()

        if r.headers['content-type'] != 'image/jpeg':
            raise ValueError()

        return r.raw.data

def main(username, password, target):
    """
    Sync all mail to directory
    """

    client = UKPostbox()
    client.login(username, password)

    for tracking_id in client.get_ids():
        for page in itertools.count(1):
            filename = os.path.join(target, '{0}_{1:02d}.jpg'.format(
                tracking_id.replace(' ', '_'),
                page,
            ))

            if os.path.exists(filename):
                break

            try:
                page = client.get_page(tracking_id, page)
            except ValueError:
                break

            print("Saving {}".format(filename))

            with open(filename, 'wb') as f:
                f.write(page)

if __name__ == '__main__':
    try:
        sys.exit(main(*sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(2)
