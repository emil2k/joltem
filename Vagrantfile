# -*- mode: ruby -*-

Vagrant.configure('2') do |config|
  config.vm.box = 'precise64'
  config.vm.box_url = 'http://files.vagrantup.com/precise64.box'

  config.vm.provider :virtualbox do |v|
    v.customize ['modifyvm', :id, '--name', 'joltem.local']
    v.customize ['modifyvm', :id, '--memory', 1024]
  end

  config.vm.hostname = 'joltem.local'

  config.vm.network :private_network, ip: '33.33.33.33'

  config.vm.synced_folder '.', '/home/vagrant/joltem/'
  config.vm.synced_folder './deploy/salt/roots/', '/srv/'

  config.vm.provision :salt do |salt|
    salt.minion_config = 'salt/minion.conf'
    salt.run_highstate = true
    salt.verbose = true
  end
end
