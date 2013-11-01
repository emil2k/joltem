name             'pypi'
maintainer       'Kirill Klenov'
maintainer_email 'horneds@gmail.com'
license          ''
description      'Installs/Configures pypi'
long_description IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version          '0.1.0'

depends "apt"
depends "runit"
depends "nginx"
