# main.py

# make an index
# start up haystack finder with that index
# start a qa server using that finder as a qa engine

from util import get_log, bannerfy
from make_index import make_default_index, BlogIndexConfig
from haystack_server import make_finder, run_server

if __name__ == '__main__':
    config = make_default_index()
    make_finder(config)
    run_server()

