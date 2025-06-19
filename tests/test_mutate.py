"""Tests for RSS slicing functionality."""
from lxml import etree
from lxml.etree import Element
from rss_slicer import Mutation, apply_one_mutation


def test_trivial():
    """Trivial smoke test for basic rss_slicer functionality."""
    root = etree.fromstring(b'<data><a/><b/><c/></data>')

    def fn(e: Element) -> bool:
        if e.tag == 'c':
            return True

        e.tag = 'd'
        return False

    mutator = Mutation('./', fn)

    apply_one_mutation(root, mutator)
    assert b'<data><d/><d/></data>' == etree.tostring(root)
