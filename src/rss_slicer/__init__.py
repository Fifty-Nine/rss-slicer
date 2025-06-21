"""
RSS slicer library
~~~~~~~~~~~~~~~~~~

`rss-slicer` is an RSS feed slicer-dicer for combining an arbitrary
set of input RSS feeds and transforming them into a new set of output
streams.

:copyright: (c) 2025 by Tim Prince
:license: GPL v3, see COPYING for details.
"""
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime, format_datetime
from typing import Annotated, Any, Callable, Optional
from lxml.etree import Element, SubElement

Callback = Annotated[
    Callable[[Element], bool],
    """\
Bundles together an XPath query and a function
that modifies an XML element. The function should
modify the passed-in Element in-place and return
`True` if the element (and its children) should be
deleted from the tree and `False` if it should be
preserved.
"""
]


def apply_one_mutation(tree: Element, query: str, mutator: Callback):
    """Given a mutation, apply it to the children of `tree` that
    satisfy the associated XPath query. The tree is modified in-place.

    :param tree: the root XML node to which tthe transformation should be
        applied.
    :param query: the XPath query to select elements which should be
        mutated.
    :param mutator: the mutation function to apply to the tree.
    :rtype: None
    """
    nodes = tree.findall(query)
    to_remove = []
    for node in nodes:
        if mutator(node):
            to_remove.append(node)

    for node in to_remove:
        node.find('..').remove(node)


def apply_mutations(tree: Element, mutations: list[tuple[str, Callback]]):
    """Given a list of mutations, apply them in sequence to
    the given tree.

    :param tree: the root XML node to which the transformations should be
        applied.
    :param mutations: the mutations to apply to the tree.
    :rtype: None
    """
    for mutation in mutations:
        apply_one_mutation(tree, *mutation)


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


@dataclass
class FeedCategory:
    """Stores a feed category as defined by the RSS specification."""
    text: str
    domain: Optional[str] = None

    def render(self) -> Element:
        """Render this item into an XML element."""
        result = Element("category")
        result.text = self.text
        if self.domain is not None:
            result.attrib['domain'] = self.domain

        return result

    @staticmethod
    def parse(e: Element) -> 'FeedCategory':
        """Parse the given 'category' element from an RSS document."""
        return FeedCategory(
            e.text or '',
            e.attrib.get('domain')
        )


@dataclass
class FeedImage:
    """Stores a feed image as defined by the RSS specification."""
    url: str
    title: str
    link: str
    width: Optional[int] = None
    height: Optional[int] = None
    description: Optional[str] = None

    def render(self) -> Element:
        """Render this image into an XML element."""
        result = Element('image')

        url = SubElement(result, 'url')
        url.text = self.url

        title = SubElement(result, 'title')
        title.text = self.title

        link = SubElement(result, 'link')
        link.text = self.link

        if self.width is not None:
            width = SubElement(result, 'width')
            width.text = str(self.width)

        if self.height is not None:
            height = SubElement(result, 'height')
            height.text = str(self.height)

        if self.description is not None:
            description = SubElement(result, 'description')
            description.text = self.description

        return result

    @staticmethod
    def parse(e: Element) -> 'FeedImage':
        """Parse the given 'image' element from an RSS document."""
        return FeedImage(
            _get(e, 'url'),
            _get(e, 'title'),
            _get(e, 'link'),
            _get_opt(e, 'width', int),
            _get_opt(e, 'height', int),
            _get_opt(e, 'description')
        )


@dataclass
class FeedCloud:
    """
    Stores a cloud field as defined by the RSS specification.
    """
    domain: str
    port: int
    path: str
    register_procedure: str
    protocol: str

    def render(self) -> Element:
        """Render this item into an XML element."""
        result = Element('cloud')
        result.attrib['domain'] = self.domain
        result.attrib['port'] = str(self.port)
        result.attrib['path'] = self.path
        result.attrib['registerProcedure'] = self.register_procedure
        result.attrib['protocol'] = self.protocol
        return result

    @staticmethod
    def parse(e: Element) -> 'FeedCloud':
        """Parse the given 'cloud' element from an RSS document."""
        return FeedCloud(
            e.attrib['domain'],
            int(e.attrib['port']),
            e.attrib['path'],
            e.attrib['registerProcedure'],
            e.attrib['protocol']
        )


@dataclass
class FeedTextInput:
    """
    Stores a textInput field as defined by the RSS specification.
    """
    title: str
    description: str
    name: str
    link: str

    def render(self) -> Element:
        """Render this item into an XML element."""
        result = Element('textInput')

        title = SubElement(result, 'title')
        title.text = self.title

        description = SubElement(result, 'description')
        description.text = self.description

        name = SubElement(result, 'name')
        name.text = self.name

        link = SubElement(result, 'link')
        link.text = self.link

        return result

    @staticmethod
    def parse(e: Element) -> 'FeedTextInput':
        """Parse the given 'textInput' element from an RSS document."""
        return FeedTextInput(
            _get(e, 'title'),
            _get(e, 'description'),
            _get(e, 'name'),
            _get(e, 'link')
        )


