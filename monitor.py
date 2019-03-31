#!/usr/bin/env python
import time
import requests
import yaml
import re
import sys
import json
try:
    from influxdb import InfluxDBClient
except ImportError:
    pass
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError
from datetime import datetime


MAX_RETRIES = 3
CURRENT_TIME = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')    



def load_radios(file_path):
    with open(file_path, 'r') as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)    
            exit(1)

def get_shoutcast_radio_show_name(server, retries=MAX_RETRIES):
    while retries > 0:
        try:
            url_current_song = '{protocol}://{server_host}:{server_port}/{server_path}'.format(
                protocol='https' if server.get('secure') else 'http',
                server_host=server.get('host'),
                server_port=server.get('port'),
                server_path=server.get('current_song', 'currentsong?sid=1')
            )
            r = requests.get(url_current_song)
            if r.status_code == requests.codes.ok:
                return r.content
        except ConnectionError as e:
            pass
        except Exception:
            pass
        finally:
            retries -= 1
            time.sleep(0.5)

def get_shoutcast_server_stats(server, retries=MAX_RETRIES):
    while retries > 0:
        try:
            url_current_users = '{protocol}://{server_host}:{server_port}/{server_path}'.format(
                protocol='https' if server.get('secure') else 'http',
                server_host=server.get('host'),
                server_port=server.get('port'),
                server_path=server.get('path', 'index.html?sid=1')
            )
            r = requests.get(url_current_users)
            if r.status_code == requests.codes.ok:
                soup = BeautifulSoup(r.content, "html.parser")
                text = soup.find("td", text="Stream Status: ").find_next_sibling("td").text
                shoutcast_info = re.match("Stream is (?P<up>up).* with (?P<users>\d+) of.*", text)
                if shoutcast_info:
                    return 1 if shoutcast_info.group(1) else 0, int(shoutcast_info.group(2))
        except ConnectionError as e:
            print e
        except Exception as e:
            print e
        finally:
            retries -= 1
            time.sleep(0.5)
        return 0, 0

def get_icecast_server_stats(server, retries=MAX_RETRIES):
    while retries > 0:
        try:
            url_current_users = '{protocol}://{server_host}:{server_port}/{server_path}'.format(
                protocol='https' if server.get('secure') else 'http',
                server_host=server.get('host'),
                server_port=server.get('port'),
                server_path=server.get('path', 'status.xsl')
            )
            r = requests.get(url_current_users)
            if r.status_code == requests.codes.ok:
                soup = BeautifulSoup(r.content, "html.parser")
                for mountpoint in soup.find_all('div', class_='newscontent'):
                    if mountpoint.find("h3", text="Mount Point " + server.get('mountpoint')):
                        return 1, int(mountpoint.find('td', text='Current Listeners:').find_next_sibling().text), \
                            mountpoint.find('td', text='Current Song:').find_next_sibling().text
        except ConnectionError as e:
            print e
        except Exception as e:
            print e
        finally:
            retries -= 1
            time.sleep(0.5)
        return 0, 0, None

def get_radio_stats(radio_id,  radio_info):
    total, values, measurements = 0, {"total": 0}, []
        
    for server in radio_info.get('servers', []):
        origin = server.get('origin', 'web')
        software = server.get('software', 'shoutcast')
        if software == 'shoutcast':
            status, current_listeners = get_shoutcast_server_stats(server)
            current_radio_show_name = get_shoutcast_radio_show_name(server)
        elif software == 'icecast':
            status, current_listeners, current_radio_show_name = get_icecast_server_stats(server)

        if current_radio_show_name is None:
            continue

        measurements.append({
            "measurement": "radio_server_status",
            "tags": {
                "radio_name": radio_info.get('radio_name', radio_id),
                "radio_show_name": current_radio_show_name,
                "server_name": "{}:{}".format(server.get('host'), server.get('port')),
                "origin": origin
            },
            "time": CURRENT_TIME,
            "fields": {
                "status": status
            }
        })

        if origin not in values.keys():
            values[origin] = 0
        values[origin] += current_listeners

    for key, value in values.iteritems():
        if key != 'total':
            values['total'] += value

    if current_radio_show_name is None:
        return []

    return measurements + [
        {
            "measurement": "radio_listeners",
            "tags": {
                "radio_name": radio_info.get('radio_name', radio_id),
                "radio_show_name": current_radio_show_name 
            },
            "time": CURRENT_TIME,
            "fields": values
        }
    ]

if __name__ == "__main__":
    file_path = "/opt/monitor/radios.yaml"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]

    radios = load_radios(file_path)
    measurements = []
    for radio_id, radio_info in radios.iteritems():
        measurements += get_radio_stats(radio_id, radio_info)

    print json.dumps(measurements, indent=1)
    # PUSH the stats
    try:
        client = InfluxDBClient('influxdb', 8086, 'shoutcast', '1shoutcast!', 'shoutcast')
        client.write_points(measurements)
    except Exception:
        pass
