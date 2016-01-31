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
import urllib
import urllib2
import re
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import cpu_count
import time
import os
import posixpath
import argparse
import json
import collections

# some print utils, move to a new file in the future
def printerr(msg):
    print "%8s:  %s" % ('ERROR', msg)

def printwarn(msg):
    print "%8s:  %s" % ('WARNING', msg)

def printfail(msg):
    print "%8s:  %s" % ('FAIL', msg)

def printinfo(msg, info='INFO'):
    print "%8s:  %s" % (info, msg)

def printbar():
    print '*' * 72

def report_and_exit(num):
    #printbar()
    sys.exit(num)

#
# json related utils
#
"""
json file structure
{
  online_info : {
    urls : ['http://url_0',
            'http://url_1',
            ...
           ]
    processed_urls : ['http://url_0',
                      'http://url_6',
                      ...
                     ]
  }

  page_0: {
    url : 'http://url_0'
    user_list: [ '12345678', '23456789', '34567890' ... ]
    user_0 : {}
  }
  ...
  page_40: {
    url : 'http://url_40'
    user_list: [ '12345678', '23423659', '97565690' ... ]
  }
}
"""
def get_json_path(online_id):
    wkdir = get_wkdir(online_id)
    filename = 'online-' + online_id + '.js'
    filepath = posixpath.join(wkdir, filename)
    return filepath

# True: exists and not size 0
def is_non_zero_file(fpath):
    return True if os.path.isfile(fpath) and \
        os.path.getsize(fpath) > 0 \
        else False

def is_json_exist(online_id):
    filename = get_json_path(online_id)
    return is_non_zero_file(filename)

def json_test(fpath, userid, top):
    with open(fpath, 'r') as f:
        json_obj = json.load(f)

    unsorted_list = []
    for photo in json_obj.keys():
        user_id = json_obj[photo]['userid']
        photo_url = json_obj[photo]['url']
        photo_id = json_obj[photo]['id']
        num_comments = json_obj[photo]['comments']

        if userid == user_id:
            print photo_url

        unsorted_list.append( (photo_id, int(num_comments)) )

    sorted_list = sorted(unsorted_list, key=lambda x:x[1], reverse=True)

    # get top #
    ntop = top
    if len(sorted_list) <= top:
        top_list = sorted_list
        ntop = len(sorted_list)
    else:
        top_list = sorted_list[:ntop]

    print
    printbar()
    print "TOP %s" % repr(ntop)
    printbar()

    for each in top_list:
        print json_obj[each[0]]['url'] + '   #' + json_obj[each[0]]['comments']


# args
def get_options_parser():
    aut_parser = argparse.ArgumentParser(
        description='Douban Online Analyzer: 1.0',
        epilog="Example: python online.py -user 53907177 -online 122845047",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False
    )

    # required group
    req_args = aut_parser.add_argument_group('required arguments')

    # optional group
    opt_args = aut_parser.add_argument_group('optional arguments')

    req_args.add_argument(
        '-user',
        help='douban user id (not nickname)',
        required=True,
        default=argparse.SUPPRESS
    )
    req_args.add_argument(
        '-online',
        help="""douban online activity id (11567824)
                http://www.douban.com/online/11567824
             """,
        required=True,
        default=argparse.SUPPRESS
    )
    opt_args.add_argument(
        '-h',
        action="help",
        help='show this help message and exit'
    )
    opt_args.add_argument(
        '-top',
        help='Top # images based on comments',
        type=int,
        default=10,
        choices=[10, 20, 30, 50, 60, 100]
    )
    opt_args.add_argument(
        '-save',
        help='save the images',
        action='store_true',
        default=argparse.SUPPRESS
    )
    opt_args.add_argument(
        '-update',
        help='update the list and files',
        action='store_true',
        default=argparse.SUPPRESS
    )

    return aut_parser


# some libs
def addslash(url):
    if not url.endswith('/'):
        return url + '/'
    else:
        return url

def retrieve_one_img(imgurl, online_id):
    imagename = str( re.findall('p\d+', imgurl)[0] ) + '.jpg'
    imagepath = posixpath.join(get_imgdir(online_id), imagename)
    return urllib.urlretrieve(imgurl, imagepath)

def retrieve_wrapper(args):
    return retrieve_one_img(*args)

def process(online_id, userid):
    online_url = 'http://www.douban.com/online/' + online_id + '/'
    album_url = online_url + 'album/' + get_album_id(online_id)

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

    # parse each result page but will process them all later
    org_all = []
    for i, pagesrc in enumerate(results):
        #print "Processing page " + str(i)
        soup = BeautifulSoup(pagesrc, "html.parser")
        org = soup.find_all(class_='photo_wrap')
        org_all += org

    process_all(online_id, org_all, userid)

