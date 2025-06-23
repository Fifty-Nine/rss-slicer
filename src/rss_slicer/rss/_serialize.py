"""Types and methods to reduce serialization boilerplate."""
from dataclasses import (Field, MISSING, fields, is_dataclass)
from datetime import datetime
from email.utils import format_datetime, parsedate_to_datetime
from enum import Enum
from functools import singledispatch
import types
import typing
from typing import (Annotated,
                    Any,
                    Callable,
                    Generic,
                    Optional,
                    Type,
                    TypeVar)
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
    NESTED_OBJECT = 0
    TEXT_ELEMENT = 1
    EMBEDDED_TEXT_ELEMENT = 2
    ATTRIBUTE = 3
    ELEMENT_LIST = 4


def _get_conversion_for_type(t: Type):
    if typing.get_origin(t) in (Annotated, list):
        return _get_conversion_for_type(typing.get_args(t)[0])

    if typing.get_origin(t) in (typing.Union, types.UnionType):
        args = typing.get_args(t)
        if type(None) not in args:
            raise NotImplementedError('union types not supported')

        return _get_conversion_for_type(next(a for a in args if a is not None))

    if is_dataclass(t):
        return XMLSerialization[t].parse

    if t is datetime:
        return parsedate_to_datetime

    return t


def _has_default(field: Field):
    return field.default != MISSING or field.default_factory != MISSING


def _get_default(field: Field):
    if not _has_default(field):
        raise TypeError('Field has no default.')
    return (field.default if field.default != MISSING
            else field.default_factory())


def _is_defaulted(field: Field, value: Any):
    return ((field.default != MISSING and value == field.default)
            or (field.default_factory != MISSING
                and value == field.default_factory()))


def _is_optional(t: Type):
    return (typing.get_origin(t) in (typing.Union, types.UnionType)
            and type(None) in typing.get_args(t))


def _get_renderer(t: Type):
    if is_dataclass(t):
        return XMLSerialization[t]

    if _is_optional(t):
        return _get_renderer(next(nt for nt in typing.get_args(t)
                                  if nt is not type(None)))

    raise NotImplementedError(
        "No available renderer for type {t}"
    )  # pragma: no cover


def _is_nested_object(t: Type):
    return (is_dataclass(t) or
            _is_optional(t) and any(_is_nested_object(nt)
                                    for nt in typing.get_args(t)))


def _get_list_elem_type(t: Type):
    if typing.get_origin(t) is list:
        return typing.get_args(t)[0]

    if _is_optional(t):
        return _get_list_elem_type(
            next(nt for nt in typing.get_args(t) if nt is not type(None))
        )

    return None


def _is_list(t: Type):
    return _get_list_elem_type(t) is not None


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

    if _is_nested_object(t):
        return _FieldKind.NESTED_OBJECT

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
NestedObject = _MakeAnnotated[_FieldKind.NESTED_OBJECT]


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
        if elem_kind == _FieldKind.NESTED_OBJECT:
            _render_renderable(e, value)
        else:
            assert elem_kind == _FieldKind.TEXT_ELEMENT
            child = SubElement(e, elem_name)
            child.text = _render_primitive(value)


def _get_element_text(e: Element):
    text = e.text.strip() if e.text is not None else None
    return text if text is not None and len(text) > 0 else None


class _MissingFieldException(Exception):
    def __init__(self, field: Field):
        self.field_name = field.name


def _check_default(field: Field,
                   text: Optional[str],
                   conv: Callable[[str], Any]):
    if text is None and not _has_default(field):
        raise _MissingFieldException(field)

    if text is None:
        return _get_default(field)

    return conv(text)


def _parse_field(field: Field, e: Element):
    # pylint: disable=too-many-return-statements
    conv = _get_conversion_for_type(field.type)
    match _get_field_kind(field.type):
        case _FieldKind.EMBEDDED_TEXT_ELEMENT:
            return _check_default(field, _get_element_text(e), conv)

        case _FieldKind.ATTRIBUTE:
            return _check_default(field,
                                  e.attrib.get(to_camel(field.name)),
                                  conv)

        case _FieldKind.TEXT_ELEMENT:
            child = e.find(f'./{to_camel(field.name)}')

            text = _get_element_text(child) if child is not None else None

            return _check_default(field, text, conv)

        case _FieldKind.ELEMENT_LIST:
            children = e.findall(f'./{_singularize(to_camel(field.name))}')
            if len(children) == 0 and not _has_default(field):
                raise _MissingFieldException(field)

            if len(children) == 0:
                return _get_default(field)

            return [conv(_get_element_text(c))
                    for c in children]

        case _FieldKind.NESTED_OBJECT:
            e = e.find(f'./{to_camel(field.name)}')
            if e is None and not _has_default(field):
                raise _MissingFieldException(field)

            if e is None:
                return _get_default(field)

            return _get_renderer(field.type).parse(e)

        case _:  # pragma: no cover
            raise RuntimeError('unexpected field kind')


def _parse_rss_element(rss_type, e: Element):
    init_dict = {}

    for field in fields(rss_type):
        try:
            init_dict[field.name] = _parse_field(field, e)
        except _MissingFieldException:
            continue

    return rss_type(**init_dict)


# pylint: disable=invalid-name
XMLSerType = TypeVar('XMLSerType')


class XMLSerialization(Generic[XMLSerType]):
    """Serialization helper for RSS elements.
    E.g.:
    ```
    RSSElement[MyRSSType].render(my_rss_element)
    ```

    `MyRSSType` must be a `dataclass`.
    """
    # These static methods are required just to make type hinting
    # resolve the result types of these methods.
    @staticmethod
    def parse(elem: Element) -> XMLSerType:  # pragma: no cover
        """Stub for parsing."""
        raise NotImplementedError()

    @staticmethod
    def render(elem: XMLSerType) -> Element:  # pragma: no cover
        """Stub for rendering."""
        raise NotImplementedError()

    @staticmethod
    def tag_name() -> str:  # pragma: no cover
        """Stub for getting the name of an element."""
        raise NotImplementedError()

    @classmethod
    def __class_getitem__(cls,
                          item: XMLSerType) -> 'XMLSerialization[XMLSerType]':
        class _RSSType:
            @staticmethod
            def render(elem: XMLSerType) -> Element:
                """Render the given element according to the RSS spec."""
                if hasattr(elem, 'render'):
                    return elem.render()

                return _render_rss_element(elem, item)

            @staticmethod
            def parse(elem: Element) -> XMLSerType:
                """Parse the given XML element into the RSS type."""
                if hasattr(item, 'parse'):
                    return item.parse(elem)

                return _parse_rss_element(item, elem)

            @staticmethod
            def tag_name() -> str:
                """Get the tag name used to serialize this element."""
                if hasattr(item, 'tag_name'):
                    return item.tag_name()
                return item.__name__[:1].lower() + item.__name__[1:]

        return _RSSType


def _render_rss_element(elem, t: Type) -> Element:
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

            case _FieldKind.NESTED_OBJECT:
                _render_renderable(e, value)

            case _FieldKind.ATTRIBUTE:
                _render_attribute(e, field, value)

            case _FieldKind.ELEMENT_LIST:
                _render_element_list(e, field, value)

            case _:  # pragma: no cover
                raise RuntimeError("unexpected _FieldKind value")

    return e
