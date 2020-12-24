#!/usr/bin/env python

"""Tests for `ldsnotes` package."""

import os
from ldsnotes import Notes


def test_login():
    Notes(os.environ['USERNAME'], os.environ['PASSWORD'])