# process each one
def process_all(online_id, org, userid):
    # html = eachurl
    # content = pagesrc

    filename = get_json_path(online_id)
    #file = open(filename, 'aw')
    # file.write('\n' + eachurl + '\n' + '-'*72 + '\n')

    uid_set = set()
    download = []

    # entire js file
    json_obj = {}
    # all the info for a user
    user_obj = {}

    # each processing block is a photo
    photo_obj = {}
    for i, photo in enumerate(org):
        # find img link
        urls = re.findall(
            r'src=\"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\"', \
            str(photo))
        imgurl = re.findall(
            r'"([^"]*)"', str(urls[0]))
        imgurl = str(imgurl[0]).replace("thumb", "photo")

        # update photo_obj with photoid
        photoid = str( re.findall('p\d+', imgurl)[0] )
        photo_obj['id'] = photoid

        # update photo_obj with imgurl
        photo_obj['url'] = imgurl

        # find user id and update photo_obj
        uid = re.findall(
            r'<a href="http://www.douban.com/people/(.*?)/">', str(photo))
        uid_set.add(uid[0])
        photo_obj['userid'] = uid[0]

        # find the comments number and update photo_obj
        comment = re.findall(
            r'#comments\">(.*?)</a>', str(photo))
        comment_str = u''.join(comment).encode('utf-8')
        ncomment = 0
        if comment:
            ncomment = re.findall(
                r'\d+', comment_str)
            photo_obj['comments'] = str(ncomment[0])
        else:
            photo_obj['comments'] = str(ncomment)

        # add an entry into the json file with photoid
        json_obj[photoid] = photo_obj
        photo_obj = {}

        # write the record
        #file.write(str(uid[0]) + ' '*2 + imgurl + '\n')

        # note here it's a tuple
        download.append( (imgurl, online_id) )

        if userid == str(uid[0]):
            # download and save the image
            # print imgurl
            pass

    '''
    pool = ThreadPool(4)
    results = pool.map(retrieve_wrapper, download)
    pool.close()
    pool.join()

    if len(results) != len(download):
        print "RETRIEVE INCOMPLETE"
        sys.exit(1)
    '''

    with open(filename, 'w') as f:
        json.dump(json_obj, f)

    f.close()

# get the total number of photos
def get_total(album_url):
    html = addslash(album_url)
    html = html + '?start=0&sortby=time'
    soup = get_single_page(html)

    org = soup.find(class_='count')
    count = 0
    count = re.findall(
        r'\d+', str(org))[0]

    return count

# get the album id
def get_album_id(online_id):
    online_url = 'http://www.douban.com/online/' + online_id + '/'
    html = online_url
    soup = get_single_page(html)
    org = soup.find("a", {"id" : "pho-num"})
    aid = re.findall(
        r'\d+', str(org))

    if online_id in aid:
        return str(aid[aid.index(online_id) + 1])
    else:
        print "ERROR"
        sys.exit(0)

# get online activity id through user's input
def get_online_id(online_url):
    online_id = re.findall(
        r'\d+', str(online_url))
    if not online_id or len(online_id) != 1:
        print "URL error: %s" % online_url
        sys.exit(0)

    return str(online_id[0])

# get single page content after bs4
def get_single_page(html):
    try:
        hdr = {'User-Agent': 'Mozilla/5.0'}
        req = urllib2.Request(html, headers=hdr)
        content = urllib2.urlopen(req, timeout=1000).read()
        soup = BeautifulSoup(content, "html.parser")
    except Exception, e:
        print "\nRequest Error: %s" % e
        sys.exit(0)

    return soup

def print_user_name(userid):
    html = 'http://www.douban.com/people/' + userid
    soup = get_single_page(html)
    node = soup.findAll('title')[0]
    name = u''.join(node.findAll(text=True)).encode('utf-8').strip('\n')

    # you may do not have access to user's main page
    if name == u'\u767B\u5F55\u8C46\u74E3':
        print html + '\n'
    else:
        print name + ' '*2 + html + '\n'

def get_wkdir(online_id):
    wkdir = posixpath.join(os.getcwd(), 'online-' + online_id)
    if not os.path.exists(wkdir):
        os.makedirs(wkdir)
    return wkdir

def get_imgdir(online_id):
    imgdir = posixpath.join(get_wkdir(online_id), 'images')
    if not os.path.exists(imgdir):
        os.makedirs(imgdir)
    return imgdir

# driver
def main():
    parser = get_options_parser()
    if len(sys.argv) < 2:
        parser.print_help()
        report_and_exit(-1)

    args = parser.parse_args()
    userid = vars(args).get('user')
    online_id = vars(args).get('online')
    update = vars(args).get('update')
    save = vars(args).get('save')
    top = vars(args).get('top')

    # be nice
    #print_user_name(userid)

    filepath = get_json_path(online_id)
    if update:
        # touch the file
        file = open(filepath, 'w')
        file.close()
        process(online_id, userid)

    # if not update, directly check
    if is_json_exist(online_id):
        json_test(filepath, userid, top)

    if save:
        print "\nImages are saved in %s" % get_wkdir(online_id)

if __name__ == '__main__':
    print
    start = time.time()
    main()
    end = time.time()
    print "\nElapsed time: %s seconds" % str(end-start)
