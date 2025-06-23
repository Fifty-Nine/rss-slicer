"""Tests for serialization helpers."""
from dataclasses import dataclass
from datetime import datetime
from typing import (Optional)
from zoneinfo import ZoneInfo
from lxml import etree
from pytest import raises, mark
from rss_slicer.rss._serialize import (_FieldKind,
                                       Attribute,
                                       EmbeddedText,
                                       NestedObject,
                                       TextElement,
                                       XMLSerialization,
                                       _get_field_kind,
                                       _is_defaulted,
                                       _render_primitive,
                                       _render_rss_element,
                                       _singularize,
                                       fields)


def test_primitives():
    assert _render_primitive(0) == "0"
    assert _render_primitive("str") == "str"
    assert (_render_primitive(datetime(1999, 3, 15, 12, 0, 0))
            == "Mon, 15 Mar 1999 12:00:00 -0000")

    with raises(NotImplementedError):
        _render_primitive(None)

    with raises(NotImplementedError):
        class TestRandoType:
            pass
        _render_primitive(TestRandoType)


def test_singularize():
    assert _singularize("ducks") == "duck"
    assert _singularize("vagaries") == "vagary"
    assert _singularize("honk") == "honk"


def test_is_defaulted():
    @dataclass
    class Test:
        a: int
        b: Optional[str]
        c: int = 0
        d: Optional[int] = None

    t = Test(0, 1, 2, 3)

    assert ([_is_defaulted(f, getattr(t, f.name)) for f in fields(t)]
            == [False, False, False, False])

    t = Test(-1, -2)
    assert ([_is_defaulted(f, getattr(t, f.name)) for f in fields(t)]
            == [False, False, True, True])

    t = Test(-1, -2, 0, None)
    assert ([_is_defaulted(f, getattr(t, f.name)) for f in fields(t)]
            == [False, False, True, True])


def test_get_field_kind():
    assert _get_field_kind(Attribute[str]) == _FieldKind.ATTRIBUTE
    assert _get_field_kind(Attribute[int]) == _FieldKind.ATTRIBUTE
    assert (_get_field_kind(Attribute[Optional[datetime]])
            == _FieldKind.ATTRIBUTE)
    assert (_get_field_kind(Optional[Attribute[datetime]])
            == _FieldKind.ATTRIBUTE)

    assert (_get_field_kind(EmbeddedText[str])
            == _FieldKind.EMBEDDED_TEXT_ELEMENT)

    assert _get_field_kind(str) == _FieldKind.TEXT_ELEMENT
    assert _get_field_kind(int) == _FieldKind.TEXT_ELEMENT
    assert _get_field_kind(Optional[int]) == _FieldKind.TEXT_ELEMENT
    assert _get_field_kind(TextElement[int]) == _FieldKind.TEXT_ELEMENT
    assert (_get_field_kind(Optional[TextElement[int]])
            == _FieldKind.TEXT_ELEMENT)

    @dataclass
    class _NestedObj:
        pass

    assert _get_field_kind(_NestedObj) == _FieldKind.NESTED_OBJECT
    assert _get_field_kind(Optional[_NestedObj]) == _FieldKind.NESTED_OBJECT
    assert (_get_field_kind(NestedObject[_NestedObj])
            == _FieldKind.NESTED_OBJECT)
    assert (_get_field_kind(NestedObject[Optional[_NestedObj]])
            == _FieldKind.NESTED_OBJECT)

    assert _get_field_kind(list[int]) == _FieldKind.ELEMENT_LIST
    assert _get_field_kind(list[_NestedObj]) == _FieldKind.ELEMENT_LIST
    assert _get_field_kind(list[TextElement[str]]) == _FieldKind.ELEMENT_LIST
    assert _get_field_kind(Optional[list[int]]) == _FieldKind.ELEMENT_LIST
    assert _get_field_kind(list[Optional[int]]) == _FieldKind.ELEMENT_LIST


def test_render_multiple_text():
    @dataclass
    class TestBadMultipleText:
        a: EmbeddedText[int]
        b: EmbeddedText[str]

    with raises(RuntimeError):
        _render_rss_element(TestBadMultipleText(0, "a"), TestBadMultipleText)


def test_render_embedded_text_in_list():
    @dataclass
    class TestEmbeddedTextInList:
        a: list[EmbeddedText[int]]

    with raises(TypeError):
        _render_rss_element(TestEmbeddedTextInList([]), TestEmbeddedTextInList)


def test_render_attribute_in_list():
    @dataclass
    class TestAttributeInList:
        a: list[Attribute[int]]

    with raises(TypeError):
        _render_rss_element(TestAttributeInList([]), TestAttributeInList)


def test_render_nested_list():
    @dataclass
    class TestNestedList:
        a: list[list[int]]

    with raises(NotImplementedError):
        _render_rss_element(TestNestedList([[]]), TestNestedList)


