mysql-server:
  pkg:
    - installed
  service:
    - running
    - name: mysql
    - require:
      - pkg: mysql-server

mysql-client:
  pkg:
    - installed
    - names:
      - mysql-client
      - python-mysqldb

database-setup:
  mysql_user:
    - present
    - name: joltem
    - password: bobcat
    - require:
      - pkg: python-mysqldb
      - service: mysql-server

  mysql_database:
    - present
    - name: joltem
    - require:
      - mysql_user: database-setup

  mysql_grants:
    - present
    - grant: all privileges
    - database: joltem.*
    - user: joltem
    - require:
      - mysql_database: database-setup
