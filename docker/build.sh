#!/usr/bin/env bash

VERSION=0.1

docker build . -t fwd-ansible:${VERSION}
docker save fwd-ansible:${VERSION} > fwd-ansible-${VERSION}.tar

echo ""
echo fwd-ansible docker image is at fwd-ansible-${VERSION}.tar
