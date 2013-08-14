#!/usr/bin/env python
"""
With some modification.

Code Copyright (C) 2012-2013 Liam Stanley
Credits: Sean B. Palmer, Michael Yanovich
url.py - Code Url Module
http://code.liamstanley.net/
"""

import json
import re
from htmlentitydefs import name2codepoint
import unicode as uc
import urllib2
import web
from lxml import html
from bs4 import UnicodeDammit


EXCLUSION_CHAR = '!'
IGNORE = ['git.io', 'build.liamstanley.net']

# do not edit below this line unless you know what you're doing

url_finder = re.compile(r'(?u)(%s?(http|https|ftp)(://\S+\.\S+/?\S+?))' %
                        (EXCLUSION_CHAR))
r_entity = re.compile(r'&[A-Za-z0-9#]+;')

def tidy_title(title):
    title = title.strip()
    new_title = str()
    for char in title:
        unichar = uc.encode(char)
        if len(list(unichar)) <= 3:
            new_title += unichar
    return new_title

def find_title_lite(url):
    try:
        content = urllib2.urlopen(url).read()
        doc = UnicodeDammit(content, is_html=True)
        parser = html.HTMLParser(encoding=doc.original_encoding)
        root = html.document_fromstring(content, parser=parser)
        title = root.find('.//title').text_content()
        if title:
            return True, tidy_title(title)
        else:
            return False, 'No Title'
    except:
        return False, 'No Title'

def find_title(url):
    """
    This finds the title when provided with a string of a URL.
    """
    uri = url

    for item in IGNORE:
        if item in uri:
            return False, 'ignored'

    if not re.search('^((https?)|(ftp))://', uri):
        uri = 'http://' + uri

    if 'twitter.com' in uri:
        uri = uri.replace('#!', '?_escaped_fragment_=')

    uri = uc.decode(uri)

    ## proxy the lookup of the headers through .py
    pyurl = u'https://tumbolia.appspot.com/py/'
    code = 'import simplejson;'
    code += "req=urllib2.Request(u'%s', headers={'Accept':'text/html'});"
    code += "req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1;"
    code += "rv:17.0) Gecko/20100101 Firefox/17.0'); u=urllib2.urlopen(req);"
    code += "rtn=dict();"
    code += "rtn['headers'] = u.headers.dict;"
    code += "contents = u.read();"
    code += "con = str();"
    code += r'''exec "try: con=(contents).decode('utf-8')\n'''
    code += '''except: con=(contents).decode('iso-8859-1')";'''
    code += "rtn['read'] = con;"
    code += "rtn['url'] = u.url;"
    code += "rtn['geturl'] = u.geturl();"
    code += r"print simplejson.dumps(rtn)"
    query = code % uri
    try:
        temp = web.quote(query)
        u = web.get(pyurl + temp)
    except Exception, e:
        return False, e

    try:
        useful = json.loads(u)
    except:
        print 'Failed to parse JSON for:', uri, 'because:', u[:300],
        return False, u
    info = useful['headers']
    page = useful['read']

    try:
        mtype = info['content-type']
    except:
        return False, 'mtype failed'
    if not (('/html' in mtype) or ('/xhtml' in mtype)):
        return False, str(mtype)

    content = page
    regex = re.compile('<(/?)title( [^>]+)?>', re.IGNORECASE)
    content = regex.sub(r'<\1title>', content)
    regex = re.compile('[\'"]<title>[\'"]', re.IGNORECASE)
    content = regex.sub('', content)
    start = content.find('<title>')
    if start == -1:
        return False, 'NO <title> found'
    end = content.find('</title>', start)
    if end == -1:
        return False, 'NO </title> found'
    content = content[start + 7:end]
    content = content.strip('\n').rstrip().lstrip()
    title = content

    if len(title) > 200:
        title = title[:200] + '[...]'

    def e(m):
        entity = m.group()
        if entity.startswith('&#x'):
            cp = int(entity[3:-1], 16)
            meep = unichr(cp)
        elif entity.startswith('&#'):
            cp = int(entity[2:-1])
            meep = unichr(cp)
        else:
            char = name2codepoint[entity[1:-1]]
            meep = unichr(char)
        try:
            return uc.decode(meep)
        except:
            return uc.decode(uc.encode(meep))

    title = r_entity.sub(e, title)

    title = title.replace('\n', '')
    title = title.replace('\r', '')

    def remove_spaces(x):
        if '  ' in x:
            x = x.replace('  ', ' ')
            return remove_spaces(x)
        else:
            return x

    title = remove_spaces(title)

    new_title = str()
    for char in title:
        unichar = uc.encode(char)
        if len(list(uc.encode(char))) <= 3:
            new_title += uc.encode(char)
    title = new_title

    title = re.sub(r'(?i)dcc\ssend', '', title)

    if title:
        return True, title
    else:
        return False, 'No Title'


def remove_nonprint(text):
    new = str()
    for char in text:
        x = ord(char)
        if x > 32 and x < 126:
            new += char
    return new


def getTLD(url):
    url = url.strip()
    url = remove_nonprint(url)
    idx = 7
    if url.startswith('https://'):
        idx = 8
    elif url.startswith('ftp://'):
        idx = 6
    u = url[idx:]
    f = u.find('/')
    if f == -1:
        u = url
    else:
        u = url[0:idx] + u[0:f]
    return remove_nonprint(u)


def get_results(text):
    if not text:
        return list()
    a = re.findall(url_finder, text)
    k = len(a)
    i = 0
    display = list()
    passs = False
    while i < k:
        url = uc.encode(a[i][0])
        url = uc.decode(url)
        url = uc.iriToUri(url)
        url = remove_nonprint(url)
        domain = getTLD(url)
        if '//' in domain:
            domain = domain.split('//')[1]
        if not url.startswith(EXCLUSION_CHAR):
            #passs, page_title = find_title(url)
            passs, page_title = find_title_lite(url)
            display.append([page_title, url])
        i += 1
    return passs, display


if __name__ == '__main__':
    print __doc__.strip()
