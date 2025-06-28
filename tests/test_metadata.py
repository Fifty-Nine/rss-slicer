"""Tests for rss slicer metadata types."""
from datetime import datetime
import xml.etree.ElementTree as ET
from pytest import raises
from rss_slicer.rss import (Category,
                            Image,
                            Cloud,
                            TextInput,
                            SkipHours,
                            SkipDays,
                            Channel,
                            _read_int)


def test_category_roundtrip():
    cat = Category('text', 'some.domain')
    assert cat == Category.parse(cat.render())


def test_category_parse():
    assert (Category('text', domain='here it is')
            == Category.parse(
                ET.fromstring('<category domain="here it is">text</category>')
            ))
    assert Category('') == Category.parse(ET.fromstring('<category/>'))


def test_category_render():
    assert (ET.tostring(Category('e', domain='hereitis').render())
            == b'<category domain="hereitis">e</category>')


def test_feedimage_roundtrip():
    image_req = Image('image', 'title', 'link')
    assert image_req == Image.parse(image_req.render())

    image_opt = Image('im', 'ti', 'li', 1, 2, 'desc')
    assert image_opt == Image.parse(image_opt.render())


def test_feedcloud_roundtrip():
    cloud = Cloud("domain", 80, "/", "doStuff", "xml-rpc")
    assert cloud == Cloud.parse(cloud.render())


def test_textinput_roundtrip():
    text_input = TextInput("title", "desc", "name", "link")
    assert text_input == TextInput.parse(text_input.render())


def test_skiphours_roundtrip():
    skip_hours = SkipHours([1, 2, 3])
    assert skip_hours == SkipHours.parse(skip_hours.render())


def test_skipdays_roundtrip():
    skip_days = SkipDays(["Monday", "Friday", "Sunday"])
    assert skip_days == SkipDays.parse(skip_days.render())


def test_metadata_roundtrip():
    meta_req = Channel('title', 'link', 'desc')
    assert meta_req == Channel.parse(meta_req.render())

    meta_opt = Channel(
        title='title',
        link='http://something!',
        description='desc',
        language='en-us',
        copyright='EvilCorp Inc.',
        managing_editor='nobody',
        web_master="can't afford em",
        pub_date=datetime.now().replace(microsecond=0),
        last_build_date=datetime(1970, 1, 1),
        categories=[Category('funny stuff'),
                    Category('dumb stuff', domain='dumshit.io')],
        generator='rss-slicer',
        docs='https://www.rssboard.org/rss-specification',
        cloud=Cloud('nowhere.local',
                    99,
                    '/somewhere',
                    'justDoIt',
                    'magic-proto'),
        ttl=10,
        image=Image('http://img/image.jpg', 'image', 'somewhere'),
        rating='bad',
        text_input=TextInput('eh', 'desc', 'name', ''),
        skip_hours=SkipHours(list(range(0, 23))),
        skip_days=SkipDays(['Today', 'Tomorrow'])
    )
    assert meta_opt == Channel.parse(meta_opt.render())


def test_parse_int():
    with raises(ValueError):
        _read_int(ET.fromstring('<a/>'))
