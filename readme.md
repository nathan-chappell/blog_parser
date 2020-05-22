# Mono Site parser/ indexer/ haystack-qa webserver

The purpose of this software is three-fold:

* parse data from a dump of mono-software.com
* use ElasticSearch to create an index of the site
* use haystack to answer questions using the index
* provide a simple web-server as a frontend to haystack

## Installation

Linux:

> ./install.sh

Windows:

> powershell install.ps1

## Usage

To use the program, an instance of ElasticSearch (a node) must be running.
To run one as a daemon (background service), try:

> elasticsearch/bin/elasticsearch -d

Everything set up for ES to run on __localhost:9200__, so if you want
something different you'll have to set it up yourself.
