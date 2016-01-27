#!/usr/bin/python -tt
#-*-coding:utf-8-*-
#
# Author: Brian Yang
# Email: brianyang1106@gmail.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import urllib2
import re
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count

def addslash(url):
    if not url.endswith('/'):
        return url + '/'
    else:
        return url

def process(online_url, userid):
    album_url = addslash(online_url) + 'album/' + \
                get_album_id(online_url)

    total = int(get_total(album_url))
    if total == 0:
        return

    # 90 is douban's default
    urls = []
    for page in range(0, total-1, 90):
        pid = str(page)
        appstr = '?start=%s&sortby=time' % pid
        phtml = addslash(album_url) + appstr
        urls.append(phtml)

    # parallel fetching
    pool = ThreadPool(4)
    results = pool.map(urllib2.urlopen, urls)
    pool.close()
    pool.join()

    if len(results) != len(urls):
        print "FETCH INCOMPLETE"
        sys.exit(1)

    print "*"*72
    # process each result page
    for i, pagesrc in enumerate(results):
        process_each_page(pagesrc, urls[i], userid)


# process each one
def process_each_page(pagesrc, eachurl, userid):
    # html = eachurl
    content = pagesrc
    soup = BeautifulSoup(content)
    org = soup.find_all(class_='photo_wrap')

    file = open('info.txt', 'aw')
    file.write('\n' + eachurl + '\n' + '-'*72 + '\n')

    uid_set = set()
    for photo in org:
        uid = re.findall(
            r'<a href="http://www.douban.com/people/(.*?)/">', str(photo))
        uid_set.add(uid[0])

    uid_list = list(uid_set)
    for uid in uid_list:
        file.write(str(uid) + '\n')

    if userid in uid_list:
        print eachurl

    file.close()

# get the total number of photos
def get_total(album_url):
    html = addslash(album_url)
    html = html + '?start=0&sortby=time'

    content = urllib2.urlopen(html, timeout=1000).read()
    soup = BeautifulSoup(content)

    org = soup.find(class_='count')
    count = 0
    count = re.findall(
        r'\d+', str(org))[0]

    return count

# get the album id
def get_album_id(online_url):
    html = online_url
    online_id = re.findall(
        r'\d+', str(online_url))
    if not online_id or len(online_id) != 1:
        print "URL error: %s" % online_url
        sys.exit(0)

    content = urllib2.urlopen(html, timeout=1000).read()
    soup = BeautifulSoup(content)
    org = soup.find("a", {"id" : "pho-num"})
    aid = re.findall(
        r'\d+', str(org))

    if online_id[0] in aid:
        return str(aid[aid.index(online_id[0]) + 1])
    else:
        print "ERROR"
        sys.exit(0)

# driver
def main():
    if len(sys.argv) != 3:
        print "Usage: online.py online_url userid"
        print "Output:"
        print "     - info.txt"
        print "     - page url if userid is found"
        print "Example: online.py http://www.douban.com/online/11567824/ 50980841"
        print
        sys.exit(0)
    else:
        file = open('info.txt', 'w')
        file.close()
        print "*"*72
        process(sys.argv[1], sys.argv[2])

if __name__ == '__main__':
    main()
