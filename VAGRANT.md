http://www.opscode.com/chef/

Setup vagrant instance for local development
============================================

* Install [Vagrant](http://www.opscode.com/chef/)
* Run in project directory:

```
vagrant up
```

Your develpment virtual machine will be setuped.

Connect them by ssh:
```
vagrant ssh
```

Update your "hosts" file. (/etc/hosts on OSX and Linux)
```
33.33.33.33 joltem.local
```

Go to project directory (shared with your repository)
update database and run development server.

```
cd /joltem
make db
make run
```

Have a fun.
