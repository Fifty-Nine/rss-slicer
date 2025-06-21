"""Types and methods to reduce serialization boilerplate."""
from dataclasses import (Field, MISSING, fields, is_dataclass)
from datetime import datetime
from email.utils import format_datetime
from enum import Enum
from functools import singledispatch
import types
import typing
from typing import (Annotated,
                    Any,
                    Callable,
                    Optional,
                    Type)
from camel_converter import to_camel
from lxml.etree import Element, SubElement


def _singularize(noun: str) -> str:
    """Quick and dirty plural -> singular conversion. Only expected
    to work for names that appear in the RSS spec.
    """
    if noun.endswith('ies'):
        return noun[:-3] + 'y'

    if noun.endswith('s'):
        return noun[:-1]

    return noun


def _get(e: Element, name: str, ctor: Callable[[str], Any] = str):
    text = e.find(f'./{name}').text
    return ctor(text if text is not None else '')


def _get_opt(e: Element, name: str, ctor: Callable[[str], Any] = str):
    result = e.find(f'./{name}')

    if result is not None:
        return ctor(result.text)

    return None


def _parse_opt(e: Element, name: str, parser: Callable[[Element], Any]):
    result = e.find(f'./{name}')

    if result is not None:
        return parser(result)

    return None


def _parse_list(e: Element, name: str, parser: Callable[[Element], Any]):
    result = e.findall(f'./{name}')

    if len(result) == 0:
        return None

    return [parser(r) for r in result]


class _FieldKind(Enum):
    RENDERABLE = 0
    TEXT_ELEMENT = 1
    EMBEDDED_TEXT_ELEMENT = 2
    ATTRIBUTE = 3
    ELEMENT_LIST = 4


def _is_optional(t: Type):
    return (typing.get_origin(type) not in (typing.Union, types.UnionType)
            and type(None) in typing.get_args(t))


def _is_renderable(t: Type):
    return (is_dataclass(t) or
            _is_optional(t) and any(_is_renderable(nt)
                                    for nt in typing.get_args(t)))


def _is_list(t: Type):
    return _get_list_elem_type(t) is not None


def _get_list_elem_type(t: Type):
    if typing.get_origin(t) is list:
        return typing.get_args(t)[0]

    if _is_optional(t):
        return _get_list_elem_type(
            next(nt for nt in typing.get_args(t) if nt is not type(None))
        )

    return None


def _get_annotated_kind(t: Type) -> Optional[_FieldKind]:
    if _is_optional(t):
        args = [nt for nt in typing.get_args(t) if nt is not type(None)]
        return _get_annotated_kind(args[0]) if len(args) == 1 else None

    if typing.get_origin(t) is Annotated:
        return typing.get_args(t)[1]

    return None


def _get_field_kind(t: Type) -> _FieldKind:
    annot = _get_annotated_kind(t)
    if annot is not None:
        return annot

    if _is_renderable(t):
        return _FieldKind.RENDERABLE

    if _is_list(t):
        return _FieldKind.ELEMENT_LIST

    return _FieldKind.TEXT_ELEMENT


class _MakeAnnotated:
    def __class_getitem__(cls, kind):
        class _Builder:
            def __class_getitem__(cls, base_type):
                return Annotated[base_type, kind]

        return _Builder


Attribute = _MakeAnnotated[_FieldKind.ATTRIBUTE]
TextElement = _MakeAnnotated[_FieldKind.TEXT_ELEMENT]
EmbeddedText = _MakeAnnotated[_FieldKind.EMBEDDED_TEXT_ELEMENT]
Renderable = _MakeAnnotated[_FieldKind.RENDERABLE]


@singledispatch
def _render_primitive(arg):
    raise NotImplementedError(f'Unable to render value with type {type(arg)}')


@_render_primitive.register
def _(arg: int):
    return str(arg)


@_render_primitive.register
def _(arg: str):
    return arg


@_render_primitive.register
def _(arg: datetime):
    return format_datetime(arg)


def _is_defaulted(field: Field, value: Any):
    return field.default != MISSING and value == field.default


def _render_renderable(e: Element, value: Any):
    e.append(XMLSerialization[type(value)].render(value))


def _render_embedded_text_element(e: Element, value: Any):
    e.text = _render_primitive(value)


def _render_attribute(e: Element, field: Field, value: Any):
    e.attrib[to_camel(field.name)] = _render_primitive(value)


def _render_text_element(e: Element, field: Field, value: Any):
    child = SubElement(e, to_camel(field.name))
    child.text = _render_primitive(value)


def _render_element_list(e: Element, field: Field, values: list[Any]):
    elem_name = _singularize(to_camel(field.name))
    elem_kind = _get_field_kind(_get_list_elem_type(field.type))

    if elem_kind in (_FieldKind.EMBEDDED_TEXT_ELEMENT, _FieldKind.ATTRIBUTE):
        raise TypeError(
            f'{elem_kind} elements cannot nest within a list element.'
        )

    if elem_kind == _FieldKind.ELEMENT_LIST:
        raise NotImplementedError('Nested lists are not implemented.')

    for value in values:
        if elem_kind == _FieldKind.RENDERABLE:
            _render_renderable(e, value)
        else:
            assert elem_kind == _FieldKind.TEXT_ELEMENT
            child = SubElement(e, elem_name)
            child.text = _render_primitive(value)


class XMLSerialization:
    """Serialization helper for RSS elements.
    E.g.:
    ```
    RSSElement[MyRSSType].render(my_rss_element)
    ```

    `MyRSSType` must be a `dataclass`.
    """
    def __class_getitem__(cls, rss_type):
        class _RSSType:
            @staticmethod
            def render(elem):
                """Render the given element according to the RSS spec."""
                if hasattr(elem, 'render'):
                    return elem.render()

                return _render_rss_element(elem, rss_type)

            @staticmethod
            def tag_name():
                """Get the tag name used to serialize this element."""
                if hasattr(rss_type, 'tag_name'):
                    return rss_type.tag_name()
                return rss_type.__name__[:1].lower() + rss_type.__name__[1:]

        return _RSSType


def _render_rss_element(elem, t: Type):
    name = XMLSerialization[t].tag_name()
    e = Element(name)
    has_text = False

    for field in fields(elem):
        value = getattr(elem, field.name)
        if _is_defaulted(field, value):
            continue

        match _get_field_kind(field.type):
            case _FieldKind.EMBEDDED_TEXT_ELEMENT:
                if has_text:
                    raise RuntimeError(
                        f'Multiple text elements encountered for {type(elem)}'
                    )
                has_text = True
                _render_embedded_text_element(e, value)

            case _FieldKind.TEXT_ELEMENT:
                _render_text_element(e, field, value)

            case _FieldKind.RENDERABLE:
                _render_renderable(e, value)

            case _FieldKind.ATTRIBUTE:
                _render_attribute(e, field, value)

            case _FieldKind.ELEMENT_LIST:
                _render_element_list(e, field, value)

            case _:  # pragma: no cover
                raise RuntimeError("unexpected _FieldKind value")

    return e
