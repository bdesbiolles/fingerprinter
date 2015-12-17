"""This script check if a remote website is using RoR."""

import argparse
import warnings
import os
import json
import logging
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(name=__name__)


class Webpage(object):
    """Simple reprentation of a Webpage."""

    def __init__(self, url, headers, html):
        """
        Initialize a new Webpage object.

        Parameters:
        url
        headers
        html
        """
        self.url = url
        self.headers = headers
        self.html = html

        self._parse_html()

    def _parse_html(self):
        """
        Parse the HTML with BeautifulSoup.

        find <script>, <meta> and <link> tags.
        """
        self.parsed_html = soup = BeautifulSoup(self.html, 'html.parser')
        self.scripts = [script['src'] for script in
                        soup.findAll('script', src=True)]
        self.meta = {
            meta['name'].lower():
                meta['content'] for meta in soup.findAll(
                    'meta', attrs=dict(name=True, content=True))
        }
        self.links = [link['href'] for link in
                      soup.findAll('link', href=True)]

    @classmethod
    def new_from_url(cls, url):
        """
        Construct a webpage object from an url.

        Parameters:
        url
        """
        logger.info("Creating webpage from url: %s", url)
        response = requests.get(url, verify=True, timeout=2.5)
        return cls(response.url, headers=response.headers, html=response.text)


class Fingerprinter(object):
    """Fingerprinter."""

    def __init__(self, heuristics):
        """
        Initialize a new Fingerprinter instance.

        Parameters:
        heuristics
        """
        self.heuristics = heuristics

        self._prepare_heuristic(heuristics)

    @classmethod
    def latest(cls, heuristic_file=None):
        """
        Construct a Fingerprinter instance.

        using the given heuristics db path,
        or the default path in data/heuristics.json.
        """
        if not heuristic_file:
            __location__ = os.path.realpath(os.path.join(os.getcwd(),
                                            os.path.dirname(__file__)))
            heuristic_file = os.path.join(__location__, 'data/heuristics.json')
        logger.info("Loading heuristics db at: %s", heuristic_file)
        with open(heuristic_file, 'r') as fd:
            obj = json.load(fd)

        return cls(heuristics=obj)

    def _prepare_heuristic(self, heuristics):
        """Normalize the data before compiling regex."""
        # Ensure these keys' values are lists
        for key in ['link', 'script']:
            try:
                value = heuristics[key]
            except KeyError:
                heuristics[key] = []
            else:
                if not isinstance(value, list):
                    heuristics[key] = [value]

        # Ensure these keys exist
        for key in ['headers', 'meta']:
            try:
                heuristics[key]
            except KeyError:
                heuristics[key] = {}

        # Ensure the 'meta' key is a dict
        obj = heuristics['meta']
        if not isinstance(obj, dict):
            heuristics['meta'] = {'generator': obj}

        # Ensure keys are lowercase
        for key in ['headers', 'meta']:
            obj = heuristics[key]
            heuristics[key] = {k.lower(): v for k, v in obj.items()}

        # Prepare regular expression patterns
        for key in ['link', 'script']:
            heuristics[key] = [self._prepare_pattern(pattern)
                               for pattern in heuristics[key]]

        for key in ['headers', 'meta']:
            obj = heuristics[key]
            for name in obj:
                obj[name] = self._prepare_pattern(obj[name])

    def _prepare_pattern(self, pattern):
        """Strip out key:value pairs from the pattern and compile the regex."""
        try:
            return re.compile(pattern, re.I)
        except re.error as error:
            warnings.warn(
                "Caught '{error}' compiling regex: {regex}"
                .format(error=error, regex=pattern)
            )
            # regex that never matches:
            # http://stackoverflow.com/a/1845097/413622
            return re.compile(r'(?!x)x')

    def analyze(self, webpage):
        """Return a list of the heuristics detected on the webpage."""
        detected_heuristics = set()
        logger.info("Analyzing webpage.")
        for name, regex in self.heuristics['headers'].items():
            if name in webpage.headers:
                content = webpage.headers[name]
                if regex.search(content):
                    logger.info("Found header %s: %s", name, content)
                    detected_heuristics.add('headers: ' + name)

        for regex in self.heuristics['script']:
            for script in webpage.scripts:
                if regex.search(script):
                    logger.info("Found script: src=\"%s\"", script)
                    detected_heuristics.add('script')

        for name, regex in self.heuristics['meta'].items():
            if name in webpage.meta:
                content = webpage.meta[name]
                if regex.search(content):
                    logger.info("Found meta: name=\"%s\" content=\"%s\"",
                                name, content)
                    detected_heuristics.add('meta: ' + name)

        for regex in self.heuristics['link']:
            for link in webpage.links:
                if regex.search(link):
                    logger.info("Found link: href=\"%s\"", link)
                    detected_heuristics.add('link')

        return detected_heuristics


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="indicate if remote website"
                                     " is using RoR")
    parser.add_argument("url", metavar="URL", type=str, nargs='+',
                        help="website url")
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="store_true")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        print("Score    URL  ")
    fingerprinter = Fingerprinter.latest()
    for url in args.url:
        webpage = Webpage.new_from_url(url)
        result = fingerprinter.analyze(webpage)
        if args.verbose:
            print("Score    URL  ")
        print(len(result), "/ 5   ", url)
