"""
    audioaddict.listitem
    Kodi ListItem helpers compatible with Kodi 19 through Omega.
"""

from audioaddict.metadata import apply_track_to_listitem


def _channel_date_added(channel):
    date, time = channel.creation_timestamp.split('T')
    return "%s %s" % (date, time.split('-')[0])


def configure_channel_list_item(list_item, channel, track=None):
    """Apply music and live-stream metadata for a radio channel."""
    list_item.setProperty('IsPlayable', 'true')
    list_item.setProperty('IsInternetStream', 'true')

    apply_track_to_listitem(list_item, channel, track)

    timestamp = _channel_date_added(channel)
    if hasattr(list_item, 'getMusicInfoTag'):
        tag = list_item.getMusicInfoTag()
        if hasattr(tag, 'setDateAdded'):
            tag.setDateAdded(timestamp)
