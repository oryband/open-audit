#!/bin/sh
# Show given index properties.

set -x

ADDRESS=${2:-"localhost:9200"}
PROPERTIES=${3:-"_settings,_mapping,_warmers,_aliases"}

curl -sSXGET $ADDRESS/$1/$PROPERTIES?pretty
