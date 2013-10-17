Getting started developing Joltem
=================================

Let's assume that you have already installed
[Vagrant](http://www.vagrantup.com). First, you have to install Salty Vagrant.

    $ vagrant plugin install vagrant-salt

Second, add `precise64` box if you have not got it yet

    $ vagrant box add precise64 http://files.vagrantup.com/precise64.box

or do the following if you have a slow network connection:

    $ wget -c http://files.vagrantup.com/precise64.box
    $ vagrant box add precise64 precise64.box

`vagrant box add` is required only once. It installs a box named
`precise64` to `~/.vagrant.d`.

Following command will install every dependency that project needs,
setup any networking and sync folders:

    $ vagrant up

In order to reach development site add `33.33.33.33 joltem.local`
to `/etc/hosts/`. Now it should work:

    $ curl joltem.local
