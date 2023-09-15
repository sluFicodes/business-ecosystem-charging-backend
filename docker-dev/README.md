# Business API Ecosystem Charging Backend Dev Docker

This directory includes a *Dockerfile* and a *docker-compose.yml* files that enable using a completely configured Ubuntu 20.04
machine, with all the software dependencies installed, for developing stuff over the business-ecosystem-charging-backend
software.

The first step for using this container is building it, you can do that with the following command:

```
docker build -t charging-dev .
```

Then, you can run the container as well as another one containing MongoDB using the following command:

```
docker compose up
```

You can stop the containers with the following command:

```
docker compose stop
```

And start them again with:

```
docker compose start
```

Moreover, you can terminate the containers with:

```
docker compose down
```

The provided *docker-compose.yml* file is creating a volume called *charging-data* which includes all the saved information
in MongoDB, so you can persist it or used it as a backup.

In addition, the docker-compose is going to create a volume over the *src* folder of the sources, so you can modify,
test or execute the software inside the container. To access to the container execute the following command:

```
docker exec -ti dockerdev_charging_1 /bin/bash
```
