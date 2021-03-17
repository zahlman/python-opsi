# -*- coding: utf-8 -*-

# This module is part of the desktop management solution opsi
# (open pc server integration) http://www.opsi.org
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
Backends.

:license: GNU Affero General Public License version 3
"""

import functools

def no_export(func):
	func.no_export = True
	return func

def deprecated(func=None, *, alternative_method=None):
	if func is None:
		return functools.partial(deprecated, alternative_method=alternative_method)

	func.deprecated = True
	func.alternative_method = alternative_method
	return func

	# @functools.wraps(func)
	# def wrapper(*args, **kwargs):
	# 	logger.warning("Deprecated")
	# 	return func(*args, **kwargs)
	# return wrapper
