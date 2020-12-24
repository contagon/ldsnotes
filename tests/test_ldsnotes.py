#!/usr/bin/env python

"""""""""Tests for `ldsnotes` package."""""""""

import pytest
import os
from ldsnotes import Notes, Bookmark, Journal, Highlight, Reference


@pytest.fixture(scope="session")
def notes():
    return Notes(os.environ['USERNAME'], os.environ['PASSWORD'])


def test_login(notes):
    pass


""""""""" TEST CONSTRUCTOR FOR ALL TYPE OF ANNOTATIONS """""""""


def test_bookmark(notes):
    n = notes.search(annot_type="bookmark", start=1, stop=3)
    assert len(n) == 2
    assert isinstance(n[0], Bookmark)


def test_journal(notes):
    n = notes.search(annot_type="journal", start=1, stop=3)
    assert len(n) == 2
    assert isinstance(n[0], Journal)


def test_highlight(notes):
    n = notes.search(annot_type="highlight", start=1, stop=3)
    assert len(n) == 2
    assert isinstance(n[0], Highlight)


def test_reference(notes):
    n = notes.search(annot_type="reference", start=1, stop=3)
    assert len(n) == 2
    assert isinstance(n[0], Reference)


"""""""""           TEST SEARCH FUNCTION           """""""""


def test_tag(notes):
    n = notes.search(tag="Faith", start=1, stop=3)
    for i in n:
        assert "Faith" in i.tags


def test_folder(notes):
    n = notes.search(folder="Journal", start=1, stop=3)
    j_id = [i.id for i in notes.folders if i.name == "Journal"][0]
    for i in n:
        assert j_id in i.folders_id


"""""""""           TEST INDEXING          """""""""


def test_index(notes):
    assert not isinstance(notes[1], list)
    assert len(notes[:10]) == 10
    assert len(notes[1:11]) == 10
