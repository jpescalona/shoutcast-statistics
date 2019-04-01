# Shoutcast Statistics Dashboard

This project was specifically designed to gather shoutcast statictics (listeners and radio show names mainly) of several radio stations.

It runs several docker containers and is componed by:
* InfluxDB to store radio stats
* Grafana to show dashboards with the results
* Monitor daemon, it triggers a cronjob every minute and executes one python script to get the statistics from the list of radio stations defined by the file /opt/monito/radios.yml. On the project you can find a file named servers-example.yml to start building your own list. For example:
```
---
beachgrooves: # this is the name of the radio (it will create the same tag value in influxdb)
  radio_name: "Beach Grooves Radio" # This is the label for the radio station
  servers: # A list of servers componed by: hostname/ip address, port and a label named origin. 
           # The usage of this origin label will help you to aggregate traffic 
           # from different sources served by different servers.
    - host: stream.beachgrooves.com
      port: 8000
      origin: web
    - host: stream.beachgrooves.com
      port: 8020
      origin: app
```

## Building the project

To build the project you need docker-compose: https://docs.docker.com/compose/install/

Then execute build, create to create services and start the containers:
```
docker-compose build 
docker-compose create
docker-compose start
```

## Proxy pass on nginx/haproxy

You can extend your docker-compose to add a new service to expose grafana using a nginx or haproxy. This is out of the scope and is a user's choice, but here is an example configuration snippet for nginx that you can use:
```
# MANAGED BY PUPPET
server {
  listen *:80;
  server_name           www.server.com;

  location /grafana/ {
    proxy_pass http://localhost:3000/;
  }
  
  access_log            /var/log/nginx/www.server.com.access.log combined;
  error_log             /var/log/nginx/www.server.com.error.log;

}
```
Official documentation of proxy_pass on grafana can be found on http://docs.grafana.org/installation/behind_proxy/
