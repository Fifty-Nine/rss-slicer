"""Tests for rss slicer metadata types."""
from datetime import datetime
import lxml.etree as ET
from rss_slicer import (FeedCategory,
                        FeedImage,
                        FeedCloud,
                        FeedTextInput,
                        FeedSkipHours,
                        FeedSkipDays,
                        FeedMetadata)


def test_category_roundtrip():
    cat = FeedCategory('text', 'some.domain')
    assert cat == FeedCategory.parse(cat.render())


def test_category_parse():
    assert (FeedCategory('text', domain='here it is')
            == FeedCategory.parse(
                ET.XML('<category domain="here it is">text</category>')
            ))
    assert FeedCategory('') == FeedCategory.parse(ET.XML('<category/>'))


def test_category_render():
    assert (ET.tostring(FeedCategory('e', domain='hereitis').render())
            == b'<category domain="hereitis">e</category>')


def test_feedimage_roundtrip():
    image_req = FeedImage('image', 'title', 'link')
    assert image_req == FeedImage.parse(image_req.render())

    image_opt = FeedImage('im', 'ti', 'li', 1, 2, 'desc')
    assert image_opt == FeedImage.parse(image_opt.render())


def test_feedcloud_roundtrip():
    cloud = FeedCloud("domain", 80, "/", "doStuff", "xml-rpc")
    assert cloud == FeedCloud.parse(cloud.render())


def test_textinput_roundtrip():
    text_input = FeedTextInput("title", "desc", "name", "link")
    assert text_input == FeedTextInput.parse(text_input.render())


def test_skiphours_roundtrip():
    skip_hours = FeedSkipHours([1, 2, 3])
    assert skip_hours == FeedSkipHours.parse(skip_hours.render())


def test_skipdays_roundtrip():
    skip_days = FeedSkipDays(["Monday", "Friday", "Sunday"])
    assert skip_days == FeedSkipDays.parse(skip_days.render())


def test_metadata_roundtrip():
    meta_req = FeedMetadata('title', 'link', 'desc')
    assert meta_req == FeedMetadata.parse(meta_req.render())

    meta_opt = FeedMetadata(
        title='title',
        link='http://something!',
        description='desc',
        language='en-us',
        copyright='EvilCorp Inc.',
        managing_editor='nobody',
        web_master="can't afford em",
        pub_date=datetime.now().replace(microsecond=0),
        last_build_date=datetime(1970, 1, 1),
        categories=[FeedCategory('funny stuff'),
                    FeedCategory('dumb stuff', domain='dumshit.io')],
        generator='rss-slicer',
        docs='https://www.rssboard.org/rss-specification',
        cloud=FeedCloud('nowhere.local',
                        99,
                        '/somewhere',
                        'justDoIt',
                        'magic-proto'),
        ttl=10,
        image=FeedImage('http://img/image.jpg', 'image', 'somewhere'),
        rating='bad',
        text_input=FeedTextInput('eh', 'desc', 'name', ''),
        skip_hours=FeedSkipHours(list(range(0, 23))),
        skip_days=FeedSkipDays(['Today', 'Tomorrow'])
    )
    assert meta_opt == FeedMetadata.parse(meta_opt.render())
