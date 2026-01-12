# Build and deploy docker containers

###### Build docker images defined in docker-compose

```
docker-compose -f docker/docker-compose.yml build
```

###### Initialize docker swarm for containers that have networks defined as overlay

```
docker swarm init
```

###### Deploy all containers defined in docker-compose and detach from the process

```
docker-compose -f docker/docker-compose.yml up -d
```

###### Follow logs of the deployed docker container by id

```
docker logs -f [container-id]
```

###### Enter bash of the deployed docker container by id

```
docker exec -it [container-id] bash
```

###### Monitor docker containers and their resource usage

```
docker stats $(docker ps --filter "name=[container-name]" -q)
```

###### Stop all docker containers defined in docker-compose

```
docker-compose -f docker/docker-compose.yml down
```

###### Cleanup all docker data and volumes

```
docker system prune -a --force
```

```
docker system prune --volumes --force
```

```
docker system prune -a --volumes --force
```