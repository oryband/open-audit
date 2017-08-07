#!/usr/bin/env python

from flask import (Flask,
                   g,
                   request,
                   render_template,
                   jsonify)

from elasticsearch import Elasticsearch


app = Flask(__name__)


app.config.update({
    'DEBUG': True,
    'JSON_AS_ASCII': False,

    'ELASTICSEARCH_HOST': 'elasticsearch',
    'ELASTICSEARCH_PORT': 9200,
    'ELASTICSEARCH_DEFAULT_INDEX': 'default',
    'ELASTICSEARCH_SEARCH_RESULT_SIZE': 99999,
})


def get_es():
    """Get or create Elasticsearch connection."""
    try:
        return g._elasticsearch
    except AttributeError:
        es = g._elasticsearch = Elasticsearch(hosts=[{'host': app.config['ELASTICSEARCH_HOST'],
                                                      'port': app.config['ELASTICSEARCH_PORT']}])
        return es


@app.route('/')
@app.route('/index.html')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    """Search given term in Elasticsearch and return JSON result."""
    # search elasticsearch for given term
    res = get_es().search(
        index=app.config['ELASTICSEARCH_DEFAULT_INDEX'],
        size=app.config['ELASTICSEARCH_SEARCH_RESULT_SIZE'],
        q=request.json['term'],
    )

    # build response body
    hits = {
        'status': 'ok',
        # elasticsearch results contain plenty of unimportant fields,
        # keep only '_type' and '_source'
        'results': [{'type': s['_type'], 'source': s['_source']}
                    for s in res['hits']['hits']],
    }

    return jsonify(hits)
