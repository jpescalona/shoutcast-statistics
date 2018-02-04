FROM centos:latest
MAINTAINER Juan Pedro Escalona <jpescalona@otioti.com>
USER root

COPY *.py /usr/local/bin/
RUN mkdir -p /opt/monitor
COPY servers-example.yaml /opt/monitor/servers.yaml

RUN yum -y install epel-release cronie \
  && yum -y install python-pip \
  && yum clean all \
  && pip install -U pip pyyaml influxdb beautifulsoup4 requests \
  && chmod a+x /usr/local/bin/* \
  && echo "* * * * * /usr/local/bin/monitor.py >/dev/null 2>&1" > /tmp/crontab \
  && crontab /tmp/crontab

ENTRYPOINT ["/usr/sbin/crond", "-n"]
