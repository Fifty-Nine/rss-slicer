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
from typing import Annotated, Callable
from xml.etree.ElementTree import Element
from rss_slicer import rss

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
        parent = tree.find(f'{query}/..')
        assert parent is not None
        parent.remove(node)


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


@dataclass
class SlicedFeed:
    """Defines how to produce a sliced feed from a set of input feeds."""
    meta: rss.Channel
    slicers: list[tuple[str, Callback]]
    keep_unrecognized: bool = False


def slice_feeds(
        input_feeds: list[Element],
        output_feed: SlicedFeed) -> list[Element]:  # pragma: no cover
    """Slice a set of RSS feeds according to the specified output feeds."""
    _ = input_feeds, output_feed
    return []
