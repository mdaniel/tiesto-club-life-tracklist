# -*- coding: utf-8 -*-
from __future__ import print_function
import re
import sys
import scraperwiki
from bs4 import BeautifulSoup

def get_episode_links():
    html = scraperwiki.scrape('http://www.tiestoblog.com/tiesto-club-life/')
    soup = BeautifulSoup(html)
    postings = soup.select('[itemtype="http://schema.org/BlogPosting"]')
    for p in postings:
        bk_a_list = p.select('a[rel=bookmark]')
        if not bk_a_list:
            print('Unable to find rel=bookmark in %s' % repr(p), file=sys.stderr)
            continue
        bk_a = bk_a_list[0]
        item_href = bk_a.attrs.get('href')
        if not item_href:
            print('Odd, a@rel=bookmark had no href %s' % repr(bk_a), file=sys.stderr)
            continue
        if re.search(r'life-\d+/$', item_href):
            yield item_href
        else:
            print('Skipping unexpected href: %s' % repr(item_href), file=sys.stderr)


def get_episode_bodies():
    for url in get_episode_links():
        html = scraperwiki.scrape(url)
        soup = BeautifulSoup(html)
        entries = soup.select('[itemtype="http://schema.org/BlogPosting"]')
        if not entries:
            print('No blog postings on %s' % repr(url), file=sys.stderr)
            continue
        posting = entries[0]
        bodies = posting.select('[itemprop=articleBody]')
        if not bodies:
            print('Unable to find articleBody in %s' % repr(posting), file=sys.stderr)
            continue
        body = bodies[0]
        ma = re.search(r'life-(\d+)/$', url)
        if not ma:
            print('Odd URL you have there "%s"' % repr(url), file=sys.stderr)
            episode = 0
        else:
            episode = int(ma.group(1))
        # all that getattr jazz is because NavigableString has no 'name'
        payload = u''.join([u'\n%s\n ' % it.text if getattr(it, 'name', '').startswith('h')
                            else u''.join(['\n' if getattr(ii, 'name', '') == 'br' else unicode(ii)
                                           for ii in it.contents])
                            for it in body.contents])
        payload = payload.strip()
        # sqlite prefers unicode, so don't encode the str
        output = {
            'episode': episode,
            'text': payload,
            'url': url,
        }
        yield output


def main():
    data_items = list(get_episode_bodies())
    # episode# may be a better key
    scraperwiki.sqlite.save(unique_keys=['url'], data=data_items)


if __name__ == '__main__':
    main()
