# Getting started

This is a guide on how to setup the project in your local environment for development.

---

Let's assume that you have already installed
[Vagrant](http://www.vagrantup.com) and
[VirtualBox](https://www.virtualbox.org).

First, you have to install Salty Vagrant :

    $ vagrant plugin install vagrant-salt

Second, add `precise64` box if you have not got it yet :

    $ vagrant box add precise64 http://files.vagrantup.com/precise64.box

or do the following if you have a slow network connection :

    $ wget -c http://files.vagrantup.com/precise64.box
    $ vagrant box add precise64 precise64.box

`vagrant box add` is required only once. It installs a box named
`precise64` to `~/.vagrant.d`.

Run the following command in the `vagrant` folder. It will install every dependency that the project needs,
setup any networking, and sync folders :

    $ vagrant up

In order to reach the development site add `33.33.33.33 joltem.local` to `/etc/hosts`. Now it should work (N.B. site is served by Nginx) :

    $ curl -i joltem.local

If you want to start the Django development server you need to log into the guest VM by ssh :

    $ vagrant ssh
    $ cd /home/joltem/joltem
    $ source /home/joltem/venv/bin/activate
    (venv)$ python manage.py runserver 33.33.33.33:8000

Now `curl -i joltem.local:8000` requests are served by built in Django server.

##### Users

The vagrant setup will create a few dummy users that you can sign in with immediately to test the system, all passwords are `123` with usernames :

* emil ( admin )
* becky
* bob
* ian
* jill
* kate
* will

However you can also create a super user :

    (venv)$ python manage.py createsuperuser

##### Gateway

In order to clone repository you have to add your public key on
``http://joltem.local/account/keys/`` page. Say your username is ``marsel``, the repository id is ``1``, and the git server listens on port ``222`` :

    $ git clone ssh://marsel@joltem.local:222/1

Also you can access the site's shell by running :

	$ ssh -p 222 marsel@joltem.local

##### Tests

You can run tests from VM:

    (venv)$ python manage.py test

##### Troubleshooting

If something goes wrong, see logs at `/var/log/supervisor`.

If you encounter intermittent 404s, you might have multiple VMs running
at the same time. We suggest powering off all VMs and unregister
the inaccessible ones and reran the Vagrant up progress.
