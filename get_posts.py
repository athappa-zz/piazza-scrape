#!/usr/bin/env python
from piazza_api import Piazza
from bs4 import BeautifulSoup
from HTMLParser import HTMLParser

import sys
import warnings

h = HTMLParser()
warnings.filterwarnings('ignore', category=UserWarning, module='bs4')

# Mapping from user-provided Piazza class name to Piazza network ID (https://piazza.com/class/{network_id})
CLASS_NETWORK_IDS = {
    'cpsc340': 'j2grn4bal3z44'
}


def unicode2str(string_in):
    """Use BeautifulSoup to parse raw text from HTML format"""
    soup = BeautifulSoup(string_in.encode('ascii', 'ignore'), 'lxml')
    text = ' '.join([s for s in soup.stripped_strings]).replace('\n', ' ').replace('\r', ' ')
    return h.unescape(text)


def main(piazza_class, output_filename):
    # Use Piazza API (https://github.com/hfaran/piazza-api) to login and fetch all posts for given class
    p = Piazza()
    p.user_login()
    piazza_class = p.network(CLASS_NETWORK_IDS[piazza_class])
    posts = piazza_class.iter_all_posts()

    f = open(output_filename, 'w')

    num_posts = 0
    for post in posts:
        if 'type' in post:
            if unicode2str(post['type']) == 'question':
                title = ''
                question = ''
                answer = ''
                timestamp = unicode2str(post['created'])
                tags = ' '.join(post['tags'])

                if post['history']:
                    if post['history'][0]['subject']:
                        title = unicode2str(post['history'][0]['subject'])
                    if post['history'][0]['content']:
                        question = unicode2str(post['history'][0]['content'])
                if post['children']:
                    if post['children'][0]:
                        if 'history' in post['children'][0]:
                            answer = unicode2str(post['children'][0]['history'][0]['content'])

                # Print each post as a single line in output file, with parts of posts delimited by '@@@'
                try:
                    f.write(title + '@@@' + question + '@@@' + answer + '@@@' + timestamp + '@@@' + tags + '\n')
                except UnicodeEncodeError as err:
                    print err
                    num_posts -= 1
                num_posts += 1
    print('Scraped %s posts\n' % num_posts)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python get_posts.py <piazza_class> <output_filename>')
        exit(1)
    main(sys.argv[1], sys.argv[2])

