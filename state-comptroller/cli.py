#!/usr/bin/env python
"""cli helper tool for 66a report."""
import json
import os
import os.path

import click
import elasticsearch as es
import yaml


@click.group()
def cli(): pass


@cli.command(
    short_help='read yaml objects and convert to json ',
    help=('read all yaml files in given directory '
          'and print a single merged json object'))
@click.argument('root', type=click.Path(exists=True), default='.')
@click.option('-v', '--verbose', is_flag=True)
def yaml_to_json(root, verbose):
    data = {}
    for chapter in os.listdir(root):
        if os.path.isdir(os.path.join(root, chapter)):
            data[chapter] = {}  # directory name is the chapter name

            # load chapter meta
            path = os.path.join(root, chapter, 'meta.yml')
            if verbose:
                click.echo(path)
            with open(path, 'r') as f:
                meta = yaml.load(f)
                data[chapter]['meta'] = meta

            # load chapter topics
            data[chapter]['topics'] = []
            for file in os.listdir(os.path.join(root, chapter)):
                if file == 'meta.yml':
                    continue
                path = os.path.join(root, chapter, file)
                if verbose:
                    click.echo(path)
                with open(path, 'r') as f:
                    topic = yaml.load(f)
                    data[chapter]['topics'].append(topic)

    click.echo(json.dumps(data, ensure_ascii=False).encode('utf-8'))


@cli.command(help='read json and insert to elasticsearch')
@click.argument('path', type=click.Path(exists=True), default='./66a.json')
@click.argument('address', default='localhost:9200')
@click.option('-v', '--verbose', is_flag=True)
def json_to_elasticsearch(path, address, verbose):
    if verbose:
        click.echo('connecting to %s' % address)
    conn = es.Elasticsearch([address])

    if verbose:
        click.echo('reading %s' % path)
    with open(path, 'r') as f:
        def gen_doc(chapter_name, topic, obj):
            """return document to insert to elasticsearch.

            uses given chapter, topic, and defect/amendment (obj)
            """
            doc = {k: topic[k] for k in
                   ['title', 'docx', 'pdf']}
            doc['sub_type'] = topic['type']
            doc['keywords'] = chapter['meta']['keywords']
            doc.update({
                'chapter': chapter_name
            })

            try:
                doc['body'] = topic['sub_type']
            except KeyError:
                pass

            try:
                doc['description'] = obj['description']
            except KeyError:
                pass

            try:
                doc['clauses'] = '\n\n'.join(obj['clauses'])
            except KeyError:
                pass

            return doc

        data = yaml.load(f)
        for chapter_name, chapter in data.items():
            for i, topic in enumerate(chapter['topics'], start=1):
                for j, defect in enumerate(topic['defects'], start=1):
                    if verbose:
                        click.echo('indexing %s/topic_%d/defect_%d'
                                   % (chapter_name, i, j))
                    conn.index(index='66a',
                               doc_type='defect',
                               body=gen_doc(chapter_name, topic, defect))

                for j, amendment in enumerate(topic['amendments'], start=1):
                    if verbose:
                        click.echo('indexing %s/topic_%d/amendments_%d'
                                   % (chapter_name, i, j))
                    conn.index(index='66a',
                               doc_type='amendment',
                               body=gen_doc(chapter_name, topic, amendment))


if __name__ == '__main__':
    cli()
