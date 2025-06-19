from lxml.etree import ElementTree as Element
from dataclasses import dataclass
from typing import Callable


@dataclass
class Mutation:
    query: str
    mutator: Callable[[Element], bool]


def apply_one_mutation(tree: Element, mutation: Mutation):
    nodes = tree.findall(mutation.query)
    to_remove = []
    for node in nodes:
        if mutation.mutator(node):
            to_remove.append(node)

    for node in to_remove:
        node.find('..').remove(node)


def apply_mutations(tree: Element, mutations: list[Mutation]):
    for mutation in mutations:
        apply_one_mutation(tree, mutation)
