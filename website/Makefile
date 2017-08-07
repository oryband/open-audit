.DEFAULT_GOAL: default
default: up
.PHONY: default

up: elasticsearch
	docker-compose up flask
.PHONY: up

elasticsearch: elasticsearch-init
	docker-compose up -d elasticsearch kibana
	until $$(curl -sfo /dev/null localhost:9200); do sleep 1; done
.PHONY: elasticsearch

elasticsearch-load-data: elasticsearchelasticsearch-dynamic-template
	docker-compose run load-elasticsearch-data
.PHONY: elasticsearch-load-data

elasticsearch-dynamic-template: elasticsearch
	curl -sSXPUT localhost:9200/_template/default?pretty --data @elasticsearch/template.json
.PHONY: elasticsearch-dynamic-template

elasticsearch-init:
	if [ ! -d elasticsearch/elk-hebmorph-docker ]; then \
		git clone https://github.com/oryband/elk-hebmorph-docker.git elasticsearch/elk-hebmorph-docker; \
	fi
.PHONY: elasticsearch-init

down:
	docker-compose down -v
.PHONY: down

clean: down
	docker-compose down --rmi all
	rm -rf elasticsearch/elk-hebmorph-docker
.PHONY: clean
