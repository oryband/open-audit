.PHONY: default
.DEFAULT_GOAL: default


default: up

up:
	docker-compose up

down:
	docker-compose down -v

clean: down
	docker-compose down --rmi all
