"""Tests for rss slicer metadata types."""
from datetime import datetime
import lxml.etree as ET
from rss_slicer.rss import (Category,
                            Image,
                            Cloud,
                            TextInput,
                            SkipHours,
                            SkipDays,
                            Channel)
from rss_slicer.rss.xml import (CategoryXML,
                                ImageXML,
                                CloudXML,
                                TextInputXML,
                                SkipHoursXML,
                                SkipDaysXML,
                                ChannelXML)


def test_category_roundtrip():
    cat = Category('text', 'some.domain')
    assert cat == CategoryXML.parse(CategoryXML.render(cat))


def test_category_parse():
    assert (Category('text', domain='here it is')
            == CategoryXML.parse(
                ET.XML('<category domain="here it is">text</category>')
            ))
    assert (Category('something')
            == CategoryXML.parse(
                ET.XML('<category>   something   \t</category>'))
            )


def test_category_render():
    assert (
        ET.tostring(
            CategoryXML.render(
                Category('e', domain='hereitis')
            )
        )
        == b'<category domain="hereitis">e</category>')


def test_feedimage_roundtrip():
    image_req = Image('image', 'title', 'link')
    assert image_req == ImageXML.parse(ImageXML.render(image_req))

    image_opt = Image('im', 'ti', 'li', 1, 2, 'desc')
    assert image_opt == ImageXML.parse(ImageXML.render(image_opt))


def test_feedcloud_roundtrip():
    cloud = Cloud("domain", 80, "/", "doStuff", "xml-rpc")
    assert cloud == CloudXML.parse(CloudXML.render(cloud))


def test_textinput_roundtrip():
    text_input = TextInput("title", "desc", "name", "link")
    assert (text_input
            == TextInputXML.parse(TextInputXML.render(text_input)))


def test_skiphours_roundtrip():
    skip_hours = SkipHours([1, 2, 3])
    assert (skip_hours
            == SkipHoursXML.parse(SkipHoursXML.render(skip_hours)))


def test_skipdays_roundtrip():
    skip_days = SkipDays(["Monday", "Friday", "Sunday"])
    assert (skip_days
            == SkipDaysXML.parse(SkipDaysXML.render(skip_days)))


def test_metadata_roundtrip():
    meta_req = Channel('title', 'link', 'desc')
    assert (meta_req
            == ChannelXML.parse(ChannelXML.render(meta_req)))

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
        text_input=TextInput('eh', 'desc', 'name', 'link'),
        skip_hours=SkipHours(list(range(0, 23))),
        skip_days=SkipDays(['Today', 'Tomorrow'])
    )
    assert (meta_opt
            == ChannelXML.parse(ChannelXML.render(meta_opt)))
