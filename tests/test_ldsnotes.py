#!/usr/bin/env python

"""Tests for `ldsnotes` package."""

import pytest
import os
from ldsnotes import Notes

def test_login():
    n = Notes(os.environ['USERNAME'], os.environ['PASSWORD'])