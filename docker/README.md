# Docker cheatsheet

###### Build docker images defined in docker-compose

docker-compose -f docker/single/docker-compose.yml build

###### Initialize docker swarm for containers that have networks defined as overlay

docker swarm init

###### Deploy all containers defined in docker-compose and detach from the process

docker-compose -f docker/single/docker-compose.yml up -d

###### Follow logs of deployed docker container by id

docker logs -f [container-id]

###### Enter bash of deployed docker container by id

docker exec -it [container-id] bash

###### Stop all docker containers defined in docker-compose

docker-compose -f docker/single/docker-compose.yml down

###### Cleanup all docker data and volumes

docker system prune -a  
docker system prune --volumes  
docker system prune -a --volumes