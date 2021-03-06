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

#
# globals, I am gonna get rid of them
#
POOL_SIZE = 8

# some print utils, move to a new file in the future
def printerr(msg):
    print "%-8s:  %s\n" % ('ERROR', msg)

def printwarn(msg):
    print "%-8s:  %s\n" % ('WARNING', msg)

def printfail(msg):
    print "%-8s:  %s\n" % ('FAIL', msg)

def printinfo(msg, info='INFO'):
    print "%-8s:  %s\n" % (info, msg)

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
def check_options(args):
    userid = vars(args).get('user')
    online_id = vars(args).get('online')

    if not userid and not online_id:
        return False

    return True

def get_options_parser():
    aut_parser = argparse.ArgumentParser(
        description="douban online analyzer: 1.0",
        epilog="example: python online.py -user 53907177 -online 122845047",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        add_help=False
    )

    # required group
    req_args = aut_parser.add_argument_group('required arguments')

    # optional group
    opt_args = aut_parser.add_argument_group('optional arguments')

    opt_args.add_argument(
        '-user',
        help="""douban user id (not nickname)
                If no user id specified, will search the top #
                images of the given online id.

                (user id and online id, at least one of them
                 must be present on the command line)
             """,
        #required=True,
        default=argparse.SUPPRESS
    )
    opt_args.add_argument(
        '-online',
        help="""douban online activity id (11567824)
                http://www.douban.com/online/11567824

                If no online id specified, will search all the
                online activities' images.
             """,
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
        choices=[10, 20, 50, 100]
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

def process(online_id, userid, save):
    online_url = 'http://www.douban.com/online/' + online_id + '/'
    album_url = online_url + 'album/' + get_album_id(online_id)

    total = int(get_total(album_url))
    if total == 0:
        return

    # 90 is douban's default
    urls = []
    for page in range(0, total, 90):
        pid = str(page)
        appstr = '?start=%s&sortby=time' % pid
        phtml = addslash(album_url) + appstr
        urls.append(phtml)

    # parallel fetching
    pool = ThreadPool(POOL_SIZE)
    results = pool.map(urllib2.urlopen, urls)
    pool.close()
    pool.join()

    if len(results) != len(urls):
        print "FETCH INCOMPLETE"
        sys.exit(1)

    # parse each result page but will process them all together later
    org_all = []
    for i, pagesrc in enumerate(results):
        #print "Processing page " + str(i)
        soup = BeautifulSoup(pagesrc, "html.parser")
        org = soup.find_all(class_='photo_wrap')
        org_all += org

    process_all(online_id, org_all, userid, save)

# process each one
def process_all(online_id, org, userid, save):
    filename = get_json_path(online_id)
    #file = open(filename, 'aw')
    # file.write('\n' + eachurl + '\n' + '-'*72 + '\n')

    uid_set = set()
    download = []

    #
    # first step, get all the objects
    #

    # entire js file
    json_obj = {}
    # all the info for a user
    user_obj = {}
    # all the online photo page url and # of comments
    imgonline_info = []
    # total number of comments
    total_comments = 0
    max_ncomment = 0

    # each processing block is a photo
    # also update the js block here
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
        photoid = str( re.findall(r'p\d+', imgurl)[0] )
        photoid = str( re.findall(r'\d+', photoid)[0] )
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

            #
            # OK, I am applying restrictions here, because
            # the total number of images can be 1000+ and it
            # won't be a good idea to request all these pages.
            #
            # So, two rules:
            #   - set up a threshold to fetch or not (cont'd)
            #   - if yes, only when ncomment > avg(ncomments)
            #
            ncomm = int(ncomment[0])
            if ncomm > max_ncomment:
                max_ncomment = ncomm
            if ncomm > 0:
                imgourl = 'http://www.douban.com/online/' + \
                          online_id + '/photo/' + photoid
                imgonline_info.append( (imgourl,ncomm) )

                total_comments += ncomm
        else:
            photo_obj['comments'] = str(ncomment)

        # add an entry into the json file with photoid
        json_obj[photoid] = photo_obj
        photo_obj = {}

        # save it for downloading?
        photo_obj['save'] = 0
        if save:
            photo_obj['save'] = 1

        # write the record
        #file.write(str(uid[0]) + ' '*2 + imgurl + '\n')

        # note here it's a tuple
        download.append( (imgurl, online_id) )

        if userid == str(uid[0]):
            # download and save the image
            # print imgurl
            pass

        # end of for

    # decide the image pages that we are gonna fetch
    avg_comment = int ( total_comments / len(imgonline_info) )
    thres_comment = int ( (max_ncomment - avg_comment) / 2 )
    imgonline_url = []

    print '\n  Average Comments: %s' %  repr(avg_comment)
    print 'Threshold Comments: %s' %  repr(thres_comment)

    printbar()
    for image in imgonline_info:
        if (image[1] > thres_comment):
            imgonline_url.append(image[0])

            print image[0] + '  ... #' + str(image[1])
    printbar()
    print '\nTotal Pages: %s' % repr(len(imgonline_url))

    #
    # second part, process each photos online page
    # imgonlineurl
    #
    '''
    pool = ThreadPool(POOL_SIZE)
    results = pool.map(urllib2.urlopen, imgonline_url)
    pool.close()
    pool.join()

    if len(results) != len(imgonline_url):
        print "FETCH photo page INCOMPLETE"
        sys.exit(1)
    '''

    #
    # download the images if -save is present
    #
    '''
    pool = ThreadPool(POOL_SIZE)
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
    # userid or online_id must be present one of them
    if len(sys.argv) < 3:
        parser.print_help()
        report_and_exit(-1)

    args = parser.parse_args()
    if not check_options(args):
        printerr ('you need to specify -userid or -onlineid')
        parser.print_help()
        report_and_exit(-1)

    userid = vars(args).get('user')
    online_id = vars(args).get('online')
    update = vars(args).get('update')
    save = vars(args).get('save')
    top = vars(args).get('top')

    # be nice
    print_user_name(userid)

    filepath = get_json_path(online_id)
    if update or not is_json_exist(online_id):
        # touch the file
        file = open(filepath, 'w')
        file.close()
        process(online_id, userid, save)

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
