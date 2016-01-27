import urllib2
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool

urls = [
    'http://www.douban.com/online/11567824/',
    'http://google.com'
]

# Make the Pool of workers
pool = ThreadPool(4)
# Open the urls in their own threads
# and return the results
results = pool.map(urllib2.urlopen, urls)

for page in results:
    soup = BeautifulSoup(page)
    print soup

print results
#close the pool and wait for the work to finish
pool.close()
pool.join()
