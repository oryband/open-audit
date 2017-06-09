.PHONY: default
.DEFAULT_GOAL: default


default: load-data

load-data: elasticsearch dynamic-template
	docker run \
		--rm -it \
		-v $$PWD:/code \
		-v $$PWD/../scraper/output:/data \
		--network host \
		python:3-alpine \
		sh -c "pip install -r /code/requirements.txt && /code/insert.py /data"

dynamic-template:
	curl -sSXPUT localhost:9200/_template/default?pretty --data @template.json

elasticsearch: elasticsearch-init elasticsearch-down
	docker-compose -f elk-hebmorph-docker/docker-compose.yml up -d
	until $$(curl -sfo /dev/null localhost:9200); do sleep 1; done
elasticsearch-down:
	docker-compose -f elk-hebmorph-docker/docker-compose.yml down -v
elasticsearch-init:
	if [ ! -d elk-hebmorph-docker ]; then git clone https://github.com/oryband/elk-hebmorph-docker.git; fi

clean: elasticsearch-down
	rm -rf elk-hebmorph-docker
