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
      - libmysqlclient-dev
      - python-mysqldb

database-setup:
  mysql_user:
    - present
    - name: {{ pillar['mysql_user'] }}
    - password: {{ pillar['mysql_password'] }}
    - require:
      - pkg: python-mysqldb
      - service: mysql-server

  mysql_database:
    - present
    - name: {{ pillar['mysql_db'] }}
    - require:
      - mysql_user: database-setup

  mysql_grants:
    - present
    - grant: all privileges
    - database: {{ pillar['mysql_db'] }}.*
    - user: {{ pillar['mysql_user'] }}
    - require:
      - mysql_database: database-setup
