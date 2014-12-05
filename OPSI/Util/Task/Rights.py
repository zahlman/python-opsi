#!/usr/bin/python
# -*- coding: utf-8 -*-

# This module is part of the desktop management solution opsi
# (open pc server integration) http://www.opsi.org

# Copyright (C) 2014 uib GmbH - http://www.uib.de/

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Setting access rights for opsi.

Opsi needs different access rights and ownerships for files and folders
during its use. To ease the setting of these permissions this modules
provides helpers for this task.


.. versionadded:: 4.0.6.1

:copyright:  uib GmbH <info@uib.de>
:author: Niko Wenselowski <n.wenselowski@uib.de>
:license: GNU Affero General Public License version 3
"""

import grp
import os
import pwd
import re

from OPSI.Backend.Backend import OPSI_GLOBAL_CONF
from OPSI.Logger import Logger
from OPSI.Types import forceHostId
from OPSI.Util import findFiles, getfqdn
from OPSI.Util.File.Opsi import OpsiConfFile

logger = Logger()

_OPSICONFD_USER = u'opsiconfd'
_ADMIN_GROUP = u'opsiadmin'
_CLIENT_USER = u'pcpatch'

try:
	_FILE_ADMIN_GROUP = OpsiConfFile().getOpsiFileAdminGroup()
except Exception:
	_FILE_ADMIN_GROUP = u'pcpatch'


# TODO: better ways!
def getDistribution():
	distribution = ''
	try:
		f = os.popen('lsb_release -d 2>/dev/null')
		distribution = f.read().split(':')[1].strip()
		f.close()
	except:
		pass
	return distribution


# TODO: use OPSI.System.Posix.Sysconfig for a more standardized approach
def getLocalFQDN():
	try:
		fqdn = getfqdn(conf=OPSI_GLOBAL_CONF)
		return forceHostId(fqdn)
	except Exception:
		raise Exception(
			u"Failed to get fully qualified domain name, "
			u"got '{0}'".format(fqdn)
		)


def setRights(path=u'/'):
	logger.notice(u"Setting rights")
	basedir = path
	if not os.path.isdir(basedir):
		basedir = os.path.dirname(basedir)

	clientUserUid = pwd.getpwnam(CLIENT_USER)[2]
	opsiconfdUid = pwd.getpwnam(_OPSICONFD_USER)[2]
	adminGroupGid = grp.getgrnam(_ADMIN_GROUP)[2]
	fileAdminGroupGid = grp.getgrnam(_FILE_ADMIN_GROUP)[2]

	distribution = getDistribution()

	depotDir = ''
	specialfiles = [u'setup.py', u'show_drivers.py', u'create_driver_links.py', u'opsi-deploy-client-agent', u'opsi-deploy-client-agent-old', u'winexe']
	dirnames = [u'/tftpboot/linux', u'/home/opsiproducts', u'/var/log/opsi', u'/etc/opsi', u'/var/lib/opsi']
	if 'suse linux enterprise server' in distribution.lower():
		dirnames = [u'/var/lib/tftpboot/opsi', u'/var/log/opsi', u'/etc/opsi', u'/var/lib/opsi', u'/var/lib/opsi/workbench']
	if not path.startswith('/etc') and not path.startswith('/tftpboot'):
		try:
			from OPSI.Backend.BackendManager import BackendManager
			backend = BackendManager(
				dispatchConfigFile=u'/etc/opsi/backendManager/dispatch.conf',
				backendConfigDir=u'/etc/opsi/backends',
				extensionConfigDir=u'/etc/opsi/backendManager/extend.d'
			)
			depot = backend.host_getObjects(type='OpsiDepotserver', id=getLocalFQDN())
			backend.backend_exit()
			if depot:
				depot = depot[0]
				depotUrl = depot.getDepotLocalUrl()
				if not depotUrl.startswith('file:///'):
					raise Exception(u"Bad repository local url '%s'" % depotUrl)
				depotDir = depotUrl[7:]
				if os.path.exists(depotDir):
					logger.info(u"Local depot directory '%s' found" % depotDir)
					dirnames.append(depotDir)
		except Exception as e:
			logger.error(e)

	if basedir.startswith('/opt/pcbin/install'):
		found = False
		for dirname in dirnames:
			if dirname.startswith('/opt/pcbin/install'):
				found = True
				break
		if not found:
			dirnames.append('/opt/pcbin/install')

	# TODO: split into paths here:
	# First we want a part that just gives (yield?) us the directories to travel through.
	# Then we want a part that processes that directory and sets the rights

	for dirname in dirnames:
		if not dirname.startswith(basedir) and not basedir.startswith(dirname):
			continue
		uid  = opsiconfdUid
		gid  = fileAdminGroupGid
		fmod = 0660
		dmod = 0770
		correctLinks = False

		isProduct = False
		if dirname not in (u'/var/lib/tftpboot/opsi', u'/tftpboot/linux', u'/var/log/opsi', u'/etc/opsi', u'/var/lib/opsi', u'/var/lib/opsi/workbench'):
			isProduct = True

		if dirname in (u'/var/lib/tftpboot/opsi', u'/tftpboot/linux'):
			fmod = 0664
			dmod = 0775
		if dirname in (u'/var/log/opsi', u'/etc/opsi'):
			gid = adminGroupGid
			correctLinks = True
		if dirname in (u'/home/opsiproducts', '/var/lib/opsi/workbench'):
			uid = -1
			dmod = 02770
		if dirname in (depotDir,):
			dmod = 02770

		if os.path.isfile(path):
			logger.debug(u"Setting ownership to {user}:{group} on file '{file}'".format(file=path, user=uid, group=gid))
			os.chown(path, uid, gid)
			logger.debug(u"Setting rights on file '%s'" % path)
			if isProduct:
				os.chmod(path, (os.stat(path)[0] | 0660) & 0770)
			else:
				os.chmod(path, fmod)
			continue

		startPath = dirname
		if basedir.startswith(dirname):
			startPath = basedir

		logger.notice(u"Setting rights on directory '%s'" % startPath)
		os.chown(startPath, uid, gid)
		os.chmod(startPath, dmod)
		for f in findFiles(startPath, prefix=startPath, returnLinks=correctLinks, excludeFile=re.compile("(.swp|~)$")):
			logger.debug(u"Setting ownership to {user}:{group} on file '{file}'".format(file=f, user=uid, group=gid))
			os.chown(f, uid, gid)
			if os.path.isdir(f):
				logger.debug(u"Setting rights on directory '%s'" % f)
				os.chmod(f, dmod)
			elif os.path.isfile(f):
				logger.debug(u"Setting rights on file '%s'" % f)
				if isProduct:
					if os.path.basename(f) in specialfiles:
						logger.debug(u"Setting rights on special file '{0}'".format(f))
						os.chmod(f, 0770)
					else:
						logger.debug(u"Setting rights on file '{0}'".format(f))
						os.chmod(f, (os.stat(f)[0] | 0660) & 0770)
				else:
					logger.debug(u"Setting rights {rights} on file '{file}'".format(file=f, rights=fmod))
					os.chmod(f, fmod)

		if startPath.startswith(u'/var/lib/opsi'):
			os.chmod(u'/var/lib/opsi', 0750)
			os.chown(u'/var/lib/opsi', clientUserUid, fileAdminGroupGid)
			sshDir = u'/var/lib/opsi/.ssh'
			if os.path.exists(sshDir):
				os.chown(sshDir, clientUserUid, fileAdminGroupGid)
				os.chmod(sshDir, 0750)
				idRsa = os.path.join(sshDir, u'id_rsa')
				if os.path.exists(idRsa):
					os.chmod(idRsa, 0640)
					os.chown(idRsa, clientUserUid, fileAdminGroupGid)
				idRsaPub = os.path.join(sshDir, u'id_rsa.pub')
				if os.path.exists(idRsaPub):
					os.chmod(idRsaPub, 0644)
					os.chown(idRsaPub, clientUserUid, fileAdminGroupGid)
				authorizedKeys = os.path.join(sshDir, u'authorized_keys')
				if os.path.exists(authorizedKeys):
					os.chmod(authorizedKeys, 0600)
					os.chown(authorizedKeys, clientUserUid, fileAdminGroupGid)
