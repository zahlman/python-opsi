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
Dispatching backend calls to multiple backends.

:copyright: uib GmbH <info@uib.de>
:author: Jan Schneider <j.schneider@uib.de>
:author: Niko Wenselowski <n.wenselowski@uib.de>
:license: GNU Affero General Public License version 3
"""

import importlib
import inspect
import os
import re
import types
from functools import lru_cache

from OPSI.Backend.Base import (
	Backend, ConfigDataBackend, getArgAndCallString)
from OPSI.Exceptions import BackendConfigurationError
from OPSI.Logger import Logger
from OPSI.Types import forceList
from OPSI.Util.File.Opsi import BackendDispatchConfigFile

from .Config import loadBackendConfig

__all__ = ('BackendDispatcher', )

logger = Logger()


class BackendDispatcher(Backend):
	def __init__(self, **kwargs):
		Backend.__init__(self, **kwargs)

		self._dispatchConfigFile = None
		self._dispatchConfig = []
		self._dispatchIgnoreModules = []
		self._backendConfigDir = None
		self._backends = {}
		self._context = self

		for (option, value) in kwargs.items():
			option = option.lower()
			if option == 'dispatchconfig':
				self._dispatchConfig = value
			elif option == 'dispatchconfigfile':
				self._dispatchConfigFile = value
			elif option == 'dispatchignoremodules' and value:
				self._dispatchIgnoreModules = forceList(value)
			elif option == 'backendconfigdir':
				self._backendConfigDir = value
			elif option == 'context':
				self._context = value

		if self._dispatchConfigFile:
			logger.info("Loading dispatch config file '%s'", self._dispatchConfigFile)
			self.__loadDispatchConfig()

		if not self._dispatchConfig:
			raise BackendConfigurationError("Dispatcher not configured")

		self.__loadBackends(dict(kwargs))
		self._createInstanceMethods()

	def __repr__(self):
		additionalInformation = []
		try:
			if self._dispatchIgnoreModules:
				additionalInformation.append('dispatchIgnoreModules={0!r}'.format(self._dispatchIgnoreModules))

			if self._dispatchConfigFile:
				additionalInformation.append('dispatchConfigFile={0!r}'.format(self._dispatchConfigFile))
			elif self._dispatchConfig:
				additionalInformation.append('dispatchConfig={0!r}'.format(self._dispatchConfig))

			if self._context != self:
				additionalInformation.append('context={0!r}'.format(self._context))
		except AttributeError:
			# Can happen during initialisation
			pass

		return '<{0}({1})>'.format(self.__class__.__name__, ', '.join(additionalInformation))

	def __loadDispatchConfig(self):
		if not self._dispatchConfigFile:
			raise BackendConfigurationError("No dispatch config file defined")

		try:
			self._dispatchConfig = _loadDispatchConfig(self._dispatchConfigFile)
			logger.debug("Read dispatch config from file %s: %s", self._dispatchConfigFile, self._dispatchConfig)
		except Exception as err:
			raise BackendConfigurationError(
				f"Failed to load dispatch config file '{self._dispatchConfigFile}': {err}"
			) from err

	def __loadBackends(self, kwargs=None):
		if not self._backendConfigDir:
			raise BackendConfigurationError("Backend config dir not given")

		if not os.path.exists(self._backendConfigDir):
			raise BackendConfigurationError(f"Backend config dir '{self._backendConfigDir}' not found")

		collectedBackends = set()
		for pattern, backends in self._dispatchConfig:
			for backend in backends:
				if not backend:
					raise BackendConfigurationError(
						f"Bad dispatcher config: {pattern} has empty target backend: {backends}"
					)

				collectedBackends.add(backend)

		for backend in collectedBackends:
			self._backends[backend] = {}
			backendConfigFile = os.path.join(self._backendConfigDir, '%s.conf' % backend)
			logger.info("Loading backend config '%s'", backendConfigFile)
			backend_config = loadBackendConfig(backendConfigFile)
			if not backend_config['module']:
				raise BackendConfigurationError(
					f"No module defined in backend config file '{backendConfigFile}'"
				)
			if backend_config['module'] in self._dispatchIgnoreModules:
				logger.notice("Ignoring module '%s', backend '%s'", backend_config['module'], backend)
				del self._backends[backend]
				continue
			if not isinstance(backend_config['config'], dict):
				raise BackendConfigurationError(
					"Bad type for config var in backend config file '{backendConfigFile}', has to be dict"
				)
			backend_config["config"]["context"] = self
			moduleName = f"OPSI.Backend.{backend_config['module']}"
			backendClassName = f"{backend_config['module']}Backend"
			backend_module = importlib.import_module(moduleName)
			cargs = dict(backend_config['config'])
			cargs.update(kwargs or {})
			self._backends[backend]["instance"] = getattr(backend_module, backendClassName)(**cargs)
		logger.info("Dispatcher backends: %s", list(self._backends.keys()))

	def _createInstanceMethods(self):  # pylint: disable=too-many-branches
		logger.debug("BackendDispatcher is creating instance methods")
		classes = [ConfigDataBackend]
		classes.extend([ backend["instance"].__class__ for backend in self._backends.values() ])
		for Class in classes:  # pylint: disable=too-many-nested-blocks
			for methodName, functionRef in inspect.getmembers(Class, inspect.isfunction):
				if getattr(functionRef, "no_export", False):
					continue
				if methodName.startswith('_'):
					# Not a public method
					continue
				logger.trace("Found public %s method '%s'", Class.__name__, methodName)

				if hasattr(self, methodName):
					logger.trace("%s: skipping already present method %s", self.__class__.__name__, methodName)
					continue

				methodBackends = []
				methodBackendName = methodName.split("_", 1)[0]
				if methodBackendName in self._backends:
					logger.debug("Method name %s starts with %s, dispatching to backend: %s", methodName, methodBackendName, methodBackendName)
					methodBackends.append(methodBackendName)
				else:
					for regex, backends in self._dispatchConfig:
						if not re.search(regex, methodName):
							continue

						for backend in forceList(backends):
							if backend not in self._backends:
								logger.debug("Ignoring backend %s: backend not available", backend)
								continue
							if not hasattr(self._backends[backend]["instance"], methodName):
								logger.info("Ignoring backend %s: method %s not found", backend, methodName)
								continue
							methodBackends.append(backend)

						if methodBackends:
							logger.debug("%s matches method %s, dispatching to backends: %s", regex, methodName, ', '.join(methodBackends))
						break

				if not methodBackends:
					continue

				argString, callString = getArgAndCallString(functionRef)

				exec(f'def {methodName}(self, {argString}): return self._dispatchMethod({methodBackends}, "{methodName}", {callString})')  # pylint: disable=exec-used
				setattr(self, methodName, types.MethodType(eval(methodName), self))  # pylint: disable=eval-used

	def _dispatchMethod(self, methodBackends, methodName, **kwargs):
		logger.debug("Dispatching method %s to backends: %s", methodName, methodBackends)
		result = None

		for methodBackend in methodBackends:
			meth = getattr(self._backends[methodBackend]["instance"], methodName)
			res = meth(**kwargs)

			if isinstance(result, list) and isinstance(res, list):
				result.extend(res)
			elif isinstance(result, dict) and isinstance(res, dict):
				result.update(res)
			elif isinstance(result, set) and isinstance(res, set):
				result = result.union(res)
			elif isinstance(result, tuple) and isinstance(res, tuple):
				result = result + res
			elif res is not None:
				result = res

		logger.trace("Finished dispatching method %s", methodName)
		return result

	def backend_setOptions(self, options):
		Backend.backend_setOptions(self, options)
		for be in self._backends.values():
			be['instance'].backend_setOptions(options)

	def backend_getOptions(self):
		options = Backend.backend_getOptions(self)
		for be in self._backends.values():
			options.update(be['instance'].backend_getOptions())
		return options

	def backend_exit(self):
		for be in self._backends.values():
			be['instance'].backend_exit()

	def dispatcher_getConfig(self):
		return self._dispatchConfig

	def dispatcher_getBackendNames(self):
		return list(self._backends.keys())


@lru_cache(maxsize=None)
def _loadDispatchConfig(dispatchConfigFile):
	if not os.path.exists(dispatchConfigFile):
		raise BackendConfigurationError("Dispatch config file '%s' not found" % dispatchConfigFile)

	return BackendDispatchConfigFile(dispatchConfigFile).parse()
