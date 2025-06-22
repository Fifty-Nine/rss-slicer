"""Serialization helpers for RSS XML."""
from rss_slicer.rss._rss_types import (Category,
                                       Channel,
                                       Cloud,
                                       Image,
                                       SkipDays,
                                       SkipHours,
                                       TextInput)

from rss_slicer.rss._serialize import XMLSerialization

__all__ = [
    'CategoryXML',
    'ChannelXML',
    'CloudXML',
    'ImageXML',
    'SkipDaysXML',
    'SkipHoursXML',
    'TextInputXML'
]

CategoryXML = XMLSerialization[Category]
ChannelXML = XMLSerialization[Channel]
CloudXML = XMLSerialization[Cloud]
ImageXML = XMLSerialization[Image]
SkipDaysXML = XMLSerialization[SkipDays]
SkipHoursXML = XMLSerialization[SkipHours]
TextInputXML = XMLSerialization[TextInput]
