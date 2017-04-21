# -*- coding: utf-8 -*-
from __future__ import print_function
import re
import sys
import scraperwiki
from datetime import datetime
from bs4 import BeautifulSoup

def get_episode_links():
    html = scraperwiki.scrape('http://www.tiestoblog.com/category/podcast/')
    soup = BeautifulSoup(html)
    postings = soup.select('[role="main"] .post a[href]')
    for p in postings:
        item_href = p.attrs.get('href')
        if not item_href:
            print('Odd, a[href] had no href %s' % repr(p), file=sys.stderr)
            continue
        if re.search(r'-\d+/$', item_href):
            yield item_href
        else:
            print('Skipping unexpected href: %s' % repr(item_href), file=sys.stderr)


def get_episode_bodies():
    for url in get_episode_links():
        html = scraperwiki.scrape(url)
        soup = BeautifulSoup(html)
        contents = soup.select('[role="main"] .post .entry-content')
        if not contents:
            print('Unable to find entry content in %s' % repr(html), file=sys.stderr)
            continue
        content_el = contents[0]
        ma = re.search(r'-(\d+)/$', url)
        if not ma:
            print('Odd URL you have there "%s"' % repr(url), file=sys.stderr)
            episode = 0
        else:
            episode = int(ma.group(1))
        # :type: list[unicode]
        parts = []
        for it in content_el.contents:
            # getattr is because NavigableString has no 'name'
            el_name = getattr(it, 'name', '')
            # skip over the <h?>Tracklist
            if el_name.startswith('h'):
                continue
            if el_name == 'br':
                parts.append('\n')
            else:
                parts.append(unicode(it))
        payload = u''.join(parts)
        payload = payload.strip()
        # sqlite prefers unicode, so don't encode the str
        output = {
            'episode': episode,
            'text': payload,
            'url': url,
        }
        yield output


def main():
    # careful, .weekday() is Monday indexed so Sun = 6
    #if 6 != datetime.utcnow().weekday():
    #    return 0
    data_items = list(get_episode_bodies())
    # episode# may be a better key
    scraperwiki.sqlite.save(unique_keys=['url'], data=data_items)


if __name__ == '__main__':
    main()