def test_anonymous():
    @dataclass
    class TestAnon:
        pass

    assert XMLSerialization[TestAnon].tag_name() == 'testAnon'


def test_named():
    @dataclass
    class TestNamed:
        # pylint: disable=missing-function-docstring
        @staticmethod
        def tag_name():
            return 'unconventional name'

    assert XMLSerialization[TestNamed].tag_name() == 'unconventional name'


def test_no_render():
    @dataclass
    class TestNoRender:
        pass

    assert (
        etree.tostring(XMLSerialization[TestNoRender].render(TestNoRender()))
        == b'<testNoRender/>'
    )


def test_custom_render():
    @dataclass
    class TestCustomRender:
        # pylint: disable=missing-function-docstring
        def render(self):
            return 'surprisingly, not an xml element'

    assert (XMLSerialization[TestCustomRender].render(TestCustomRender())
            == 'surprisingly, not an xml element')


def test_parse_optional_fields_parse():
    @dataclass
    class TestOptFields:
        a: Optional[EmbeddedText[str]] = None
        b: Optional[TextElement[str]] = None

    obj = XMLSerialization[TestOptFields].parse(
        etree.XML("<testFieldOpt><b/></testFieldOpt>")
    )

    assert obj.a is None
    assert obj.b is None


def test_parse_renderable():
    @dataclass
    class TestTrivial:
        a: str

    @dataclass
    class TestRenderable:
        some_field: TestTrivial
        opt: Optional[TestTrivial] = None

    obj = XMLSerialization[TestRenderable].parse(
        etree.XML(
            '<testRenderable>'
            '  <someField><a>foo</a></someField>'
            '</testRenderable>'
        )
    )

    assert obj.some_field.a == "foo"
    assert obj.opt is None


def test_parse_empty_elem_list():
    @dataclass
    class TestEmptyList:
        a: Optional[list[int]] = None

    obj = XMLSerialization[TestEmptyList].parse(
        etree.XML("<testEmptyList/>")
    )

    assert obj.a is None


def test_parse_bad_union():
    @dataclass
    class TestUnionType:
        a: int | str

    with raises(NotImplementedError):
        XMLSerialization[TestUnionType].parse(
            etree.XML('<testUnionType><a>0</a></testUnionType>')
        )


def test_parse_datetime_field():
    @dataclass
    class TestDatetime:
        a: datetime

    obj = XMLSerialization[TestDatetime].parse(
        etree.XML(
            '<testDatetime><a>Sat, 07 Sep 2002 00:00:01 GMT</a></testDatetime>'
        )
    )

    assert obj.a == datetime(2002, 9, 7, 0, 0, 1, 0, ZoneInfo('Etc/GMT'))


def test_parse_opt_dataclass():
    @dataclass
    class TestSubObj:
        a: EmbeddedText[int]

    @dataclass
    class TestOptDataclass:
        m: Optional[TestSubObj]

    obj = XMLSerialization[TestOptDataclass].parse(
        etree.XML(
            '<testOptDataclass>'
            '  <m>33</m>'
            '</testOptDataclass>'
        )
    )

    assert obj.m.a == 33


class _TestNotADataclass:  # pylint: disable=missing-function-docstring
    def __init__(self, a: int):
        self.a = a

    @staticmethod
    def parse(_: etree.Element) -> '_TestNotADataclass':
        return _TestNotADataclass(1234)

    def render(self) -> etree.Element:
        return etree.XML('<someCustomXML/>')


def test_non_dataclass_obj():
    obj = XMLSerialization[_TestNotADataclass].parse(
        etree.XML('<arbitrary/>')
    )

    assert obj.a == 1234

    rendered = XMLSerialization[_TestNotADataclass].render(obj)

    assert etree.tostring(rendered) == b'<someCustomXML/>'


@mark.xfail(raises=NotImplementedError)
def test_nested_non_dataclass_obj():
    @dataclass
    class TestNested:
        a: NestedObject[_TestNotADataclass]

    _ = XMLSerialization[TestNested].parse(
        etree.XML('<testNested><a/></testNested>')
    )


def test_opt_field_no_default():
    @dataclass
    class TestOptFieldNoDefault:
        a: Optional[int]

    with raises(TypeError):
        _ = XMLSerialization[TestOptFieldNoDefault].parse(
            etree.XML('<testOptFieldNoDefault/>')
        )


def test_defaulted_non_opt_field():
    @dataclass
    class TestDefaultedNonOptField:
        a: int = 59

    obj = XMLSerialization[TestDefaultedNonOptField].parse(
        etree.XML('<testDefaultedNonOptField/>')
    )

    assert obj.a == 59


def test_defaulted_optional():
    @dataclass
    class TestDefaultedOptional:
        a: Optional[int] = 22

    obj = XMLSerialization[TestDefaultedOptional].parse(
        etree.XML('<testDefaultedOptional/>')
    )

    assert obj.a == 22
