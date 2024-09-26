# test_crawler.py

import unittest
from unittest.mock import patch, Mock
import crawler
import os
from urllib.parse import urljoin
import logging
import requests
from bs4 import BeautifulSoup

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
                <div>Main content</div>
                <footer>Footer</footer>
            </body>
        </html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        soup = crawler.remove_common_elements(soup)
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
        soup = crawler.remove_common_elements(soup, extra_selectors=['header', 'footer', '.ad'])
        result = str(soup)
        self.assertNotIn('Header', result)
        self.assertNotIn('Ad Content', result)
        self.assertNotIn('Footer', result)
        self.assertIn('Main content', result)


class TestGetShingles(unittest.TestCase):
    def test_get_shingles(self):
        text = 'This is a simple test for shingles generation'
        shingles = crawler.get_shingles(text, k=3)
        expected_shingles = {
            'This is a',
            'is a simple',
            'a simple test',
            'simple test for',
            'test for shingles',
            'for shingles generation',
        }
        self.assertEqual(shingles, expected_shingles)

    def test_get_shingles_short_text(self):
        text = 'Short text'
        shingles = crawler.get_shingles(text, k=5)
        self.assertEqual(shingles, set())


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

        root, _ = crawler.build_tree(
            start_url='http://example.com/start',
            base_url='http://example.com',
            handle_robots_txt=False,
            delay=0,
            delay_range=0,
            similarity_threshold=0.8,
            common_section_threshold=0.5,
            allowed_paths=None
        )

        # Check that the root node has one child
        self.assertEqual(len(root.children), 1)
        # Check that the child's URL is correct
        self.assertEqual(root.children[0].url, 'http://example.com/page1')


class TestTraverseTreeAndCollect(unittest.TestCase):
    def test_traverse_tree_and_collect(self):
        # Create a simple tree manually
        root = crawler.PageNode('http://example.com/start')
        root.sections = [BeautifulSoup('<div><h1>Start Page</h1><p>Start Page Content</p></div>', 'html.parser').div]
    
        child = crawler.PageNode('http://example.com/page1')
        child.sections = [BeautifulSoup('<div><h1>Page 1</h1><p>Page 1 Content</p></div>', 'html.parser').div]
        root.children.append(child)
    
        # Create url_to_anchor mapping
        url_to_anchor = {}
        content = crawler.traverse_tree_and_collect(root, url_to_anchor)
    
        # Check that the content includes the page content and the anchors
        self.assertIn('Start Page Content', content)
        self.assertIn('Page 1 Content', content)
        self.assertIn('<a id="start-page"></a>', content)
        self.assertIn('<a id="page-1"></a>', content)
        self.assertIn('# Start Page', content)
        self.assertIn('# Page 1', content)

        # Check that the anchors are added to url_to_anchor
        self.assertIn('http://example.com/start', url_to_anchor)
        self.assertIn('http://example.com/page1', url_to_anchor)
        self.assertEqual(url_to_anchor['http://example.com/start'], 'start-page')
        self.assertEqual(url_to_anchor['http://example.com/page1'], 'page-1')


class TestCrawlAndConvert(unittest.TestCase):
    def setUp(self):
        # Set up parameters for testing
        self.base_url = 'https://httpbin.org'
        self.starting_point = '/html'
        self.start_url = urljoin(self.base_url, self.starting_point)
        self.output_filename = 'test_output.md'

        # Modified HTML pages with links between them
        self.left_page = """
        <html>
            <body>
                <header>
                    <h1>Common Header</h1>
                </header>
                <section>
                    <p>This is unique content A.</p>
                    <p>This is common content A.</p>
                    <a href="https://httpbin.org/right">Link to right page.</a>
                </section>
                <footer>
                    <p>Common Footer</p>
                </footer>
            </body>
        </html>
        """

        self.right_page = """
        <html>
            <body>
                <header>
                    <h1>Common Header</h1>
                </header>
                <section>
                    <header>
                        <h2>Unique Header</h2>
                    </header>
                    <p>This is unique content B.</p>
                    <p>This is common content A.</p>
                    <a href="https://httpbin.org/html">Link to left page.</a>
                </section>
                <footer>
                    <p>Common Footer</p>
                </footer>
            </body>
        </html>
        """

    def tearDown(self):
        if os.path.exists(self.output_filename):
            os.remove(self.output_filename)

    def mock_fetch_content(self, url):
        """Mock fetch_content function to return test HTML content based on URL."""
        if url.endswith('/html'):
            return self.left_page, url
        elif url.endswith('/right'):
            return self.right_page, url
        else:
            # Return empty content or raise an error for unexpected URLs
            return '', url

@patch('crawler.fetch_content')
def test_crawl_and_convert(self, mock_fetch_content):
    mock_fetch_content.side_effect = self.mock_fetch_content

    # Run the crawler
    crawler.crawl_and_convert(
        start_url=self.start_url,
        base_url=self.base_url,
        output_filename=self.output_filename,
        handle_robots_txt=False,
        delay=0,
        delay_range=0,
        extra_remove_selectors=['nav', '.nav', '.navbar', '.footer'],
        similarity_threshold=0.8,
        common_section_threshold=0.5,
        allowed_paths=None
    )

    # Read the content
    with open(self.output_filename, 'r', encoding='utf-8') as f:
        content = f.read()

        print(content)
        
        # Verify that common sections are included once at the beginning
        self.assertIn('# Common Sections', content)

        self.assertEqual(content.count('Common Header'), 1)
        self.assertEqual(content.count('Common Footer'), 1)

        # Verify that common sections are not present in individual pages
        # The counts should be 1 (from the common section at the beginning)
        self.assertEqual(content.count('Common Header'), 1)
        self.assertEqual(content.count('Common Footer'), 1)

        # Verify that unique content is present
        self.assertIn('This is unique content A.', content)
        self.assertIn('This is unique content B.', content)

        # Verify that duplicate sections are not included multiple times
        occurrences = content.count('This is common content A.')
        self.assertEqual(occurrences, 1)  # Should appear once in common sections

        # Verify that unique contents are present only once
        occurrences = content.count('This is unique content A.')
        self.assertEqual(occurrences, 1)
        occurrences = content.count('This is unique content B.')
        self.assertEqual(occurrences, 1)


if __name__ == '__main__':
    unittest.main()
