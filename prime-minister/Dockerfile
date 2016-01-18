FROM ubuntu:vivid
MAINTAINER Ory Band <http://oryband.com>

# necessary for using 'source' keyword
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# install python
RUN apt-get update && \
    apt-get install -y python python-dev python-setuptools python-pip && \
    pip install --upgrade pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# install python dependencies
RUN apt-get update && \
    apt-get install -y python-dev libxml2-dev libxslt-dev zlib1g-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# create virtualenv and install dependencies
RUN pip install virtualenv && virtualenv /root/gov-review
COPY requirements.txt /tmp/requirements.txt
RUN source /root/gov-review/bin/activate && \
    pip install -r /tmp/requirements.txt && \
    deactivate

# debugging only
RUN pip install ipython

VOLUME ["/opt/gov-review"]
WORKDIR /opt/gov-review
