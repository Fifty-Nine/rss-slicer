"""Tests for slicing functionality."""
from copy import deepcopy
import xml.etree.ElementTree as ET
import pytest
from rss_slicer import (SliceDefinition, slice_feeds, preserve_meta)
from rss_slicer.rss import Channel


@pytest.fixture(name='trivial_xml')
def fixture_trivial_xml():
    """Test fixure providing the root node of the WC3 RSS 2.0 sample."""
    result = ET.parse('./tests/samples/trivial.xml')
    ET.indent(result)
    return result


@pytest.fixture(name='trivial_channel')
def fixture_trivial_channel():
    """Test fixture providing a trivial Channel instance."""
    return Channel(title='new title',
                   link='rss-slicer.trprince.com',
                   description='I made this up')


def test_empty_slicer(trivial_xml: ET.ElementTree, trivial_channel: Channel):
    orig = deepcopy(trivial_xml)

    result = slice_feeds(
        [trivial_xml],
        SliceDefinition(trivial_channel, [])
    )

    # FIXME We should convert these to Item instances and diff those.
    old_items = [ET.tostring(n) for n in orig.findall('./channel/item')]
    new_items = [ET.tostring(n) for n in result.findall('./channel/item')]

    assert old_items == new_items


def test_strip_item_content(trivial_xml: ET.ElementTree,
                            trivial_channel: Channel):
    orig = deepcopy(trivial_xml)
    result = slice_feeds(
        [trivial_xml],
        SliceDefinition(
            trivial_channel,
            slicers=[('./channel/item/guid', lambda _: True)]
        )
    )

    old_items = orig.findall('./channel/item/*')
    new_items = result.findall('./channel/item/*')

    assert ([ET.tostring(n).strip() for n in old_items if n.tag != 'guid']
            == [ET.tostring(n).strip() for n in new_items])


def test_remove_item(trivial_xml: ET.ElementTree, trivial_channel: Channel):
    orig = deepcopy(trivial_xml)

    def starts_with_nasa(e: ET.Element) -> bool:
        title = e.find('./title')
        if title is None or title.text is None:
            return False

        return title.text.startswith('NASA')

    result = slice_feeds(
        [trivial_xml],
        SliceDefinition(
            trivial_channel,
            slicers=[('./channel/item', lambda e: not starts_with_nasa(e))]
        )
    )

    old_items = orig.findall('./channel/item')
    new_items = result.findall('./channel/item')

    # One item's title starts with "Louisiana," another lacks a title entirely.
    assert len(new_items) == (len(old_items) - 2)
    assert all(starts_with_nasa(n) for n in new_items)


def test_preserve_meta(trivial_xml: ET.ElementTree, trivial_channel: Channel):
    orig = deepcopy(trivial_xml)

    result = slice_feeds(
        [trivial_xml],
        SliceDefinition(
            trivial_channel,
            slicers=[],
            keep_unrecognized=True,
            meta_strategy=preserve_meta)
    )

    orig_channel = orig.find('./channel')
    result_channel = result.find('./channel')
    assert orig_channel is not None and result_channel is not None
    assert Channel.parse(orig_channel) == Channel.parse(result_channel)


def test_bad_rss_no_channel(trivial_channel):
    doc = ET.ElementTree(
        ET.Element('rss', attrib={'version': '2.0'})
    )

    with pytest.raises(ValueError):
        _ = slice_feeds(
            [doc],
            SliceDefinition(
                trivial_channel,
                slicers=[]
            )
        )
