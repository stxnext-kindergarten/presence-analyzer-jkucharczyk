# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import logging
import threading

from datetime import datetime, timedelta
from flask import Response
from functools import wraps
from json import dumps
from lxml import etree

from main import app

log = logging.getLogger(__name__)  # pylint: disable=invalid-name

CACHE = {}


def memoize(secs=600):
    """
    Caches values of a function and stores them for a given period of time.
    """
    def decorator(func):
        def wrapped_func():
            """
            Returns data if cache didn't expire, else gets fresh one.
            """
            lock = threading.Lock()
            with lock:
                current_time = datetime.now()
                fname = func.__name__  # Stores function name
                if fname in CACHE and current_time <= CACHE[fname]['expire']:
                    return CACHE[fname]['data']
                CACHE[fname] = {
                    'expire': current_time + timedelta(seconds=secs),
                    'data': func(),
                }
                return CACHE[fname]['data']
        return wrapped_func
    return decorator


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        """
        This docstring will be overridden by @wraps decorator.
        """
        return Response(
            dumps(function(*args, **kwargs)),
            mimetype='application/json'
        )
    return inner


@memoize()
def get_data_by_month():
    """
    Gets data for common users in DATA_CSV file and USERS.xml.

    It creates structure like this:
    data = {
        '2011': {
            '01': {
                'user_id': {
                    'worked_hours': '404',
                    'avatar_url': 'https://google.com/12'
                }
            }
            '02': {
                'user_id': {
                    'worked_hours': '404',
                    'avatar_url': 'https://google.com/15'
                }
            }
        }
        '2012': {
            '01': {
                'user_id': {
                    'worked_hours': '480',
                    'avatar_url': 'https://google.com/13'
                }
            }
        }
    }
    """
    data = {}
    xml_data = get_xml()
    users_list = xml_data.keys()
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = str(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)
            else:
                year = str(date.year)
                month = '{:02.0f}'.format(date.month)
                worked_time = interval(start, end) / 3600.0
                if user_id in users_list:
                    if year not in data:
                        data[year] = {}
                    if month not in data[year]:
                        data[year][month] = {}
                    if user_id not in data[year][month]:
                        data[year][month][user_id] = {
                            'worked_hours': 0,
                            'avatar_url': xml_data[user_id]['avatar_url']
                        }
                    data[year][month][user_id]['worked_hours'] += worked_time
    return data


def get_monthly_data(year, month):
    """
    Returns data from given year and month.
    """
    data = get_data_by_month()
    xml_data = get_xml()
    monthly_data = data[year][month]
    result = {
        xml_data[x]['name']: monthly_data[x]
        for x in monthly_data.keys()
    }
    return result


@memoize()
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


@memoize()
def get_xml():
    """
    Extracts presence data from XML file and sorts it by user name.

    It creates structure like this:
    data = [
        '11': {
            'name': 'Michał B.',
            'avatar_url': 'intranet.stxnext.pl/api/img/1',
        },
        '142': {
            'name': 'Marek K.',
            'avatar_url': 'intranet.stxnext.pl/api/img/142',
        },
    ]
    """
    with open(app.config['DATA_XML'], 'r') as xmlfile:
        tree = etree.parse(xmlfile)
        server = tree.find('server')
        host = server.find('host').text
        protocol = server.find('protocol').text
        port = server.find('port').text
        users = tree.find('users')
        data = {
            user.get('id'): {
                'name': user.find('name').text,
                'avatar_url': "{}://{}:{}{}".format(
                    protocol,
                    host,
                    port,
                    user.find('avatar').text
                ),
            }
            for user in users.findall('user')
        }
    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = [[], [], [], [], [], [], []]  # one list for every day in week
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0


def start_end_time(user_data):
    """
    Returns dict which keys are weekdays numbers and values are
    dicts containings lists of  starting/end times.

    It creates a structure like this:
    result = {
        0: {
            'start': [...],
            'end': [...],
        }
        ...
        6: {
            'start': [...],
            'end': [...],
        }
    }
    """
    result = {i: {'start': [], 'end': []} for i in range(7)}
    for data in user_data:
        start = user_data[data]['start']
        end = user_data[data]['end']
        result[data.weekday()]['start'].append(seconds_since_midnight(start))
        result[data.weekday()]['end'].append(seconds_since_midnight(end))
    return result
