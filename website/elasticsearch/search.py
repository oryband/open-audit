#!/usr/bin/env python

import fileinput
import json

from elasticsearch import Elasticsearch


INDEX_NAME = 'default'

def search(es, index, term):
    res = es.search(index=index, size=9999999, q=term)

    print(json.dumps(res))


if __name__ == '__main__':
    ES = Elasticsearch()
    with fileinput.input() as inp:
        search(ES, INDEX_NAME, ' '.join(inp))
