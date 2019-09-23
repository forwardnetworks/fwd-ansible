FROM ubuntu:18.04

RUN apt-get update && apt-get install -y \
    python2.7 \
    python-pip

RUN apt-get install -y software-properties-common
RUN apt-add-repository ppa:ansible/ansible
RUN apt-get update
RUN apt-get install -y ansible
RUN apt-get install -y vim

# Add project
COPY . /home/fwd-ansible

# Install dependencies
RUN pip install -U pip distribute
RUN pip install requests
RUN cd /home/fwd-ansible/deps/fwd-api/ && python setup.py install

WORKDIR /home/fwd-ansible
