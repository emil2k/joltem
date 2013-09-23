# -*- mode: ruby -*-
# vi: set ft=ruby:fdm=marker

# Options {{{
#
APP_HOST = '33.33.33.33'
APP_HOSTNAME = 'joltem.local'
# APP_ROLES = ['joltem', 'db']
APP_ROLES = ['vagrant', 'db']
APP_JSON = {
    :chef_environment => 'vagrant',
    :joltem => {
        'db-host' => APP_HOST,
        'domain' => APP_HOST
    }
}
SHARED_OPTIONS = {
    :nfs => true
}
CONFIGURATION = './vagrant'

# }}}


# Vagrant 2.0.x {{{
#
Vagrant.configure("2") do |config|
 
    # Every Vagrant virtual environment requires a box to build off of.
    config.vm.box = "precise64"
    config.vm.box_url = "http://files.vagrantup.com/precise64.box"

    # Set hostname
    config.vm.hostname = APP_HOSTNAME

    # Configure network
    config.vm.network :private_network, ip: APP_HOST

    # Configure provider
    config.vm.provider :virtualbox do |vb|
      vb.gui = false
      vb.customize ["modifyvm", :id, "--memory", "1024"]
      vb.customize ["modifyvm", :id, "--name", APP_HOSTNAME]
    end

    # Share folders
    config.vm.synced_folder ".", "/joltem", SHARED_OPTIONS

    # Enable provisioning with chef solo
    config.vm.provision :chef_solo do |chef|
        chef.log_level = :info
        chef.cookbooks_path = "#{ CONFIGURATION }/cookbooks"
        chef.roles_path = "#{ CONFIGURATION }/roles"
        chef.data_bags_path = "#{ CONFIGURATION }/data_bags"

        APP_ROLES.each do |role|
            chef.add_role role
        end
        chef.json = APP_JSON

    end

    # SSH config
    # config.ssh.forward_x11 = true
    config.ssh.forward_agent = true
end
# }}}

