#
# Copyright 2014 Google Inc. All rights reserved.
#
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
#

"""Converts Python types to string representations suitable for Maps API server.

    For example:

    sydney = {
        "lat" : -33.8674869,
        "lng" : 151.2069902
    }

    convert.latlng(sydney)
    # '-33.8674869,151.2069902'
"""

import time as _time


def latlng(arg):
    """Converts a lat/lon pair to a comma-separated string.

    For example:

    sydney = {
        "lat" : -33.8674869,
        "lng" : 151.2069902
    }

    convert.latlng(sydney)
    # '-33.8674869,151.2069902'

    :param arg: The lat/lon pair.
    :type arg: dict or list or tuple
    """
    return "%f,%f" % normalize_lat_lng(arg)

def normalize_lat_lng(arg):
    """Take the various lat/lng representations and return a tuple.

    Accepts various representations:
    1) dict with two entries - "lat" and "lng"
    2) list or tuple - e.g. (-33, 151) or [-33, 151]

    :param arg: The lat/lng pair.
    :type arg: dict or list or tuple

    :rtype: tuple (lat, lng)
    """
    if isinstance(arg, dict):
        if "lat" in arg and "lng" in arg:
            return arg["lat"], arg["lng"]

    # List or tuple.
    if _is_list(arg):
        return arg[0], arg[1]

    raise TypeError(
        "Expected a lat/lng dict or tuple, "
        "but got %s" % type(arg).__name__)


def join_list(sep, arg):
    """If arg is list-like, then joins it with sep.
    :param sep: Separator string.
    :type sep: string
    :param arg: Value to coerce into a list.
    :type arg: string or list of string
    :rtype: string
    """
    return sep.join(as_list(arg))


def as_list(arg):
    """Coerces arg into a list. If arg is already list-like, returns arg.
    Otherwise, returns a one-element list containing arg.
    :rtype: list
    """
    if _is_list(arg):
        return arg
    return [arg]


def _is_list(arg):
    """Checks if arg is list-like. This excludes strings."""
    if isinstance(arg, str): # Python 3-only, as str has __iter__
        return False
    return (not _has_method(arg, "strip")
            and _has_method(arg, "__getitem__")
            or _has_method(arg, "__iter__"))

def is_string(val):
    """Determines whether the passed value is a string, safe for 2/3."""
    try:
        basestring
    except NameError:
        return isinstance(val, str)
    return isinstance(val, basestring)

def time(arg):
    """Converts the value into a unix time (seconds since unix epoch).

    For example:
        convert.time(datetime.now())
        # '1409810596'

    :param arg: The time.
    :type arg: datetime.datetime or int
    """
    # handle datetime instances.
    if _has_method(arg, "timetuple"):
        arg = _time.mktime(arg.timetuple())

    if isinstance(arg, float):
        arg = int(arg)

    return str(arg)


def _has_method(arg, method):
    """Returns true if the given object has a method with the given name.

    :param arg: the object
    :param method: the method name
    :type method: string
    :rtype: bool
    """
    return hasattr(arg, method) and callable(getattr(arg, method))


def components(arg):
    """Converts a dict of components to the format expected by the Google Maps
    server.

    For example:
    c = {"country": "US", "postal_code": "94043"}
    convert.components(c)
    # 'country:US|postal_code:94043'

    :param arg: The component filter.
    :type arg: dict
    :rtype: basestring
    """
    if isinstance(arg, dict):
        arg = sorted(["%s:%s" % (k, arg[k]) for k in arg])
        return "|".join(arg)

    raise TypeError(
        "Expected a string or dict for components, "
        "but got %s" % type(arg).__name__)


def bounds(arg):
    """Converts a lat/lon bounds to a comma- and pipe-separated string.

    Accepts two representations:
    1) string: pipe-separated pair of comma-separated lat/lon pairs.
    2) dict with two entries - "southwest" and "northeast". See convert.latlng
    for information on how these can be represented.

    For example:

    sydney_bounds = {
        "northeast" : {
            "lat" : -33.4245981,
            "lng" : 151.3426361
        },
        "southwest" : {
            "lat" : -34.1692489,
            "lng" : 150.502229
        }
    }

    convert.bounds(sydney_bounds)
    # '-34.169249,150.502229|-33.424598,151.342636'

    :param arg: The bounds.
    :type arg: dict
    """

    if isinstance(arg, dict):
        if "southwest" in arg and "northeast" in arg:
            return "%s|%s" % (latlng(arg["southwest"]),
                              latlng(arg["northeast"]))

    raise TypeError(
        "Expected a bounds (southwest/northeast) dict, "
        "but got %s" % type(arg).__name__)


def decode_polyline(polyline):
    """Decodes a Polyline string into a list of lat/lng dicts.

    See the developer docs for a detailed description of this encoding:
    https://developers.google.com/maps/documentation/utilities/polylinealgorithm

    :param polyline: An encoded polyline
    :type polyline: string

    :rtype: list of dicts with lat/lng keys
    """
    points = []
    index = lat = lng = 0

    while index < len(polyline):
        result = 1
        shift = 0
        while True:
            b = ord(polyline[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1f:
                break
        lat += (~result >> 1) if (result & 1) != 0 else (result >> 1)

        result = 1
        shift = 0
        while True:
            b = ord(polyline[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1f:
                break
        lng += ~(result >> 1) if (result & 1) != 0 else (result >> 1)

        points.append({"lat": lat * 1e-5, "lng": lng * 1e-5})

    return points


def encode_polyline(points):
    """Encodes a list of points into a polyline string.

    See the developer docs for a detailed description of this encoding:
    https://developers.google.com/maps/documentation/utilities/polylinealgorithm

    :param points: a list of lat/lng pairs
    :type points: list of dicts or tuples

    :rtype: string
    """
    last_lat = last_lng = 0
    result = ""

    for point in points:
        ll = normalize_lat_lng(point)
        lat = int(round(ll[0] * 1e5))
        lng = int(round(ll[1] * 1e5))
        d_lat = lat - last_lat
        d_lng = lng - last_lng

        for v in [d_lat, d_lng]:
            v = ~(v << 1) if v < 0 else v << 1
            while v >= 0x20:
                result += (chr((0x20 | (v & 0x1f)) + 63))
                v >>= 5
            result += (chr(v + 63))

        last_lat = lat
        last_lng = lng

    return result
