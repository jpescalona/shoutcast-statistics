FROM centos:latest
MAINTAINER Juan Pedro Escalona <jpescalona@otioti.com>
USER root

COPY *.sh /usr/local/bin/
MKDIR /opt/monitor
COPY server-example.yaml /opt/monitor/servers.yaml

RUN yum -y install epel-release cronie python-requests python-pip \
  && yum clean all \
  && pip install -U pip pyyaml influxdb beautifulsoup4
  && chmod a+x /usr/local/bin/* \
  && echo "* * * * * /usr/local/bin/monitor.py >/dev/null 2>&1" > /tmp/crontab \
  && crontab /tmp/crontab

ENTRYPOINT ["/usr/sbin/crond -n"]
