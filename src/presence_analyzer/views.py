# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import logging

from flask import abort, redirect
from flask_mako import render_template, TemplateError

from main import app
from utils import (
    get_data,
    group_by_weekday,
    jsonify,
    mean,
    start_end_time,
)

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/presence_weekday.html')


@app.route('/<string:template_name>/', methods=['GET'])
def render_templates(template_name):
    """
    Render .html file to view.
    """
    if not template_name.endswith('.html'):
        template_name = '{}.html'.format(template_name)
    try:
        return render_template(template_name, name=template_name)
    except TemplateError:
        abort(404)


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [
        {'user_id': i, 'name': 'User {0}'.format(str(i))}
        for i in data.keys()
    ]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], mean(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]
    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    weekdays = group_by_weekday(data[user_id])
    result = [
        (calendar.day_abbr[weekday], sum(intervals))
        for weekday, intervals in enumerate(weekdays)
    ]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end(user_id):
    """
    Returns average start-end presence time of
    given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        abort(404)

    scratch = start_end_time(data[user_id])
    result = [
        (
            calendar.day_abbr[day],
            mean(intervals['start']),
            mean(intervals['end']),
        )
        for day, intervals in scratch.items()
    ]
    return result
