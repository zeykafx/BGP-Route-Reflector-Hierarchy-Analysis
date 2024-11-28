#!/bin/bash

RO_FRR_CONF="/etc/frr/frr.ro.conf"
FRR_CONF="/etc/frr/frr.conf"
DOCKER_START="/usr/lib/frr/docker-start"

if [ ! -f "${RO_FRR_CONF}" ]; then
    echo "FATAL: '${RO_FRR_CONF}' not found. Make sure that you correctly mounted the file."
    exit 1
fi

cp "${RO_FRR_CONF}" "${FRR_CONF}"
chown frr:frr "${FRR_CONF}"

# NOW start frr
${DOCKER_START}
