# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
import logging
import operator

from flask import abort, redirect
from flask_mako import render_template, TemplateError
from mako.exceptions import TopLevelLookupException

from main import app
from utils import (
    get_data,
    get_data_by_month,
    get_monthly_data,
    get_xml,
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


@app.route('/favicon.ico')
def favicon():
    """
    Prevents from rendering favicon.ico by render_templates method.
    Returns response code 404 as favicon.ico currently does not exist.
    """
    abort(404)


@app.route('/<string:template_name>/', methods=['GET'])
def render_templates(template_name):
    """
    Render .html file to view.
    """
    if not template_name.endswith('.html'):
        template_name = '{}.html'.format(template_name)
    try:
        return render_template(template_name, name=template_name)
    except (TemplateError, TopLevelLookupException):
        abort(404)


@app.route('/api/v1/years', methods=['GET'])
@jsonify
def years_view():
    """
    Sorted years listing for a dropdown.
    """
    data = get_data_by_month()
    return list(sorted(data.keys()))


@app.route('/api/v1/top_employees/<string:year>/', methods=['GET'])
@jsonify
def months_view(year):
    """
    Sorted months listing for dropdown.
    """
    data = get_data_by_month()
    if year in data.keys():
        return [
            (month, calendar.month_name[int(month)])
            for month in sorted(data[year].keys())
        ]
    abort(404)


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Sorted users listing for dropdown.
    """
    return get_xml()


@app.route('/api/v1/top_employees/<string:year>/<string:month>/', methods=['GET'])
@jsonify
def top_employees_by_month_view(year, month):
    """
    Returns a dict of users in given year-month sorted by worked_hours.
    """
    try:
        data = get_monthly_data(year, month)
    except KeyError:
        abort(404)
    else:
        return sorted(
            data.items(),
            key=lambda x: operator.getitem(x[1], 'worked_hours'),
            reverse=True,
        )


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
