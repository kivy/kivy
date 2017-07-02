#!/bin/bash
docker login -e noemail -u $QUAY_USERNAME -p $QUAY_PASSWORD quay.io
tag="quay.io/pypa/manylinux1_$PLATFORM"
docker tag ${tag}:${TRAVIS_COMMIT} ${tag}:latest
docker push ${tag}:latest
