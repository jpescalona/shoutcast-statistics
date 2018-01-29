FROM centos:latest
MAINTAINER Juan Pedro Escalona <jpescalona@otioti.com>
USER root

COPY *.sh /usr/local/bin/

RUN yum -y install curl cronie python-requests python-influxdb \
  && yum clean all \
  && chmod a+x /usr/local/bin/* \
  && echo "* * * * * /usr/local/bin/monitor.py >/dev/null 2>&1" > /tmp/crontab \
  && crontab /tmp/crontab

ENTRYPOINT ["/usr/sbin/crond -n"]
