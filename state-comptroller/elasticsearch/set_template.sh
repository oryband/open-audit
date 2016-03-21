#!/bin/sh
ADDRESS=${2:-"localhost:9200"}
curl -sSXPUT $ADDRESS/_template/$(basename $1 .json)?pretty --data @$1
