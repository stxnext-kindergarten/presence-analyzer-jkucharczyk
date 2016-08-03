# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
from __future__ import unicode_literals

import os.path
import json
import datetime
import unittest

import main
import views
import utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)


# pylint: disable=maybe-no-member, too-many-public-methods
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_memoize(self):
        utils.get_data()
        self.assertTrue('expire' in utils.CACHE['get_data'])
        self.assertTrue('data' in utils.CACHE['get_data'])
        utils.CACHE.clear()
        utils.get_data()
        self.assertTrue('expire' in utils.CACHE['get_data'])
        self.assertTrue('data' in utils.CACHE['get_data'])

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday.html')

    def test_render_templates(self):
        """
        Test rendering .html files to view.
        """
        resp_404 = self.client.get('/certainly_not_existing_page.foobar/')
        self.assertEqual(resp_404.status_code, 404)
        resp = self.client.get('/presence_start_end.html/')
        self.assertEqual(resp.status_code, 200)

    def test_mean_time_weekday_view(self):
        """
        Test mean presence time of given user grouped by weekday.
        """
        resp_user_not_found = self.client.get('/api/v1/mean_time_weekday/0')
        self.assertEqual(resp_user_not_found.status_code, 404)
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        correct_data = [
            ['Mon', 0],
            ['Tue', 30047.0],
            ['Wed', 24465.0],
            ['Thu', 23705.0],
            ['Fri', 0],
            ['Sat', 0],
            ['Sun', 0],
        ]
        self.assertEqual(data, correct_data)

    def test_presence_weekday_view(self):
        """
        Test total presence time of given user grouped by weekday.
        """
        resp_404 = self.client.get('/api/v1/presence_weekday/0')
        self.assertEqual(resp_404.status_code, 404)
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        correct_data = [
            ['Weekday', 'Presence (s)'],
            ['Mon', 0],
            ['Tue', 30047],
            ['Wed', 24465],
            ['Thu', 23705],
            ['Fri', 0],
            ['Sat', 0],
            ['Sun', 0],
        ]
        self.assertEqual(data, correct_data)

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v1/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data[0], {'user_id': 10, 'name': 'User 10'})

    def test_presence_start_end(self):
        """
        Test correctness of average start-end presence time of
        given user. Result must be sorted by weekday.
        """
        resp_404 = self.client.get('/api/v1/presence_start_end/0')
        self.assertEqual(resp_404.status_code, 404)
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        correct_data = [
            ['Mon', 0, 0],
            ['Tue', 34745.0, 64792.0],
            ['Wed', 33592.0, 58057.0],
            ['Thu', 38926.0, 62631.0],
            ['Fri', 0, 0],
            ['Sat', 0, 0], 
            ['Sun', 0, 0],
        ]

        data = json.loads(resp.data)
        self.assertEqual(correct_data, data)


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(
            data[10][sample_date]['start'],
            datetime.time(9, 39, 5)
        )

    def test_group_by_weekday(self):
        """
        Test grouping presence entries by weekday.
        """
        data = utils.get_data()
        correct_data = [[], [30047], [24465], [23705], [], [], []]
        self.assertEqual(utils.group_by_weekday(data[10]), correct_data)

    def test_seconds_since_midnight(self):
        """
        Test calculating the amount of seconds since midnight.
        """
        self.assertEqual(
            0, utils.seconds_since_midnight(datetime.time(0, 0, 0)),
        )
        self.assertEqual(
            36610,
            utils.seconds_since_midnight(datetime.time(10, 10, 10)),
        )

    def test_interval(self):
        """
        Test calculating the interval in seconds
        between two datetime.time objects.
        """
        self.assertEqual(
            0,
            utils.interval(datetime.time(0, 0, 0), datetime.time(0, 0, 0))
        )
        self.assertEqual(
            -5,
            utils.interval(datetime.time(0, 1, 0), datetime.time(0, 0, 55))
        )
        self.assertEqual(
            3675,
            utils.interval(datetime.time(0, 0, 0), datetime.time(1, 1, 15))
        )

    def test_mean(self):
        """
        Test calculating arithmetic mean.
        """
        self.assertEqual(0, utils.mean([]))
        self.assertEqual(2.5, utils.mean([5, 0]))
        self.assertAlmostEqual(1.914213, utils.mean([8**0.5, 1]), places=5)

    def test_start_end_time(self):
        """
        Test creating a correct data of start-end times
        structure for given user data.
        """
        data = utils.get_data()
        correct_data = {
            0: {'start': [], 'end': []},
            1: {'start': [34745], 'end': [64792]},
            2: {'start': [33592], 'end': [58057]},
            3: {'start': [38926], 'end': [62631]},
            4: {'start': [], 'end': []},
            5: {'start': [], 'end': []},
            6: {'start': [], 'end': []},
        }
        self.assertEqual(correct_data, utils.start_end_time(data[10]))


def suite():
    """
    Default test suite.
    """
    base_suite = unittest.TestSuite()
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    base_suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return base_suite


if __name__ == '__main__':
    unittest.main()
