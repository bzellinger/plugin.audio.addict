"""
    audioaddict.api
    Utility classes for accessing the AudioAddict API.
"""

import time
from datetime import datetime

import requests

from audioaddict.exceptions import ListenKeyError


class AudioAddictApi(object):
    def __init__(self, network_key):
        self._base_url = "https://api.audioaddict.com/v1/%s" % network_key

    def channels(self):
        r1 = requests.get("%s/channels" % self._base_url)
        r1.raise_for_status()

        r2 = requests.get("%s/listen/channels" % self._base_url)
        r2.raise_for_status()

        all_channels = r1.json()
        listen_channel_keys = [x['key'] for x in r2.json()]

        channels = []
        for channel in all_channels:
            if channel['key'] in listen_channel_keys:
                channels.append(Channel(channel))

        return channels

    def channel_by_key(self, key):
        r = requests.get("%s/channels/key/%s" % (self._base_url, key))
        r.raise_for_status()

        return Channel(r.json())

    def playlist(self, stream_key, channel_key, listen_key):
        r = requests.get("%s/listen/%s/%s" % (self._base_url, stream_key, channel_key),
                         params={'listen_key': listen_key})

        if r.status_code == 403:
            raise ListenKeyError()
        else:
            r.raise_for_status()

        return r.json()

    def track_history(self, channel_id):
        r = requests.get("%s/track_history/channel/%s" % (self._base_url, channel_id),
                         timeout=10)
        r.raise_for_status()
        return r.json()

    def currently_playing(self):
        # Cache-bust: this endpoint changes every few minutes.
        r = requests.get("%s/currently_playing" % self._base_url,
                         params={'_': int(time.time() * 1000)},
                         timeout=10)
        r.raise_for_status()
        return r.json()

    def track_details(self, track_id):
        r = requests.get("%s/tracks/%s" % (self._base_url, track_id), timeout=10)
        r.raise_for_status()
        return r.json()

    def current_track(self, channel_id):
        """Return the live now-playing track for a channel, or None."""
        playing = self.currently_playing()
        if not isinstance(playing, list):
            return None

        entry = None
        for item in playing:
            if isinstance(item, dict) and item.get('channel_id') == channel_id:
                entry = item
                break

        if not entry:
            return self._current_track_from_history(channel_id)

        track = entry.get('track') or {}
        if not isinstance(track, dict) or not track:
            return self._current_track_from_history(channel_id)

        artist = track.get('display_artist') or track.get('artist') or ''
        title = track.get('display_title') or track.get('title') or ''
        if not artist and not title:
            return self._current_track_from_history(channel_id)

        track_id = track.get('id')
        duration = track.get('duration') or track.get('length') or 0
        ends_at = _ends_at_from_start(track.get('start_time'), duration)

        return {
            'track_id': track_id,
            'artist': artist,
            'title': title,
            'art_url': '',
            'duration': duration,
            'ends_at': ends_at,
        }

    def track_art_url(self, track_id):
        if not track_id:
            return ''

        try:
            details = self.track_details(track_id)
        except requests.exceptions.RequestException:
            return ''

        images = details.get('images') or {}
        return _normalize_media_url(images.get('default') or '')

    def _current_track_from_history(self, channel_id):
        history = self.track_history(channel_id)
        if not isinstance(history, list):
            return None

        for entry in history:
            if not isinstance(entry, dict):
                continue
            if entry.get('type') == 'advertisement' or 'ad' in entry:
                continue

            artist = entry.get('display_artist') or entry.get('artist') or ''
            title = entry.get('display_title') or entry.get('title') or ''
            if not artist and not title and entry.get('track'):
                track_text = entry['track']
                if ' - ' in track_text:
                    artist, title = track_text.split(' - ', 1)
                else:
                    title = track_text

            if not artist and not title:
                continue

            started = entry.get('started') or 0
            duration = entry.get('duration') or entry.get('length') or 0
            ends_at = (started + duration) if started and duration else None

            return {
                'track_id': entry.get('track_id'),
                'artist': artist,
                'title': title,
                'art_url': _normalize_media_url(entry.get('art_url') or ''),
                'duration': duration,
                'ends_at': ends_at,
            }

        return None


def _normalize_media_url(url):
    if not url:
        return ''
    if url.startswith('//'):
        url = 'https:%s' % url
    elif url.startswith('http://'):
        url = 'https://%s' % url[7:]
    return url.split('{')[0]


def _ends_at_from_start(start_time, duration):
    if not start_time or not duration:
        return None

    try:
        started = datetime.fromisoformat(str(start_time)).timestamp()
        return started + float(duration)
    except (TypeError, ValueError):
        return None


class Channel(object):
    def __init__(self, parsed_json):
        self._channel = parsed_json

    def image_default(self):
        url = self._channel['images']['default']
        if url.startswith('//'):
            url = "https:%s" % url
        elif url.startswith('http://'):
            url = "https://%s" % url[7:]
        url = url.split('{')[0]

        return url

    @property
    def id(self):
        return self._channel['id']

    @property
    def key(self):
        return self._channel['key']

    @property
    def name(self):
        return self._channel['name']

    @property
    def creation_timestamp(self):
        return self._channel['created_at']
