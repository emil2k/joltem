ssh secret:
  file:
    - managed
    - name: /joltem/gateway/id_rsa
    - source: salt://twisted_gateway/id_rsa
    - user: vagrant
    - group: vagrant
    - mode: 600

ssh public:
  file:
    - managed
    - name: /joltem/gateway/id_rsa.pub
    - source: salt://twisted_gateway/id_rsa.pub
    - user: vagrant
    - group: vagrant
    - mode: 644

twisted_gateway:
  supervisord:
    - running
    - watch:
      - file: twisted_gateway
    - require:
      - pkg: supervisor
      - file: ssh secret
      - file: ssh public
  pkg:
    - installed
    - name: supervisor
  file:
    - managed
    - name: /etc/supervisor/conf.d/twisted_gateway.conf
    - source: salt://twisted_gateway/supervisord.conf
