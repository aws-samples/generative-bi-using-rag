#!/bin/bash

wget https://raw.githubusercontent.com/harryho/db-samples/refs/heads/master/mysql/northwind.sql

mv northwind.sql initial_data

docker exec nlq-mysql sh -c "mysql -u root -ppassword -D llm  < /opt/data/northwind.sql"