Getting started
===============

This should help you get the system setup on your computer so you can get started.

It is meant as an outline of the process and may vary when installing on various platforms.

**Things we use :**

* [Django](https://www.djangoproject.com) for a [Python](http://www.python.org) web framework.
	* [South](http://south.readthedocs.org/) for database migrations.
* [MySQL](http://www.mysql.com) for databases.
* [Gitolite](http://gitolite.com/gitolite/) as a prelimanary git server which should be able to handle a couple of thousand users, but beyond that we will need a custom solution.
* [Fabric](http://docs.fabfile.org/) for deployment. 
* [Bootstrap](http://getbootstrap.com/2.3.2/) for a front-end framework.
* [PyCharm](http://www.jetbrains.com/pycharm/) *(recommended)* a great Python and Django IDE by *JetBrains*, comes with a 30 day free trial.


####Preparation

We will assume the user you login with is named `ec2-user` (because I'm installing on EC2) and we will create a user  `git` for installation of a `gitolite` server and we will add both users to a `git-data` group to share git data.

```
ec2-user > sudo useradd git
ec2-user > sudo groupadd git-data
ec2-user > sudo usermod -a -G git-data git
ec2-user > groups git
git : git git-data
ec2-user > sudo usermod -a -G git-data ec2-user
ec2-user > groups ec2-user
ec2-user : ec2-user wheel git-data
```

Generate ssh key **without** a passphrase for `ec2-user` and then copy it to `git` user's home and chown it. This will be used for making `ec2-user` the admin of the `gitolite` server.

```
ec2-user > ssh-keygen -t rsa
ec2-user > sudo cp .ssh/id_rsa.pub /home/git/admin.pub
ec2-user > sudo chown git /home/git/admin.pub
```

Input `ec2-user`'s ssh key into Joltem system ( *Account ec2-user > Keys* ) so that you can clone the main repository.

```
ec2-user > cat .ssh/id_rsa.pub 
ssh-rsa ...
```

Install `virtualenv` an setup one at `/var/www/venv/` for example.

```
ec2-user > sudo easy_install -U distribute
ec2-user > sudo easy_install pip
Searching for pip
Reading http://pypi.python.org/simple/pip/
Best match: pip 1.4
Downloading https://pypi.python.org/packages/source/p/pip/...
ec2-user > sudo pip install virtualenv
Downloading/unpacking virtualenv
  Downloading virtualenv-1.10.tar.gz (1.3MB): 1.3MB downloaded
…
ec2-user > sudo mkdir /var/www/
[ec2-user@domU-12-31-39-07-79-EA www]$ cd /var/www/ && sudo virtualenv --no-site-packages venv
...
``` 

#### Setup gitolite

Install necessary packages and clone out the main repository so that 

```
ec2-user > cd ~
ec2-user > sudo yum install git perl-Time-HiRes
ec2-user > git clone git@joltem.com:joltem/main
ec2-user > sudo chown -R git main
ec2-user > sudo mv main /home/git/
ec2-user > sudo su git
```

Switch to `git` user.

```
git > cd ~
git > mkdir bin
git > git clone git://github.com/sitaramc/gitolite
git > gitolite/install -ln
git > bin/gitolite setup -pk admin.pub 
git > mkdir repositories/joltem
git > mv main/ repositories/joltem/
git > chgrp git-data .
git > chmod g+rX .
git > chgrp -Rv git-data repositories/
git > chmod -Rv g+wrX repositories/
```

Change `UMASK` in `.gitolite.rc` to *0007* and set `LOCAL_CODE` path like so.

```
%RC = (

    # ------------------------------------------------------------------
    LOCAL_CODE                      =>  '/var/www/joltem/git/gitolite/local-code',
    # default umask gives you perms of '0700'; see the rc file docs for
    # how/why you might change this
    UMASK                           =>  0007,

...
```

Set the `git` user's `PYTHONPATH` in the `.bashrc` to point to the `virtualenv` that you created for the custom git hooks to run properly.

```
export PYTHONPATH=/var/www/venv/:/var/www/venv/lib/python2.6/site-packages
```

#### Setup site

Set up site, and make sure that it has access to the gitolite data and update hook.

```
ec2-user > cd ~
ec2-user > git clone git@joltem.com:joltem/main
ec2-user > sudo mv main/ /var/www/joltem/
ec2-user > cd /var/www/joltem/git/
ec2-user > ln -s /home/git/repositories repositories
ec2-user > ln -s /home/git/.gitolite/hooks/common/update gitolite-update
ec2-user > cd gitolite
ec2-user > git clone git@localhost:gitolite-admin
```

Install `mysql` and create a database for the site, this will not be covered here there are plenty of [tutorials](http://www.samstarling.co.uk/2010/10/installing-mysql-on-an-ec2-micro-instance/) for this on the internet. 

After you have your database setup, you are read to configure the local settings first copy the `local.example.py` to the appropriate location.

```
[ec2-user@ip-10-138-51-252 git]$ cd /var/www/joltem/joltem/settings/
[ec2-user@ip-10-138-51-252 settings]$ cp local.example.py local.py
``` 

Then open up `local.py` and configure it appropriately, there are instructions inside to guide you.

Next install `libgit2` so that we can install `pygit2` for parsing git data in python.

```
ec2-user > cd /usr/local/src/
ec2-user > sudo su
root > git clone git://github.com/libgit2/libgit2.git -b master
root > cd libgit2/
root > mkdir build && cd build
root > yum install gcc cmake
root > cmake ..
root > cmake --build .
root > cmake --build . --target install
root > pwd > /etc/ld.so.conf.d/libgit.conf
root > ldconfig
```

Now we need to install the other requirements for the project.

```
ec2-user > sudo yum install python-devel libyaml libyaml-devel
ec2-user > cd /var/www/
ec2-user > sudo su
root > source venv/bin/activate
(venv) root > pip install -r joltem/joltem/requirements.txt 
```

Now lets sync ( *and create a Django superuser* ) and migrate the database.

```
(venv) ec2-user > python manage.py syncdb
(venv) ec2-user > python manage.py migrate project
(venv) ec2-user > python manage.py migrate git
(venv) ec2-user > python manage.py migrate
```

The site and git server should be setup now. To begin serving pages up you will need to congfigure and start up a webserver, refer to one of the many tutorials on how to deploy a Django application or if you are using the PyCharm IDE you just need to setup a run configuration.

Thanks for joining the team, if you have issues with the setup contact me at <emil2k@gmail.com>.
