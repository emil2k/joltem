ssh secret:
  file:
    - managed
    - name: {{ pillar['gitserver_private_key_path'] }}
    - source: salt://gitserver/id_rsa
    - user: joltem
    - group: joltem
    - mode: 600

ssh public:
  file:
    - managed
    - name: {{ pillar['gitserver_public_key_path'] }}
    - source: salt://gitserver/id_rsa.pub
    - user: joltem
    - group: joltem
    - mode: 644

supervisored twisted:
  pkg:
    - installed
    - name: supervisor
  file:
    - managed
    - name: /etc/supervisor/conf.d/gitserver_twisted.conf
    - source: salt://gitserver/supervisord.conf
    - template: jinja
    - require:
      - pkg: supervisored twisted
  supervisord:
    - running
    - name: gitserver_twisted
    - restart: True
    - watch:
      - file: supervisored twisted
    - require:
      - file: ssh secret
      - file: ssh public
