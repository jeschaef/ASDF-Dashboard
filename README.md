<img align="left" width="80" height="80" src="https://github.com/jeschaef/ASDF-Dashboard/blob/f56f7876e7ecd49363bccd1b4048376e4854cc3d/app/static/logo.png" alt="Project app icon">

# ASDF-Dashboard

This web application provides a service for an automated subgroup 
fairness analysis of a binary classifier. Our system detects the 
subgroups in the data automatically by using either subgroups obtained
from clustering the dataset or entropy-based patterns derived from 
the found clusters.

Therefore, the ASDF-Dashboard provides an easy automatic computation
of the subgroups with the SLINK clustering algorithm. Alternatively,
a customizable fairness assessment supporting different, configurable
clustering algorithms is offered, too. The results of the automatic 
subgroup fairness analysis of the binary classifier are visualized 
in the dashboard. The interactive charts provide various perspectives
and deep insights into the classifier's behavior on the
detected subgroups.

We offer a [live demo](http://server1.dbda.cs.uni-frankfurt.de) of the ASDF-Dashboard 
service. The ASDF-Dashboard can also be self-hosted. The installation and deployment
instructions for the self-hosted setup are given below. 

For further information on the scientific details and the experimental
results see our paper [ADBIS '22 paper: Clustering-based Subgroup 
Detection for Automated Fairness Analysis](https://link.springer.com/chapter/10.1007/978-3-031-15743-1_5) (DOI: [10.1007/978-3-031-15743-1_5](https://doi.org/10.1007/978-3-031-15743-1_5)).

## Self-hosted setup

The easiest way to self host the application is to build and run 
the provided docker compose setup consisting of
- a nginx service providing the reverse proxy functionality,
- a celery worker service for the distribution of the background
tasks,
- a redis database service used for caching and as background 
task backend,
- a postgresql database service for user and dataset management,
- and the flask container hosting the ASDF-Dashboard service.


### Create .env file

Create a `.env`-file in the project's root folder with the following variables and replace the `<placeholders>` 
with actual values according to your environment ([template](.env-template) for the
`.env`-file).
```
# Mail
MAIL_SERVER=<url_smtp_server>
MAIL_PORT=<port_smtp_server>
MAIL_USERNAME=<user_smtp_server>
MAIL_PASSWORD=<password_smtp_server>
MAIL_USE_TLS=<flag_tls_smtp_server(True/False)>
MAIL_SENDER=<sender_email_address>

# General
COMPOSE_PROJECT_NAME=asdf-dashboard

# Docker
DOCKER_RESTART_POLICY=unless-stopped
DOCKER_STOP_GRACE_PERIOD=3s
DOCKER_WEB_PORT=8000
DOCKER_WEB_VOLUME=./instance:/app/instance

# Flask
FLASK_ENV=production

# Nginx
NGINX_PORT=<nginx_port>

# Gunicorn
WEB_RELOAD=<flag_web_reload(true/false)>
WEB_CONCURRENCY=<number_of_workers>

# Postgres
POSTGRES_DB=<db_postgres>
POSTGRES_USER=<user_postgres>
POSTGRES_PASSWORD=<password_postgres>
```

### Configure Nginx

Adapt the [nginx configuration template](app/conf/nginx/nginx-template.conf) to your 
environment. To this end, copy it into a file named `nginx.conf`, which is located at 
[the same folder](app/conf/nginx). The listening port and the server name have to be 
set according to your host/domain, that will be pointed to the web service, and the 
same value as the NGINX_PORT environment variable (in the `.env`-file).

```
...
server {
        listen {same_as_the_NGINX_PORT};
        server_name {your_domain_name};
        ...
}
...
```

If you want to set a different user disk quota, you have to set the `MAX_QUOTA_MB` 
environment variable in the `.env`-file and configure limit for the client body size
(`client_max_body_size`) in the nginx configuration, e.g.,
```
...
http {
    client_max_body_size 15M;
    ...
}
```

The number of worker processes (`worker_processes`) can also be 
increased. It is not recommended to change other values from the
[nginx configuration template](app/conf/nginx/nginx-template.conf).

### Update footer

Update the [`footer.html`](app/templates/footer.html) accordingly to tell the
users who is hosting this dashboard.


### Production setup

Build and run the docker container setup with

`docker-compose up --build`

After the successful build and start of the containers, the web service of the 
ASDF-Dashboard should be available via a web browser under 
http://yourdomain:{nginx_port} as configured in the `.env`-file, 
e.g., under http://example.com:80/. This information is required for
the ASDF-Dashboard application when sending out account confirmation
emails containing confirmation links to the registered users.


### Development setup

For a development setup it is sufficient to have a
1. a local redis instance (e.g., in a docker container as shown below),
2. a celery worker instance,
3. and the ASDF-Dashboard Flask application.

Note: The development setup should not be used in a production 
environment for security reasons.

#### Install requirements

Install the required python packages with

`pip install -r requirements.txt`

#### Redis docker setup

First pull the redis docker image

`docker pull redis`

and then run it in a container

`docker run --name redis -p 6379:6379 -d redis`

#### Celery worker

From the project root execute

`celery -A app.celery_app worker -l info`

Note: The command line parameter `-P` has to be set to `solo` on windows machines.

`celery -A app.celery_app worker -P solo -l in`

#### Flask Application

The flask application for the development/debug setup is started by executing
the following command:

`python app/__init__.py`

