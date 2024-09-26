# test_crawler.py

from bs4 import BeautifulSoup
import os
import logging
import requests
import unittest
from unittest.mock import patch, Mock
from urllib.parse import urljoin

import crawler
from crawler import common_selectors


# Disable logging during tests
logging.disable(logging.CRITICAL)

class TestFetchContent(unittest.TestCase):
    @patch('crawler.requests.get')
    def test_fetch_content_success(self, mock_get):
        # Set up the mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>Test content</body></html>'
        mock_response.url = 'http://example.com/test'
        mock_get.return_value = mock_response

        # Call the function
        content, url = crawler.fetch_content('http://example.com/test')

        # Assertions
        self.assertEqual(content, '<html><body>Test content</body></html>')
        self.assertEqual(url, 'http://example.com/test')

    @patch('crawler.requests.get')
    def test_fetch_content_failure(self, mock_get):
        # Set up the mock response to raise an exception
        mock_get.side_effect = requests.exceptions.RequestException('Error')

        # Call the function
        content, url = crawler.fetch_content('http://example.com/test')

        # Assertions
        self.assertIsNone(content)
        self.assertIsNone(url)


class TestGetLinks(unittest.TestCase):
    def test_get_links_all_paths(self):
        html = '''
        <a href="/page1">Page 1</a>
        <a href="http://example.com/page2">Page 2</a>
        <a href="http://otherdomain.com/page3">Page 3</a>
        '''
        base_url = 'http://example.com'
        links = crawler.get_links(html, base_url)
        expected_links = {
            'http://example.com/page1',
            'http://example.com/page2',
        }
        self.assertEqual(links, expected_links)

    def test_get_links_with_allowed_paths(self):
        html = '''
        <a href="/docs/page1">Docs Page 1</a>
        <a href="/api/page2">API Page 2</a>
        <a href="/about">About</a>
        '''
        base_url = 'http://example.com'
        allowed_paths = ['/docs/', '/api/']
        links = crawler.get_links(html, base_url, allowed_paths=allowed_paths)
        expected_links = {
            'http://example.com/docs/page1',
            'http://example.com/api/page2',
        }
        self.assertEqual(links, expected_links)

    def test_get_links_with_index_html(self):
        html = '''
        <a href="/docs/">Docs Home</a>
        <a href="/docs/index.html">Docs Index</a>
        <a href="/api/index.html">API Index</a>
        <a href="/api/">API Home</a>
        '''
        base_url = 'http://example.com'
        allowed_paths = ['/docs', '/api']
        links = crawler.get_links(html, base_url, allowed_paths=allowed_paths)
        expected_links = {
            'http://example.com/docs',
            'http://example.com/api',
        }
        self.assertEqual(links, expected_links)


class TestIsAllowedByRobots(unittest.TestCase):
    def test_is_allowed_by_robots(self):
        robots_parser = Mock()
        robots_parser.can_fetch.return_value = True
        url = 'http://example.com/page'
        self.assertTrue(crawler.is_allowed_by_robots(url, robots_parser=robots_parser))
        robots_parser.can_fetch.assert_called_with('*', '/page')

    def test_is_disallowed_by_robots(self):
        robots_parser = Mock()
        robots_parser.can_fetch.return_value = False
        url = 'http://example.com/secret'
        self.assertFalse(crawler.is_allowed_by_robots(url, robots_parser=robots_parser))
        robots_parser.can_fetch.assert_called_with('*', '/secret')


class TestRemoveCommonElements(unittest.TestCase):
    def test_remove_common_elements(self):
        html = '''
        <html>
            <body>
                <header>Header</header>
                <nav>Navigation</nav>
                <section>
                    <header>Section header</header>
                Main content
                </section>
                <footer>Footer</footer>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        soup = crawler.remove_common_elements(soup, extra_remove_selectors=common_selectors)
        result = str(soup)
        self.assertNotIn('Header', result)
        self.assertNotIn('Navigation', result)
        self.assertNotIn('Footer', result)
        self.assertIn('Main content', result)

    def test_remove_common_elements_with_extra_selectors(self):
        html = '''
        <html>
            <body>
                <header>Header</header>
                <div class="ad">Ad Content</div>
                <div>Main content</div>
                <footer>Footer</footer>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        soup = crawler.remove_common_elements(soup, extra_remove_selectors=['header', 'footer', '.ad'])
        result = str(soup)
        self.assertNotIn('Header', result)
        self.assertNotIn('Ad Content', result)
        self.assertNotIn('Footer', result)
        self.assertIn('Main content', result)


