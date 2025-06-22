"""Defines types used for RSS serialization and manipulation."""
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional
from lxml.etree import Element

from rss_slicer.rss._serialize import (Attribute,
                                       EmbeddedText,
                                       _get,
                                       _get_opt,
                                       _parse_list,
                                       _parse_opt)


@dataclass
class Category:
    """Stores a feed category as defined by the RSS specification."""
    text: EmbeddedText[str]
    domain: Attribute[Optional[str]] = None

    @staticmethod
    def parse(e: Element) -> 'Category':
        """Parse the given 'category' element from an RSS document."""
        return Category(
            e.text or '',
            e.attrib.get('domain')
        )


@dataclass
class Image:
    """Stores a feed image as defined by the RSS specification."""
    url: str
    title: str
    link: str
    width: Optional[int] = None
    height: Optional[int] = None
    description: Optional[str] = None

    @staticmethod
    def parse(e: Element) -> 'Image':
        """Parse the given 'image' element from an RSS document."""
        return Image(
            _get(e, 'url'),
            _get(e, 'title'),
            _get(e, 'link'),
            _get_opt(e, 'width', int),
            _get_opt(e, 'height', int),
            _get_opt(e, 'description')
        )


@dataclass
class Cloud:
    """
    Stores a cloud field as defined by the RSS specification.
    """
    domain: Attribute[str]
    port: Attribute[int]
    path: Attribute[str]
    register_procedure: Attribute[str]
    protocol: Attribute[str]

    @staticmethod
    def parse(e: Element) -> 'Cloud':
        """Parse the given 'cloud' element from an RSS document."""
        return Cloud(
            e.attrib['domain'],
            int(e.attrib['port']),
            e.attrib['path'],
            e.attrib['registerProcedure'],
            e.attrib['protocol']
        )


@dataclass
class TextInput:
    """
    Stores a textInput field as defined by the RSS specification.
    """
    title: str
    description: str
    name: str
    link: str

    @staticmethod
    def parse(e: Element) -> 'TextInput':
        """Parse the given 'textInput' element from an RSS document."""
        return TextInput(
            _get(e, 'title'),
            _get(e, 'description'),
            _get(e, 'name'),
            _get(e, 'link')
        )


@dataclass
class SkipHours:
    """
    Stores the contents of a skipHours element as defined by
    the RSS specification.
    """
    hours: list[int]

    @staticmethod
    def parse(e: Element) -> 'SkipHours':
        """Parse the given 'skipHours' element from an RSS document."""
        return SkipHours(
            _parse_list(e, 'hour', lambda h: int(h.text))
        )


@dataclass
class SkipDays:
    """
    Stores the contents of a skipDays element as defined by
    the RSS specification.
    """
    days: list[str]

    @staticmethod
    def parse(e: Element) -> 'SkipDays':
        """Parse the given 'skipDays' element from an RSS document."""
        return SkipDays(
            _parse_list(e, 'day', lambda d: d.text)
        )


@dataclass
class Channel:
    """
    Stores required and optional metadata about an RSS feed as defined
    by the RSS specification.
    """
    title: str
    link: str
    description: str
    language: Optional[str] = None
    copyright: Optional[str] = None
    managing_editor: Optional[str] = None
    web_master: Optional[str] = None
    pub_date: Optional[datetime] = None
    last_build_date: Optional[datetime] = None
    categories: Optional[list[Category]] = None
    generator: Optional[str] = None
    docs: Optional[str] = None
    cloud: Optional[Cloud] = None
    ttl: Optional[int] = None
    image: Optional[Image] = None
    rating: Optional[str] = None
    text_input: Optional[TextInput] = None
    skip_hours: Optional[SkipHours] = None
    skip_days: Optional[SkipDays] = None

    @staticmethod
    def parse(e: Element) -> 'Channel':
        """
        Parse all RSS-specified metadata
        from the given 'channel' element.
        """
        return Channel(
            _get(e, 'title'),
            _get(e, 'link'),
            _get(e, 'description'),
            _get_opt(e, 'language'),
            _get_opt(e, 'copyright'),
            _get_opt(e, 'managingEditor'),
            _get_opt(e, 'webMaster'),
            _get_opt(e, 'pubDate', parsedate_to_datetime),
            _get_opt(e, 'lastBuildDate', parsedate_to_datetime),
            _parse_list(e, 'category', Category.parse),
            _get_opt(e, 'generator'),
            _get_opt(e, 'docs'),
            _parse_opt(e, 'cloud', Cloud.parse),
            _get_opt(e, 'ttl', int),
            _parse_opt(e, 'image', Image.parse),
            _get_opt(e, 'rating'),
            _parse_opt(e, 'textInput', TextInput.parse),
            _parse_opt(e, 'skipHours', SkipHours.parse),
            _parse_opt(e, 'skipDays', SkipDays.parse)
        )
