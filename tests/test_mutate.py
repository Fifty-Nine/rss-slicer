"""Tests for RSS slicing functionality."""
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from rss_slicer import apply_one_mutation, apply_mutations, Callback


class TestMutators:
    """Some basic mutators for use in unit tests."""

    @staticmethod
    def retag(new_tag: str) -> Callback:
        """Make a mutator that replaces all tags with `new_tag`."""
        def cb(e: Element) -> bool:
            e.tag = new_tag
            return False

        return cb

    @staticmethod
    def oneshot(mutator: Callback) -> Callback:
        """Make a mutator that runs only once."""
        flag = False

        def cb(e: Element) -> bool:
            nonlocal flag
            if not flag:
                mutator(e)
                flag = True

            return False

        return cb

    @staticmethod
    def delete() -> Callback:
        """Create a mutator that unconditionally deletes the element."""
        def cb(_: Element) -> bool:
            return True

        return cb

    @staticmethod
    def delete_matching(tag: str) -> Callback:
        """Create a mutator that deletes any element with a matching tag."""
        def cb(e: Element) -> bool:
            return e.tag == tag

        return cb


def test_trivial():
    """Trivial smoke test for basic rss_slicer functionality."""
    root = ET.fromstring(b'<data><a/><b/><c/></data>')

    apply_one_mutation(
        root, './',
        TestMutators.oneshot(TestMutators.retag('d'))
    )
    assert b'<data><d /><b /><c /></data>' == ET.tostring(root)

    apply_mutations(
        root,
        [
            ('./b', TestMutators.retag('e')),
            ('./', TestMutators.delete_matching('b')),
            ('./d', TestMutators.delete())
        ]
    )
    assert b'<data><e /><c /></data>' == ET.tostring(root)