class TestBuildTree(unittest.TestCase):
    @patch('crawler.fetch_content')
    def test_build_tree(self, mock_fetch_content):
        # Mock fetch_content to return predefined HTML content
        def side_effect(url):
            if url == 'http://example.com/start':
                html = '''
                <html>
                    <body>
                        <div>Start Page Content</div>
                        <a href="/page1">Page 1</a>
                    </body>
                </html>
                '''
                return html, url
            elif url == 'http://example.com/page1':
                html = '''
                <html>
                    <body>
                        <div>Page 1 Content</div>
                        <a href="/start">Start Page</a>
                    </body>
                </html>
                '''
                return html, url
            else:
                return '', url

        mock_fetch_content.side_effect = side_effect

        # Run build_tree
        page_markdowns, url_to_anchor = crawler.build_tree(
            start_url='http://example.com/start',
            base_url='http://example.com',
            handle_robots_txt=False,
            delay=0,
            delay_range=0,
            allowed_paths=None
        )

        # Check that page_markdowns contains two entries
        self.assertIn('http://example.com/start', page_markdowns)
        self.assertIn('http://example.com/page1', page_markdowns)

        # Check content
        self.assertIn('Start Page Content', page_markdowns['http://example.com/start'])
        self.assertIn('Page 1 Content', page_markdowns['http://example.com/page1'])


class TestDeduplicateContent(unittest.TestCase):
    def test_deduplicate_content_no_common(self):
        page_markdowns = {
            'http://example.com/start': 'Start Page Content\n\nUnique to Start',
            'http://example.com/page1': 'Page 1 Content\n\nUnique to Page1',
            'http://example.com/page2': 'Page 2 Content\n\nUnique to Page2',
        }
        unique_content, common_content = crawler.deduplicate_content(
            page_markdowns, similarity_threshold=0.99, min_block_length=20
        )

        # No common content expected
        self.assertEqual(len(common_content), 0)

        # All unique content should be present
        self.assertEqual(unique_content['http://example.com/start'], ['Start Page Content', 'Unique to Start'])
        self.assertEqual(unique_content['http://example.com/page1'], ['Page 1 Content', 'Unique to Page1'])
        self.assertEqual(unique_content['http://example.com/page2'], ['Page 2 Content', 'Unique to Page2'])


    def test_deduplicate_content_with_common(self):
        page_markdowns = {
            'http://example.com/start': 'Common Content\n\nStart Page Content',
            'http://example.com/page1': 'Common Content\n\nPage 1 Content',
            'http://example.com/page2': 'Common Content\n\nPage 2 Content',
        }
        unique_content, common_content = crawler.deduplicate_content(
            page_markdowns, similarity_threshold=0.99, min_block_length=20
        )

        # Common content should have 'Common Content'
        self.assertIn('Common Content', common_content)

        # Unique content should exclude 'Common Content'
        self.assertEqual(unique_content['http://example.com/start'], ['Start Page Content'])
        self.assertEqual(unique_content['http://example.com/page1'], ['Page 1 Content'])
        self.assertEqual(unique_content['http://example.com/page2'], ['Page 2 Content'])



class TestTraverseAndBuildMarkdown(unittest.TestCase):
    def test_traverse_and_build_markdown(self):
        unique_content = {
            'http://example.com/start': ['Start Page Content'],
            'http://example.com/page1': ['Page 1 Content'],
            'http://example.com/page2': ['Page 2 Content'],
        }
        common_content = ['Common Content']
        url_to_anchor = {
            'http://example.com/start': 'start',
            'http://example.com/page1': 'page1',
            'http://example.com/page2': 'page2',
        }
        final_markdown = crawler.traverse_and_build_markdown(unique_content, common_content, url_to_anchor)

        # Check that anchors are correctly added
        self.assertIn('<a id="start">http://example.com/start</a>', final_markdown)
        self.assertIn('<a id="page1">http://example.com/page1</a>', final_markdown)
        self.assertIn('<a id="page2">http://example.com/page2</a>', final_markdown)

        # Check that unique content is present
        self.assertIn('Start Page Content', final_markdown)
        self.assertIn('Page 1 Content', final_markdown)
        self.assertIn('Page 2 Content', final_markdown)

        # Check that common sections are added at the end
        self.assertIn('# Common Sections', final_markdown)
        self.assertIn('Common Content', final_markdown)


