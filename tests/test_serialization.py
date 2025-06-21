"""Tests for serialization helpers."""
from dataclasses import dataclass
from datetime import datetime
from typing import (Optional)
from lxml import etree
from pytest import raises
from rss_slicer._serialize import (_FieldKind,
                                   Attribute,
                                   EmbeddedText,
                                   Renderable,
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
    class _Renderable:
        pass

    assert _get_field_kind(_Renderable) == _FieldKind.RENDERABLE
    assert _get_field_kind(Optional[_Renderable]) == _FieldKind.RENDERABLE
    assert _get_field_kind(Renderable[_Renderable]) == _FieldKind.RENDERABLE
    assert (_get_field_kind(Renderable[Optional[_Renderable]])
            == _FieldKind.RENDERABLE)

    assert _get_field_kind(list[int]) == _FieldKind.ELEMENT_LIST
    assert _get_field_kind(list[_Renderable]) == _FieldKind.ELEMENT_LIST
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
