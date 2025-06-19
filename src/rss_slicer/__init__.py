"""
RSS slicer library
~~~~~~~~~~~~~~~~~~

`rss-slicer` is an RSS feed slicer-dicer for combining an arbitrary
set of input RSS feeds and transforming them into a new set of output
streams.

:copyright: (c) 2025 by Tim Prince
:license: GPL v3, see COPYING for details.
"""
from typing import Annotated, Callable
from lxml.etree import ElementTree as Element


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