class TestCrawlAndConvert(unittest.TestCase):
    def setUp(self):
        # Set up parameters for testing
        self.base_url = 'http://example.com'
        self.starting_point = '/start'
        self.start_url = urljoin(self.base_url, self.starting_point)
        self.output_filename = 'test_output.md'

        # Mock HTML pages with links between them
        self.html_start = """
        <html>
            <body>
                <header><h1>pages</h1></header>
                <div>Common Content</div>
                <div>
                    <h2>Start Page</h2>
                    the Start Page content like a b and c
                </div>
                <h3>nav</h3>
                <ul>
                    <li><a id="start">Start Page</a></li>
                    <li><a id="page1" href="/page1">Page 1</a></li>
                    <li><a id="page2" href="/page2">Page 2</a></li>
                </ul>
            </body>
        </html>
        """

        self.html_page1 = """
        <html>
            <body>
                <div>Common Content</div>
                <div>
                <h2>Page 1</h2>
                <span>Only Page 1's content should appear here.</span>
                </div>
                <h3>nav</h3>
                <ul>
                    <li><a id="start" href="/start">Start Page</a></li>
                    <li><a id="page1">Page 1</a></li>
                    <li><a id="page2" href="/page2">Page 2</a></li>
                </ul>
            </body>
        </html>
        """

        self.html_page2 = """
        <html>
            <body>
                <div>Common Content</div>
                <div>
                <h2>Page 2</h2>
                <p>This is Page's 2 Content</p>
                <a id="page3" href="/page3.html">Page 3</a>
                </div>
                <h3>nav</h3>
                <ul>
                    <li><a id="start" href="/start">Start Page</a></li>
                    <li><a id="page1" href="/page1">Page 1</a></li>
                    <li><a id="page2" href="/page2">Page 2</a></li>
                </ul>
            </body>
        </html>
        """

        self.html_page3 = """
        <html>
            <body>
                <div>Common Content</div>
                <div>
                <h2>Page 3</h2>
                random pg 3 Content
                </div>
            </body>
        </html>
        """


    def tearDown(self):
        if os.path.exists(self.output_filename):
            os.remove(self.output_filename)


    @patch('crawler.fetch_content')
    def test_crawl_and_convert(self, mock_fetch_content):
        # Define side effect for fetch_content
        def side_effect(url):
            normalized_url = crawler.normalize_url(url)
            if normalized_url == crawler.normalize_url(self.start_url):
                return self.html_start, url
            elif normalized_url == crawler.normalize_url(urljoin(self.base_url, 'page1')):
                return self.html_page1, urljoin(self.base_url, 'page1')
            elif normalized_url == crawler.normalize_url(urljoin(self.base_url, 'page2')):
                return self.html_page2, urljoin(self.base_url, 'page2')
            elif normalized_url == crawler.normalize_url(urljoin(self.base_url, 'page3.html')):
                return self.html_page3, urljoin(self.base_url, 'page3.html')
            elif normalized_url == crawler.normalize_url(urljoin(self.base_url, 'index.html')):
                # index.html redirects to start
                return self.html_start, self.start_url
            else:
                return '', url

        mock_fetch_content.side_effect = side_effect

        # Run the crawler with appropriate similarity threshold
        crawler.crawl_and_convert(
            start_url=self.start_url,
            base_url=self.base_url,
            output_filename=self.output_filename,
            handle_robots_txt=False,
            delay=0,
            delay_range=0,
            extra_remove_selectors=['header', 'footer', '.footer'],
            similarity_threshold=0.6,  # Increased threshold
            allowed_paths=None
        )

        # Read the content
        with open(self.output_filename, 'r', encoding='utf-8') as f:
            content = f.read()

            print(content)

            # Check that common sections are included once at the end
            self.assertIn('# Common Sections', content)
            self.assertEqual(content.count('Common Content'), 1)  # Common content should appear once

            # Check that unique content is present
            self.assertIn('the Start Page content like a b and c', content)
            self.assertIn('Only Page 1\'s content should appear here.', content)
            self.assertIn('This is Page\'s 2 Content', content)
            self.assertIn('random pg 3 Content', content)

            # Check that internal links are adjusted to anchors
            self.assertIn('[Page 1](#page1)', content)
            self.assertIn('[Page 2](#page2)', content)


            # Ensure that common content is not duplicated
            #occurrences = content.count('### nav')
            #self.assertEqual(occurrences, 1)
            occurrences = content.count('Common Content')
            self.assertEqual(occurrences, 1)


if __name__ == '__main__':
    unittest.main()
