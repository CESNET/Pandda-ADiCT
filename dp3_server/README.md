# ADiCT-lite server

This directory contains the server-side code for the ADiCT-lite project. 
The server has an API for receiving and processing data from the collector modules, and for serving the processed data to users.

## Installation 
Use the supplied `requirements.txt` file, either on your global python instance, or inside your selected virtual environment.

```shell
pip install -r requirements.txt
```

ADiCT is built on top of the [DP³ platform](https://github.com/CESNET/dp3).

## Dependencies

In order to run the server, the following services must be set up and running:
- RabbitMQ
- MongoDB
- Redis

For a local development setup, you can use the provided `docker-compose.yml` file to start these services.
  
```shell
docker-compose up -d
```

Then, you can start the workers with the following command. Be sure to start all the workers you've configured in the `config` directory:

```shell
dp3 worker adict <path to this directory>/config <worker index> -v
```

The API can be similarly started with the following command:

```shell
APP_NAME=adict CONF_DIR=<path to this directory>/config dp3 api
```