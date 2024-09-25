# crawler_cli.py

import argparse
from urllib.parse import urljoin

from crawler import crawl_and_convert


def main():
    parser = argparse.ArgumentParser(description='Crawl documentation and convert to Markdown.')
    parser.add_argument('base_url', help='The base URL of the documentation site.')
    parser.add_argument('starting_point', help='The starting path of the documentation.')
    parser.add_argument('-o', '--output', default='documentation.md',
                        help='Output filename (default: documentation.md).')
    parser.add_argument('--no-robots', action='store_true',
                        help='Ignore robots.txt rules.')
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay between requests in seconds.')
    parser.add_argument('--delay-range', type=float, default=0.5,
                        help='Range for random delay variation.')
    parser.add_argument('--remove-selectors', nargs='*',
                        help='Additional CSS selectors to remove from pages.')
    parser.add_argument('--similarity-threshold', type=float, default=0.8,
                        help='Similarity threshold for section comparison (default: 0.8).')
    parser.add_argument('--common-section-threshold', type=float, default=0.5,
                        help='Threshold for considering a section common (default: 0.5).')
    parser.add_argument('--user-agent', default='*',
                        help='User agent string to use for crawling (default: "*").')
    parser.add_argument('--allowed-paths', nargs='*',
                        help='List of URL paths to include during crawling.')

    args = parser.parse_args()

    start_url = urljoin(args.base_url, args.starting_point)

    crawl_and_convert(
        start_url=start_url,
        base_url=args.base_url,
        output_filename=args.output,
        user_agent=args.user_agent,
        handle_robots_txt=not args.no_robots,
        delay=args.delay,
        delay_range=args.delay_range,
        extra_remove_selectors=args.remove_selectors,
        similarity_threshold=args.similarity_threshold,
        common_section_threshold=args.common_section_threshold,
        allowed_paths=args.allowed_paths,
    )

if __name__ == '__main__':
    main()
