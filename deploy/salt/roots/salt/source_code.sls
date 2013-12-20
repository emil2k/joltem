joltem source code:
  file:
    - symlink
    - name: {{ pillar['website_src_dir'] }}
    - target: /home/vagrant/joltem
    - force: True
    - require:
      - user: joltem
