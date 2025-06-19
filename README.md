`rss-slicer` is a Python library for slicing and dicing RSS feeds. The goal is
to enable users to take some arbitrary set of RSS feeds and transform them into
a new set of RSS feeds, mixing and matching items from each of the input feeds
to output feeds as specified by the user.

For example, the original motivating use case for this library was to take a
podcast which consisted of a public RSS feed and a private patreon-only RSS feed
and transform it into several RSS feeds for different categories of episodes
while omitting public feed preview items.

This library is under active development and does not yet provide any stable
APIs.
