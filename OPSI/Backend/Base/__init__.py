# -*- coding: utf-8 -*-

# Copyright (c) uib GmbH <info@uib.de>
# License: AGPL-3.0
"""
Backends.
"""

from __future__ import absolute_import

from .Backend import Backend, describeInterface
from .ConfigData import ConfigDataBackend
from .Extended import (
	ExtendedBackend,
	ExtendedConfigDataBackend,
	get_function_signature_and_args,
)
from .ModificationTracking import (
	BackendModificationListener,
	ModificationTrackingBackend,
)

__all__ = (
	"describeInterface",
	"get_function_signature_and_args",
	"Backend",
	"ExtendedBackend",
	"ConfigDataBackend",
	"ExtendedConfigDataBackend",
	"ModificationTrackingBackend",
	"BackendModificationListener",
)
