#!/usr/bin/env python
import time
import requests
import yaml
import re
from influxdb import InfluxDBClient
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError

def load_servers():
    with open("/opt/monitor/servers.yaml", 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)    
            exit(1)

list_of_servers = load_servers()
measurements = []

for server_name, server_info in list_of_servers.iteritems():
    while True:
        url = '{protocol}://{server_host}:{server_port}/{server_path}'.format(
            protocol='https' if server_info.get('secure') else 'http',
            server_host=server_info.get('server'),
            server_port=server_info.get('port'),
            server_path=server_info.get('path', 'index.html?sid=1')
        )
        try:
            r = requests.get(url)
            if r.status_code == requests.codes.ok:
                soup = BeautifulSoup(r.content, "html.parser")
                text = soup.find("td", text="Stream Status: ").find_next_sibling("td").text
                shoutcast_info = re.match("Stream is (?P<up>up).*\((?P<unique>\d+) unique\)", text)
                if shoutcast_info:
                    measurements.append({
                        "measurement": "radio_status",
                        "tags": {
                            "radio_name": server_name
                        },
                        "fields": {
                            "value": 1 if shoutcast_info.group(1) else 0
                        }
                    })
                    measurements.append({
                        "measurement": "radio_listeners",
                        "tags": {
                            "radio_name": server_name
                        },
                        "fields": {
                            "value": shoutcast_info.group(2)
                        }
                    })
                break
        except ConnectionError:
            pass
        except Exception as e:
            print e
        finally:
            time.sleep(0.5)

# PUSH the stats
client = InfluxDBClient('influxdb', 8086, 'shoutcast', 'shoutcast', '1shoutcast!')
client.write_points(measurements) 
