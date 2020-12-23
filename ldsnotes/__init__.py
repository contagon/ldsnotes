"""Top-level package for LDS Notes."""
# flake8: noqa

__author__ = """Easton Potokar"""
__email__ = 'contagon6@gmail.com'
__version__ = '0.1.2'

from ldsnotes.content import Content
from ldsnotes.annotations import Bookmark, Journal, Highlight, Reference, Annotation
from ldsnotes.note import Notes, Tag, Folder
