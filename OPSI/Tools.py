#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
   = = = = = = = = = = = = = = = = = =
   =   opsi python library - Tools   =
   = = = = = = = = = = = = = = = = = =
   
   This module is part of the desktop management solution opsi
   (open pc server integration) http://www.opsi.org
   
   Copyright (C) 2006, 2007, 2008 uib GmbH
   
   http://www.uib.de/
   
   All rights reserved.
   
   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License version 2 as
   published by the Free Software Foundation.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
   
   @copyright:	uib GmbH <info@uib.de>
   @author: Jan Schneider <j.schneider@uib.de>
   @license: GNU General Public License version 2
"""

__version__ = '3.5'

# Imports
import json, os, random, base64, types
try:
	from hashlib import md5
except ImportError:
	from md5 import md5

# OS dependend imports
if (os.name == 'posix'):
	from duplicity import librsync

# OPSI imports
from OPSI.Logger import *
from OPSI.Types import *

# Get logger instance
logger = Logger()

RANDOM_DEVICE = '/dev/urandom'


def librsyncSignature(filename):
	if (os.name != 'posix'):
		raise NotImplementedError(u"Not implemented for non-posix os")
	
	(f, sf) = (None, None)
	try:
		f = open(filename, 'rb')
		sf = librsync.SigFile(f)
		sig = base64.encodestring(sf.read())
		f.close()
		sf.close()
		return sig
	except Exception, e:
		if f: f.close()
		if sf: sf.close()
		raise Exception(u"Failed to get librsync signature: %s" % e)

def librsyncPatchFile(oldfile, deltafile, newfile):
	if (os.name != 'posix'):
		raise NotImplementedError(u"Not implemented for non-posix os")
	
	logger.debug(u"Librsync : %s, %s, %s" % (oldfile, deltafile, newfile))
	if (oldfile == newfile):
		raise ValueError(u"Oldfile and newfile are the same file")
	if (deltafile == newfile):
		raise ValueError(u"deltafile and newfile are the same file")
	if (deltafile == oldfile):
		raise ValueError(u"oldfile and deltafile are the same file")
	
	(of, df, nf, pf) = (None, None, None, None)
	bufsize = 1024*1024
	try:
		of = open(oldfile, "rb")
		df = open(deltafile, "rb")
		nf = open(newfile, "wb")
		pf = librsync.PatchedFile(of, df)
		data = True
		while(data):
			data = pf.read(bufsize)
			nf.write(data)
		nf.close()
		pf.close()
		df.close()
		of.close()
	except Exception, e:
		if nf: nf.close()
		if pf: pf.close()
		if df: df.close()
		if of: of.close()
		raise Exception(u"Failed to patch file: %s" % e)

def md5sum(filename):
	f = open(filename, 'rb')
	m = md5()
	while True:
		d = f.read(524288)
		if not d:
			break
		m.update(d)
	f.close()
	return m.hexdigest()

def randomString(length):
	string = u''
	for i in range(length):
		string = string + random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
	return unicode(string)

def generateOpsiHostKey():
	key = u''
	if (os.name == 'posix'):
		logger.debug(u"Opening random device '%s' to generate opsi host key" % RANDOM_DEVICE)
		r = open(RANDOM_DEVICE)
		key = r.read(16)
		r.close()
		logger.debug("Random device closed")
		key = unicode(key.encode("hex"))
	else:
		logger.debug(u"Using python random module to generate opsi host key")
		while (len(key) < 32):
			key += random.choice([u'0',u'1',u'2',u'3',u'4',u'5',u'6',u'7',u'8',u'9',u'a',u'b',u'c',u'd',u'e',u'f'])
	return key

def timestamp(secs=0, dateOnly=False):
	''' Returns a timestamp of the current system time format: YYYY-mm-dd[ HH:MM:SS] '''
	if not secs:
		secs = time.time()
	if dateOnly:
		return time.strftime( u"%Y-%m-%d", time.localtime(secs) )
	else:
		return time.strftime( u"%Y-%m-%d %H:%M:%S", time.localtime(secs) )

def objectToBeautifiedText(obj, level=0):
	hspace = level*10
	text = u''
	if type(obj) is types.ListType:
		text += u' '*hspace + u'[ \n'
		for i in range( len(obj) ):
			if not type(obj[i]) in (types.DictType, types.ListType):
				text += u' '*hspace
			text += objectToBeautifiedText(obj[i], level+1)
			
			if (i < len(obj)-1):
				text += u',\n'
		text += u'\n' + u' '*hspace + u']'
	elif type(obj) is types.DictType:
		text += u' '*hspace + u'{ \n'
		i = 0
		for (key, value) in obj.items():
			text += u' '*hspace + u'"' + key + u'" : '
			if type(value) in (types.DictType, types.ListType):
				text += u'\n'
			text += objectToBeautifiedText(value, level+1)
			
			if (i < len(obj)-1):
				text += u',\n'
			i+=1
		text += u'\n' + u' '*hspace + u'}'
	else:
		if hasattr(json, 'dumps'):
			# python 2.6 json module
			text+= json.dumps(obj)
		else:
			text+= json.write(obj)
	return text

def objectToHtml(obj, level=0):
	hspace = level*10
	html = u''
	if type(obj) is types.ListType:
		html += u'&nbsp;'*hspace + u'[ <br />\n'
		for i in range( len(obj) ):
			if not type(obj[i]) in (types.DictType, types.ListType):
				html += u'&nbsp;'*hspace
			html += objectToHtml(obj[i], level+1)
			
			if (i < len(obj)-1):
				html += u',<br />\n'
		html += u'<br />\n' + u'&nbsp;'*hspace + u']'
	elif type(obj) is types.DictType:
		html += u'&nbsp;'*hspace + u'{ <br />\n'
		i = 0
		for (key, value) in obj.items():
			html += u'&nbsp;'*hspace + u'"<font class="json_key">' + key +  u'</font>": '
			if type(value) in (types.DictType, types.ListType):
				html += u'<br />\n'
			html += objectToHtml(value, level+1)
			
			if (i < len(obj)-1):
				html += u',<br />\n'
			i+=1
		html += u'<br />\n' + u'&nbsp;'*hspace + u'}'
	elif type(obj) in (str, unicode):
		html += obj.replace(u'\t', u'     ').replace(u' ', u'&nbsp;').replace(u'\n', u'<br />\n' + u'&nbsp;'*hspace)
	else:
		if hasattr(json, 'dumps'):
			# python 2.6 json module
			html += json.dumps(obj).replace(u'<', u'&lt;').replace(u'>', u'&gt;')
		else:
			html += json.write(obj).replace(u'<', u'&lt;').replace(u'>', u'&gt;')
	return html














