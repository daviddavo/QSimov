#!/usr/bin/env bash

# Credenciales para conectarse al servidor en el que se despliega el contenedor;


# Debe estar definido en Gitlab, como una variable del proyecto


DEPLOYMENT_PASS=$1

IP=quantum@10.0.0.240

# Conectarse por SSH al servidor de builds, 

sshpass -p "$DEPLOYMENT_PASS" scp latest.tar.gz $IP:/home/quantum
sshpass -p "$DEPLOYMENT_PASS" ssh -o StrictHostKeyChecking=no -T "$IP" << EOF
rm -rf QSimulator/*
tar -zxvf latest.tar.gz -C QSimulator
rm latest.tar.gz
exit
EOF
