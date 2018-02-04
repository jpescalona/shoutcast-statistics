#!/usr/bin/env python
import time
import requests
import yaml
import re
from influxdb import InfluxDBClient
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
from datetime import datetime

def load_servers():
    with open("/opt/monitor/servers.yaml", 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)    
            exit(1)

list_of_servers = load_servers()
measurements = []
current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

for server_name, server_info in list_of_servers.iteritems():
    while True:
        url_current_users = '{protocol}://{server_host}:{server_port}/{server_path}'.format(
            protocol='https' if server_info.get('secure') else 'http',
            server_host=server_info.get('server'),
            server_port=server_info.get('port'),
            server_path=server_info.get('path', 'index.html?sid=1')
        )
        url_current_song = '{protocol}://{server_host}:{server_port}/{server_path}'.format(
            protocol='https' if server_info.get('secure') else 'http',
            server_host=server_info.get('server'),
            server_port=server_info.get('port'),
            server_path=server_info.get('current_song', 'currentsong?sid=1')
        )

        try:
            r = requests.get(url_current_users)
            if r.status_code == requests.codes.ok:
                soup = BeautifulSoup(r.content, "html.parser")
                text = soup.find("td", text="Stream Status: ").find_next_sibling("td").text
                radio_name = server_info.get('radio_name', server_name)
                current_song_r = requests.get(url_current_song)
                shoutcast_info = re.match("Stream is (?P<up>up).* with (?P<users>\d+) of.*", text)
                if shoutcast_info:
                    measurements.append({
                        "measurement": "radio_status",
                        "tags": {
                            "radio_name": radio_name,
                            "origin": server_info.get('origin'),
                            "server_name": server_name
                        },
                        "time": current_time,
                        "fields": {
                            "value": 1 if shoutcast_info.group(1) else 0
                        }
                    })
                    measurements.append({
                        "measurement": "radio_listeners",
                        "tags": {
                            "radio_name": radio_name,
                            "origin": server_info.get('origin'),
                            "server_name": server_name,
                            "current_song": current_song_r.content
                        },
                        "time": current_time,
                        "fields": {
                            "value": int(shoutcast_info.group(2))
                        }
                    })
                    measurements.append({
                        "measurement": "radio_current_song",
                        "tags": {
                            "radio_name": radio_name,
                            "origin": server_info.get('origin'),
                            "server_name": server_name
                        },
                        "time": current_time,
                        "fields": {
                            "value": current_song_r.content
                        }
                    })
                break
        except ConnectionError as e:
            pass
        except Exception as e:
            print e
        finally:
            time.sleep(0.5)

print measurements
# PUSH the stats
client = InfluxDBClient('influxdb', 8086, 'shoutcast', '1shoutcast!', 'shoutcast')
client.write_points(measurements) 
