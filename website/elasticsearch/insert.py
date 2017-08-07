#!/usr/bin/env python

import json
import sys
import os.path

from elasticsearch import Elasticsearch


INDEX_NAME = 'default'


def prefaces(es, index_name, dir_path):
    with open(os.path.join(dir_path, 'prefaces.json'), 'r') as f:
        for line in f:
            preface = json.loads(line)

            offices_to_defects = preface['offices_to_defects'].items()
            del preface['offices_to_defects']
            for office, defects in offices_to_defects:
                es.create(index_name, doc_type='preface_office',
                         body={
                             'report_id': preface['id'],
                             'office': office,
                             'defects': defects,
                         })

            keywords_to_defects = preface['keywords_to_defects'].items()
            del preface['keywords_to_defects']
            for keyword, defects in keywords_to_defects:
                es.create(index_name, doc_type='preface_keyword',
                         body={
                             'report_id': preface['id'],
                             'keyword': keyword,
                             'defects': defects,
                         })

            es.create(index_name, doc_type='preface', body=preface)

def chapters(es, index_name, dir_path):
    with open(os.path.join(dir_path, 'chapters.json'), 'r') as f:
        for line in f:
            chapter = json.loads(line)

            offices = chapter['offices']
            del chapter['offices']
            for office in offices:
                es.create(index_name, doc_type='chapter_office',
                         body={
                             'report_id': chapter['id'],
                             'office': office,
                         })

            keywords = chapter['keywords']
            del chapter['keywords']
            for keyword in keywords:
                es.create(index_name, doc_type='chapter_keyword',
                         body={
                             'report_id': chapter['id'],
                             'keyword': keyword,
                         })

            es.create(index_name, doc_type='chapter', body=chapter)

def topics(es, index_name, dir_path):
    with open(os.path.join(dir_path, 'topics.json'), 'r') as f:
        for line in f:
            topic = json.loads(line)

            es.create(index_name, doc_type='topic', body=topic)

if __name__ == '__main__':
    es = Elasticsearch()
    print('loading prefaces...')
    prefaces(es, INDEX_NAME, sys.argv[1])
    print('loading chapters...')
    chapters(es, INDEX_NAME, sys.argv[1])
    print('loading topics...')
    topics(es, INDEX_NAME, sys.argv[1])
