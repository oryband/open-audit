#!/bin/sh
ADDRESS=${2:-"localhost:9200"}
curl -sSX DELETE $ADDRESS/$1?pretty
