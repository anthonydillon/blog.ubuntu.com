#! /usr/bin/env python3

# Core
import unittest
import time
from urlparse.parse import urlparse, urlunparse

# Local
import app
from api import get


def _get_posts():
    response = get(
        'posts',
        {
            '_embed': True,
            'per_page': 3,
            'group': "1479,1666"
        }
    )

    return response.json()


class WebAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.app.test_client()
        self.app.testing = True

    def test_cache(self):
        # Warm cache
        initial_posts = _get_posts()

        # Make a request with the cache warmed
        start = time.time()
        subsequent_posts = _get_posts()
        request_time = time.time() - start

        assert type(initial_posts) == list
        assert initial_posts == subsequent_posts
        assert request_time < 0.1

    def _get_check_slash_normalisation(self, uri):
        """
        Given a basic app path (e.g. '/page'), check that any trailing
        slashes are removed with a 302 redirect, and return the response
        for the principal URL
        """

        # Check trailing slashes trigger redirect
        parsed_uri = urlparse(uri)
        slash_uri = urlunparse(parsed_uri._replace(path=parsed_uri.path + '/'))
        redirect_response = self.app.get(slash_uri)
        assert redirect_response.status_code == 302

        url = "http://localhost" + uri
        assert redirect_response.headers.get('Location') == url

        return self._get_check_cache(url)

    def _get_check_cache(self, uri):
        """
        Retrieve URL contents twice - checking the second response is cached
        """

        # Warm cache
        initial_response = self.app.get(uri)

        # Make a request with the cache warmed
        start = time.time()
        subsequent_response = self.app.get(uri)
        request_time = time.time() - start

        assert initial_response.text == subsequent_response.text
        assert request_time < 0.1

        return subsequent_response

    def _check_basic_page(self, uri):
        """
        Check that a URI returns an HTML page that will redirect to remove
        slashes, returns a 200 and contains the standard footer text
        """

        if uri == '/':
            response = self._get_check_cache(uri)
        else:
            response = self._get_check_slash_normalisation(uri)

        assert response.status_code == 200
        assert "Ubuntu and Canonical are registered" in str(response.data)

        return response


if __name__ == '__main__':
    unittest.main()
