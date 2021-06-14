# Docker cheatsheet

###### Build docker images defined in docker-compose

[comment]: <> (docker-compose -f docker/multi/docker-compose.yml build  )
docker-compose -f docker/single/docker-compose.yml build

###### Initialize docker swarm for containers that have networks defined as overlay

docker swarm init

###### Deploy all containers defined in docker-compose and detach from the process

[comment]: <> (docker-compose -f docker/multi/docker-compose.yml up -d  )
docker-compose -f docker/single/docker-compose.yml up -d

###### Enter deployed docker container by id

docker exec -it <container-id> bash

###### Stop all docker containers defined in docker-compose

[comment]: <> (docker-compose -f docker/multi/docker-compose.yml down  )
docker-compose -f docker/single/docker-compose.yml down

###### Cleanup all docker elements and volumes

docker system prune -a --volumes