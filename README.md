# Evidence of the work done

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

This folders includes all the files we made or use for the project completion.

Date: 26/01/2020

Authors: Mikele Zurutuza, Ivan Valdes, Alex Tesouro and Xabier Etxezarreta.

## Machine Learning Data Analysis files *(/popbl_data_analysis)*

- **data/**: Packetbeat and Metricbeat collected data in csv format.
- **clustering-metricbeat.ipynb**: Metricbeat data processing, DBSCAN model generation and validation.
- **clustering-packetbeat.ipynb**: Packetbeat data processing, DBSCAN model generation and validation.


## Deployment Scripts *(/popbl_deployment_scripts)*

- **CloudFormationDeployer.yml**: CloudFormation script wich deploys the infrastructure, provides the machines and launches the services-
- **awslogs.conf**: AwsLogs config file.
- **deploy.sh**: Parametrized deployment script.
- **simule_traffic.py**: Python script that simulates a normal use of our application.


## Elastic Stack, Beats and Honeypots deployment files *(/popbl_elkstack_honeypots)*

- **sb-honey/**: Honeypots (Cowrie and Dionaea), Packetbeat and Metricbeat deployment files.
- **sb-ml/**: Elastic Stack (Elasticsearch and Kibana) deployment files.
- **sb-sniffer/**: Packetbeat and Metricbeat deployment files for Microservices monitoring.


## Microservices Application *(/popbl_servicesapp)*

- **cert_haproxy/**: Rabbitmq Certs
- **cert_rabbitmq/**: Rabbitmq Certs
- **flask_app/**: Folder with all microservices implementations.
- **haproxy/**: Contains haproxy image and configuration file.


## Vault Files *(/popbl_vault)*

- **vault.sh**: Parametrized script that allows getting secrets from the vault and storing them into env vars or wiriting them into files.
- **vault/docker-compose.yml**: Vault docker-compose.


## Kibana and Plotly dashboard files*(/popbl_visualization)*

- **kibana-dashboard/**: Kibana dashboard export file.
- **plotly-dashboard/**: Plotly dashboard files.
