# -*- coding: utf-8 -*-

# This file is part of python-opsi.
# Copyright (C) 2006-2019 uib GmbH <info@uib.de>

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
Type forcing features.

This module contains various methods to ensure force a special type
on an object.

:copyright:	uib GmbH <info@uib.de>
:author: Jan Schneider <j.schneider@uib.de>
:author: Niko Wenselowski <n.wenselowski@uib.de>
:license: GNU Affero General Public License version 3
"""

import datetime
import os
import re
import sys
import time
import types

from OPSI.Logger import Logger

__all__ = (
	'args', 'forceActionProgress', 'forceActionRequest',
	'forceActionRequestList', 'forceActionResult', 'forceArchitecture',
	'forceArchitectureList', 'forceAuditState', 'forceBool', 'forceBoolList',
	'forceConfigId', 'forceDict', 'forceDictList', 'forceDomain',
	'forceEmailAddress', 'forceFilename', 'forceFloat', 'forceFqdn',
	'forceGroupId', 'forceGroupIdList', 'forceGroupType', 'forceGroupTypeList',
	'forceHardwareAddress', 'forceHardwareDeviceId', 'forceHardwareVendorId',
	'forceHostAddress', 'forceHostId', 'forceHostIdList', 'forceHostname',
	'forceIPAddress', 'forceInstallationStatus', 'forceInt', 'forceIntList',
	'forceIpAddress', 'forceLanguageCode', 'forceLanguageCodeList',
	'forceLicenseContractId', 'forceLicenseContractIdList', 'forceLicensePoolId',
	'forceLicensePoolIdList', 'forceList', 'forceNetmask',
	'forceNetworkAddress', 'forceObjectClass', 'forceObjectClassList',
	'forceObjectId', 'forceObjectIdList', 'forceOct', 'forceOpsiHostKey',
	'forceOpsiTimestamp', 'forcePackageCustomName', 'forcePackageVersion',
	'forcePackageVersionList', 'forceProductId', 'forceProductIdList',
	'forceProductPriority', 'forceProductPropertyId',
	'forceProductPropertyType', 'forceProductTargetConfiguration',
	'forceProductType', 'forceProductVersion', 'forceProductVersionList',
	'forceRequirementType', 'forceSoftwareLicenseId',
	'forceSoftwareLicenseIdList', 'forceTime', 'forceUnicode',
	'forceUnicodeList', 'forceUnicodeLower', 'forceUnicodeLowerList',
	'forceUnicodeUpper', 'forceUniqueList', 'forceUnsignedInt', 'forceUrl'
)

encoding = sys.getfilesystemencoding()
logger = Logger()

_HARDWARE_ID_REGEX = re.compile(r'^[a-fA-F0-9]{4}$')
_OPSI_TIMESTAMP_REGEX = re.compile(r'^(\d{4})-?(\d{2})-?(\d{2})\s?(\d{2}):?(\d{2}):?(\d{2})\.?\d*$')
_OPSI_DATE_REGEX = re.compile(r'^(\d{4})-?(\d{2})-?(\d{2})$')
_FQDN_REGEX = re.compile(r'^[a-z0-9][a-z0-9\-]{,63}\.((\w+\-+)|(\w+\.))*\w{1,63}\.\w{2,16}\.?$')
_HARDWARE_ADDRESS_REGEX = re.compile(r'^([0-9a-f]{2})[:-]?([0-9a-f]{2})[:-]?([0-9a-f]{2})[:-]?([0-9a-f]{2})[:-]?([0-9a-f]{2})[:-]?([0-9a-f]{2})$')
_IP_ADDRESS_REGEX = re.compile(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
_NETMASK_REGEX = re.compile(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
_NETWORK_ADDRESS_REGEX = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/([0-3]?[0-9]|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$')
_URL_REGEX = re.compile(r'^[a-z0-9]+://[/a-zA-Z0-9]')
_OPSI_HOST_KEY_REGEX = re.compile(r'^[0-9a-f]{32}$')
_PRODUCT_VERSION_REGEX = re.compile(r'^[a-z0-9.]{1,32}$')
_PACKAGE_VERSION_REGEX = re.compile(r'^[a-z0-9.]{1,16}$')
_PRODUCT_ID_REGEX = re.compile(r'^[a-z0-9-_\.]{1,128}$')
_PACKAGE_CUSTOM_NAME_REGEX = re.compile(r'^[a-zA-Z0-9]+$')
_PRODUCT_PROPERTY_ID_REGEX = re.compile(r'^\S+$')
_CONFIG_ID_REGEX = re.compile(r'^\S+$')
_GROUP_ID_REGEX = re.compile(r'^[a-z0-9][a-z0-9-_. ]*$')
_OBJECT_ID_REGEX = re.compile(r'^[a-z0-9][a-z0-9-_. ]*$')
_EMAIL_REGEX = re.compile(r'^(([A-Za-z0-9]+_+)|([A-Za-z0-9]+\-+)|([A-Za-z0-9]+\.+)|([A-Za-z0-9]+\++))*[A-Za-z0-9]+@((\w+\-+)|(\w+\.))*\w*')
_DOMAIN_REGEX = re.compile(r'^((\w+\-+)|(\w+\.))*\w{1,63}\.\w{2,16}\.?$')
_HOSTNAME_REGEX = re.compile(r'^[a-z0-9][a-z0-9\-]*$')
_LICENSE_CONTRACT_ID_REGEX = re.compile(r'^[a-z0-9][a-z0-9-_. :]*$')
_SOFTWARE_LICENSE_ID_REGEX = re.compile(r'^[a-z0-9][a-z0-9-_. :]*$')
_LICENSE_POOL_ID_REGEX = re.compile(r'^[a-z0-9][a-z0-9-_. :]*$')
_LANGUAGE_CODE_REGEX = re.compile(r'^([a-z]{2,3})[-_]?([a-z]{4})?[-_]?([a-z]{2})?$')
_ARCHITECTURE_REGEX = re.compile(r'^(x86|x64)$')


def forceList(var):
	if not isinstance(var, (set, list, tuple, types.GeneratorType)):
		return [var]

	return list(var)


def forceUnicode(var):
	if var is None:
		return u""
	if isinstance(var, str):
		return var
	elif (os.name == 'nt') and isinstance(var, WindowsError):
		try:
			return u"[Error %s] %s" % (var.args[0], var.args[1])
		except:
			return str(var)
	try:
		if isinstance(var, bytes):
			return var.decode()
	except Exception:
		pass

	try:
		var = var.__repr__()
		if isinstance(var, str):
			return var
		return str(var, 'utf-8', 'replace')
	except Exception:
		pass

	return str(var)


def forceUnicodeLower(var):
	return forceUnicode(var).lower()


def forceUnicodeUpper(var):
	return forceUnicode(var).upper()


def forceUnicodeList(var):
	return [forceUnicode(element) for element in forceList(var)]


def forceDictList(var):
	return [forceDict(element) for element in forceList(var)]


def forceUnicodeLowerList(var):
	return [forceUnicodeLower(element) for element in forceList(var)]


def forceBool(var):
	if isinstance(var, bool):
		return var
	elif isinstance(var, str):
		if len(var) <= 5:  # longest word is 5 characters ("false")
			lowValue = var.lower()
			if lowValue in ('true', 'yes', 'on', '1'):
				return True
			elif lowValue in ('false', 'no', 'off', '0'):
				return False

	return bool(var)


def forceBoolList(var):
	return [forceBool(element) for element in forceList(var)]


def forceInt(var):
	if isinstance(var, int):
		return var
	try:
		return int(var)
	except Exception as e:
		raise ValueError(u"Bad int value '%s': %s" % (var, e))


def forceIntList(var):
	return [forceInt(element) for element in forceList(var)]


def forceUnsignedInt(var):
	var = forceInt(var)
	if var < 0:
		var = -1 * var
	return var


def forceOct(var):
	if isinstance(var, int):
		return var

	try:
		octValue = ''
		for i, x in enumerate(forceUnicode(var)):
			x = forceInt(x)
			if x > 7:
				raise ValueError(u'{0!r} is too big'.format(x))
			elif i == 0 and x != '0':
				octValue += '0'
			octValue += str(x)

		octValue = eval('0o' + octValue)
		return octValue
	except Exception as error:
		raise ValueError(u"Bad oct value {0!r}: {1}".format(var, error))


def forceFloat(var):
	if isinstance(var, float):
		return var

	try:
		return float(var)
	except Exception as e:
		raise ValueError(u"Bad float value '%s': %s" % (var, e))


def forceDict(var):
	if var is None:
		return {}
	elif isinstance(var, dict):
		return var

	raise ValueError(u"Not a dict '%s'" % var)


def forceTime(var):
	"""
	Convert `var` to a time.struct_time.

	If no conversion is possible a `ValueError` will be raised.
	"""
	if isinstance(var, time.struct_time):
		return var
	elif isinstance(var, datetime.datetime):
		var = time.mktime(var.timetuple()) + var.microsecond / 1E6

	if isinstance(var, (int, float)):
		return time.localtime(var)

	raise ValueError(u"Not a time {0!r}".format(var))


def forceHardwareVendorId(var):
	var = forceUnicodeUpper(var)
	if not re.search(_HARDWARE_ID_REGEX, var):
		raise ValueError(u"Bad hardware vendor id '%s'" % var)
	return var


def forceHardwareDeviceId(var):
	var = forceUnicodeUpper(var)
	if not re.search(_HARDWARE_ID_REGEX, var):
		raise ValueError(u"Bad hardware device id '%s'" % var)
	return var


def forceOpsiTimestamp(var):
	"""
	Make `var` an opsi-compatible timestamp.

	This is a string with the format "YYYY-MM-DD HH:MM:SS".

	If a conversion is not possible a `ValueError` will be raised.
	"""
	if not var:
		return u'0000-00-00 00:00:00'
	elif isinstance(var, datetime.datetime):
		return forceUnicode(var.strftime('%Y-%m-%d %H:%M:%S'))

	var = forceUnicode(var)
	match = re.search(_OPSI_TIMESTAMP_REGEX, var)
	if not match:
		match = re.search(_OPSI_DATE_REGEX, var)
		if not match:
			raise ValueError(u"Bad opsi timestamp: {0!r}".format(var))

		return u'%s-%s-%s 00:00:00' % (match.group(1), match.group(2), match.group(3))

	return u'%s-%s-%s %s:%s:%s' % (match.group(1), match.group(2), match.group(3), match.group(4), match.group(5), match.group(6))


def forceFqdn(var):
	var = forceObjectId(var)
	if not _FQDN_REGEX.search(var):
		raise ValueError(u"Bad fqdn: '%s'" % var)
	if var.endswith('.'):
		var = var[:-1]
	return var


forceHostId = forceFqdn


def forceHostIdList(var):
	return [forceHostId(element) for element in forceList(var)]


def forceHardwareAddress(var):
	var = forceUnicodeLower(var)
	if not var:
		return var

	match = re.search(_HARDWARE_ADDRESS_REGEX, var)
	if not match:
		raise ValueError(u"Bad hardware address: %s" % var)

	return u'%s:%s:%s:%s:%s:%s' % (match.group(1), match.group(2), match.group(3), match.group(4), match.group(5), match.group(6))


def forceIPAddress(var):
	var = forceUnicodeLower(var)
	if not re.search(_IP_ADDRESS_REGEX, var):
		raise ValueError(u"Bad ip address: '%s'" % var)
	return var


forceIpAddress = forceIPAddress


def forceHostAddress(var):
	var = forceUnicodeLower(var)
	try:
		try:
			try:
				var = forceIpAddress(var)
			except Exception:
				var = forceFqdn(var)
		except Exception:
			var = forceHostname(var)
	except Exception:
		raise ValueError(u"Bad host address: '%s'" % var)
	return var


def forceNetmask(var):
	var = forceUnicodeLower(var)
	if not re.search(_NETMASK_REGEX, var):
		raise ValueError(u"Bad netmask: '%s'" % var)
	return var


def forceNetworkAddress(var):
	var = forceUnicodeLower(var)
	if not re.search(_NETWORK_ADDRESS_REGEX, var):
		raise ValueError(u"Bad network address: '%s'" % var)
	return var


def forceUrl(var):
	"""
	Forces ``var`` to be an valid URL.

	:rtype: str
	"""
	var = forceUnicode(var)
	if not _URL_REGEX.search(var):
		raise ValueError(u"Bad url: '{0}'".format(var))
	return var


def forceOpsiHostKey(var):
	var = forceUnicodeLower(var)
	if not re.search(_OPSI_HOST_KEY_REGEX, var):
		raise ValueError(u"Bad opsi host key: {!r}".format(var))

	return var


def forceProductVersion(var):
	var = forceUnicode(var)
	if not _PRODUCT_VERSION_REGEX.search(var):
		raise ValueError(u"Bad product version: '%s'" % var)
	return var


def forceProductVersionList(var):
	return [forceProductVersion(element) for element in forceList(var)]


def forcePackageVersion(var):
	var = forceUnicode(var)
	if not _PACKAGE_VERSION_REGEX.search(var):
		raise ValueError(u"Bad package version: '%s'" % var)
	return var


def forcePackageVersionList(var):
	return [forcePackageVersion(element) for element in forceList(var)]


def forceProductId(var):
	var = forceObjectId(var)
	if not _PRODUCT_ID_REGEX.search(var):
		raise ValueError(u"Bad product id: '%s'" % var)
	return var


def forceProductIdList(var):
	return [forceProductId(element) for element in forceList(var)]


def forcePackageCustomName(var):
	var = forceUnicodeLower(var)
	if not _PACKAGE_CUSTOM_NAME_REGEX.search(var):
		raise ValueError(u"Bad package custom name: '%s'" % var)
	return var


def forceProductType(var):
	lowercaseVar = forceUnicodeLower(var)
	if lowercaseVar in ('localboot', 'localbootproduct'):
		return u'LocalbootProduct'
	elif lowercaseVar in ('netboot', 'netbootproduct'):
		return u'NetbootProduct'
	else:
		raise ValueError(u"Unknown product type: '%s'" % var)


def forceProductPropertyId(var):
	var = forceUnicodeLower(var)
	if not _PRODUCT_PROPERTY_ID_REGEX.search(var):
		raise ValueError(u"Bad product property id: '%s'" % var)
	return var


def forceConfigId(var):
	var = forceUnicodeLower(var)
	if not _CONFIG_ID_REGEX.search(var):
		raise ValueError(u"Bad config id: '%s'" % var)
	return var


def forceProductPropertyType(var):
	value = forceUnicodeLower(var)
	if value in ('unicode', 'unicodeproductproperty'):
		return u'UnicodeProductProperty'
	elif value in ('bool', 'boolproductproperty'):
		return u'BoolProductProperty'
	else:
		raise ValueError(u"Unknown product property type: '%s'" % var)


def forceProductPriority(var):
	var = forceInt(var)
	if var < -100:
		var = -100
	elif var > 100:
		var = 100

	return var


def forceFilename(var):
	return forceUnicode(var)


def forceProductTargetConfiguration(var):
	var = forceUnicodeLower(var)
	if var and var not in ('installed', 'always', 'forbidden', 'undefined'):
		raise ValueError(u"Bad product target configuration: '%s'" % var)
	return var


def forceInstallationStatus(var):
	var = forceUnicodeLower(var)
	if var and var not in ('installed', 'not_installed', 'unknown'):
		raise ValueError(u"Bad installation status: '%s'" % var)
	return var


def forceActionRequest(var):
	var = forceUnicodeLower(var)
	if var:
		if var == 'undefined':
			var = None
		elif var not in ('setup', 'uninstall', 'update', 'always', 'once', 'custom', 'none'):
			raise ValueError(u"Bad action request: '%s'" % var)

	return var


def forceActionRequestList(var):
	return [forceActionRequest(element) for element in forceList(var)]


def forceActionProgress(var):
	return forceUnicode(var)


def forceActionResult(var):
	var = forceUnicodeLower(var)
	if var and var not in ('failed', 'successful', 'none'):
		raise ValueError(u"Bad action result: '%s'" % var)
	return var


def forceRequirementType(var):
	var = forceUnicodeLower(var)
	if not var:
		return None
	elif var not in ('before', 'after'):
		raise ValueError(u"Bad requirement type: '%s'" % var)
	return var


def forceObjectClass(var, objectClass):
	if isinstance(var, objectClass):
		return var

	exception = None
	if isinstance(var, str) and var.lstrip().startswith('{'):
		from OPSI.Util import fromJson

		try:
			var = fromJson(var)
		except Exception as error:
			exception = error
			logger.debug(u"Failed to get object from json %s: %s", var, error)

	if isinstance(var, dict):
		if 'type' not in var:
			raise ValueError(u"Key 'type' missing in hash {0!r}".format(var))

		import OPSI.Object
		try:
			c = eval('OPSI.Object.%s' % var['type'])
			if issubclass(c, objectClass):
				var = c.fromHash(var)
		except AttributeError as error:
			if "module 'OPSI.Object' has no attribute" in str(error):
				error = ValueError("Invalild object type: {0}".format(var['type']))

			exception = error
			logger.debug(u"Failed to get object from dict %s: %s", var, error)
		except Exception as error:
			exception = error
			logger.debug(u"Failed to get object from dict %s: %s", var, error)

	if not isinstance(var, objectClass):
		if exception is not None:
			raise ValueError(u"Not a %s: '%s': %s" % (objectClass, var, exception))
		else:
			raise ValueError(u"Not a %s: '%s'" % (objectClass, var))

	return var


def forceObjectClassList(var, objectClass):
	return [forceObjectClass(element, objectClass) for element in forceList(var)]


def forceGroupId(var):
	var = forceObjectId(var)
	if not _GROUP_ID_REGEX.search(var):
		raise ValueError(u"Bad group id: '%s'" % var)
	return var


def forceGroupType(var):
	lowercaseValue = forceUnicodeLower(var)

	if lowercaseValue == 'hostgroup':
		return u'HostGroup'
	elif lowercaseValue == 'productgroup':
		return u'ProductGroup'
	else:
		raise ValueError(u"Unknown group type: '%s'" % var)


def forceGroupTypeList(var):
	return [forceGroupType(element) for element in forceList(var)]


def forceGroupIdList(var):
	return [forceGroupId(element) for element in forceList(var)]


def forceObjectId(var):
	var = forceUnicodeLower(var).strip()
	if not _OBJECT_ID_REGEX.search(var):
		raise ValueError(u"Bad object id: '%s'" % var)
	return var


def forceObjectIdList(var):
	return [forceObjectId(element) for element in forceList(var)]


def forceEmailAddress(var):
	var = forceUnicodeLower(var)
	if not _EMAIL_REGEX.search(var):
		raise ValueError(u"Bad email address: '%s'" % var)
	return var


def forceDomain(var):
	var = forceUnicodeLower(var)
	if not _DOMAIN_REGEX.search(var):
		raise ValueError(u"Bad domain: '%s'" % var)
	return var


def forceHostname(var):
	var = forceUnicodeLower(var)
	if not _HOSTNAME_REGEX.search(var):
		raise ValueError(u"Bad hostname: '%s'" % var)
	return var


def forceLicenseContractId(var):
	var = forceUnicodeLower(var)
	if not _LICENSE_CONTRACT_ID_REGEX.search(var):
		raise ValueError(u"Bad license contract id: '%s'" % var)
	return var


def forceLicenseContractIdList(var):
	return [forceLicenseContractId(element) for element in forceList(var)]


def forceSoftwareLicenseId(var):
	var = forceUnicodeLower(var)
	if not _SOFTWARE_LICENSE_ID_REGEX.search(var):
		raise ValueError(u"Bad software license id: '%s'" % var)
	return var


def forceSoftwareLicenseIdList(var):
	return [forceSoftwareLicenseId(element) for element in forceList(var)]


def forceLicensePoolId(var):
	var = forceUnicodeLower(var)
	if not _LICENSE_POOL_ID_REGEX.search(var):
		raise ValueError(u"Bad license pool id: '%s'" % var)
	return var


def forceLicensePoolIdList(var):
	return [forceLicensePoolId(element) for element in forceList(var)]


def forceAuditState(var):
	var = forceInt(var)
	if var not in (0, 1):
		raise ValueError(u"Bad audit state value: {0}".format(var))
	return var


def forceLanguageCode(var):
	var = forceUnicodeLower(var)
	match = _LANGUAGE_CODE_REGEX.search(var)
	if not match:
		raise ValueError(u"Bad language code: '%s'" % var)
	var = match.group(1)
	if match.group(2):
		var += u'-' + match.group(2)[0].upper() + match.group(2)[1:]
	if match.group(3):
		var += u'-' + match.group(3).upper()
	return var


def forceLanguageCodeList(var):
	return [forceLanguageCode(element) for element in forceList(var)]


def forceArchitecture(var):
	var = forceUnicodeLower(var)
	if not _ARCHITECTURE_REGEX.search(var):
		raise ValueError(u"Bad architecture: '%s'" % var)
	return var


def forceArchitectureList(var):
	return [forceArchitecture(element) for element in forceList(var)]


def forceUniqueList(_list):
	cleanedList = []
	for entry in _list:
		if entry not in cleanedList:
			cleanedList.append(entry)
	return cleanedList


def args(*vars, **typeVars):
	"""Function to populate an object with passed on keyword args.
	This is intended to be used as a decorator.
	Classes using this decorator must explicitly inherit from object or a subclass of object.

	.. code-block:: python

		@args()			#works
		class Foo(object):
			pass

		@args()			#works
		class Bar(Foo):
			pass

		@args()			#does not work
		class Foo():
			pass

		@args()			#does not work
		class Foo:
			pass
	"""
	vars = list(vars)

	def wrapper(cls):
		def new(typ, *args, **kwargs):
			if getattr(cls, "__base__", None) in (object, None):
				obj = object.__new__(typ)  # Suppress deprecation warning
			else:
				obj = cls.__base__.__new__(typ, *args, **kwargs)

			vars.extend(list(typeVars.keys()))
			ka = kwargs.copy()

			for var in vars:
				varName = var.lstrip("_")
				if varName in ka:
					if var in typeVars:
						func = typeVars[var]
						ka[var] = func(ka[varName])
					else:
						ka[var] = ka[varName]
				else:
					ka[var] = None

			for key, value in ka.items():
				if getattr(obj, key, None) is None:
					setattr(obj, key, value)

			return obj

		cls.__new__ = staticmethod(new)
		return cls

	return wrapper
