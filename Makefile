CONTAINER_NAME = jovial_keldysh

test: 
	pytest tests/ -vv -m "not zvec"

# use
docker-test: 
	docker exec -it $(CONTAINER_NAME) bash -c "cd /root/atlas && source .venv/bin/activate && pytest tests/ -vv && deactivate"