@dataclass
class FeedSkipHours:
    """
    Stores the contents of a skipHours element as defined by
    the RSS specification.
    """
    hours: list[int]

    def render(self) -> Element:
        """Render this item into an XML element."""
        result = Element('skipHours')

        for h in self.hours:
            e = SubElement(result, 'hour')
            e.text = str(h)

        return result

    @staticmethod
    def parse(e: Element) -> 'FeedSkipHours':
        """Parse the given 'skipHours' element from an RSS document."""
        return FeedSkipHours(
            _parse_list(e, 'hour', lambda h: int(h.text))
        )


@dataclass
class FeedSkipDays:
    """
    Stores the contents of a skipDays element as defined by
    the RSS specification.
    """
    days: list[str]

    def render(self) -> Element:
        """Render this item into an XML element."""
        result = Element('skipDays')

        for d in self.days:
            e = SubElement(result, 'day')
            e.text = str(d)

        return result

    @staticmethod
    def parse(e: Element) -> 'FeedSkipDays':
        """Parse the given 'skipDays' element from an RSS document."""
        return FeedSkipDays(
            _parse_list(e, 'day', lambda d: d.text)
        )


@dataclass
class FeedMetadata:
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
    categories: Optional[list[FeedCategory]] = None
    generator: Optional[str] = None
    docs: Optional[str] = None
    cloud: Optional[FeedCloud] = None
    ttl: Optional[int] = None
    image: Optional[FeedImage] = None
    rating: Optional[str] = None
    text_input: Optional[FeedTextInput] = None
    skip_hours: Optional[FeedSkipHours] = None
    skip_days: Optional[FeedSkipDays] = None

    def render(self) -> Element:
        """Render this item into an XML element."""
        result = Element('channel')

        title = SubElement(result, 'title')
        title.text = self.title

        link = SubElement(result, 'link')
        link.text = self.link

        description = SubElement(result, 'description')
        description.text = self.description

        if self.language is not None:
            language = SubElement(result, 'language')
            language.text = self.language

        if self.copyright is not None:
            cc = SubElement(result, 'copyright')
            cc.text = self.copyright

        if self.managing_editor is not None:
            managing_editor = SubElement(result, 'managingEditor')
            managing_editor.text = self.managing_editor

        if self.web_master is not None:
            web_master = SubElement(result, 'webMaster')
            web_master.text = self.web_master

        if self.pub_date is not None:
            pub_date = SubElement(result, 'pubDate')
            pub_date.text = format_datetime(self.pub_date)

        if self.last_build_date is not None:
            last_build_date = SubElement(result, 'lastBuildDate')
            last_build_date.text = format_datetime(self.last_build_date)

        if self.categories is not None:
            result.extend(c.render() for c in self.categories)

        if self.generator is not None:
            generator = SubElement(result, 'generator')
            generator.text = self.generator

        if self.docs is not None:
            docs = SubElement(result, 'docs')
            docs.text = self.docs

        if self.cloud is not None:
            result.append(self.cloud.render())

        if self.ttl is not None:
            ttl = SubElement(result, 'ttl')
            ttl.text = str(self.ttl)

        if self.image is not None:
            result.append(self.image.render())

        if self.rating is not None:
            rating = SubElement(result, 'rating')
            rating.text = self.rating

        if self.text_input is not None:
            result.append(self.text_input.render())

        if self.skip_hours is not None:
            result.append(self.skip_hours.render())

        if self.skip_days is not None:
            result.append(self.skip_days.render())

        return result

    @staticmethod
    def parse(e: Element) -> 'FeedMetadata':
        """
        Parse all RSS-specified metadata
        from the given 'channel' element.
        """
        return FeedMetadata(
            _get(e, 'title'),
            _get(e, 'link'),
            _get(e, 'description'),
            _get_opt(e, 'language'),
            _get_opt(e, 'copyright'),
            _get_opt(e, 'managingEditor'),
            _get_opt(e, 'webMaster'),
            _get_opt(e, 'pubDate', parsedate_to_datetime),
            _get_opt(e, 'lastBuildDate', parsedate_to_datetime),
            _parse_list(e, 'category', FeedCategory.parse),
            _get_opt(e, 'generator'),
            _get_opt(e, 'docs'),
            _parse_opt(e, 'cloud', FeedCloud.parse),
            _get_opt(e, 'ttl', int),
            _parse_opt(e, 'image', FeedImage.parse),
            _get_opt(e, 'rating'),
            _parse_opt(e, 'textInput', FeedTextInput.parse),
            _parse_opt(e, 'skipHours', FeedSkipHours.parse),
            _parse_opt(e, 'skipDays', FeedSkipDays.parse)
        )


@dataclass
class SlicedFeed:
    """Defines how to produce a sliced feed from a set of input feeds."""
    meta: FeedMetadata
    slicers: list[tuple[str, Callback]]
    keep_unrecognized: bool = False


def slice_feeds(
        input_feeds: list[Element],
        output_feed: SlicedFeed) -> list[Element]:
    """Slice a set of RSS feeds according to the specified output feeds."""
    _ = input_feeds, output_feed
