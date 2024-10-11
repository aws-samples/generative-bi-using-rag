#!/bin/bash


wget https://raw.githubusercontent.com/harryho/db-samples/refs/heads/master/mysql/northwind.sql

cp northwind.sql initial_data/

newgrp docker << EOF
docker exec nlq-mysql sh -c "mysql -u root -ppassword -D llm  < /opt/data/northwind.sql"
EOF
