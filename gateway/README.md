#### Gateway Setup

Some notes here about things to be aware when setting up the gateway ( git server and shell ).

##### Database Isolation Transaction Level

I experienced issues when running Django in one process and the Twisted based gateway in another process. For example if I would add or remove a SSH key through the site's web interface it would not be reflected in the behaviour of the gateway until the web server was restarted. I was using MySQL with InnoDB tables on the local machine.

After some research I found that even though Django is set by default to *autocommit* changes the underlying database may not be and its isolation behaviour may vary.

So for a *MySQL* database I needed to run this command to fix the problem :

```
SET GLOBAL TRANSACTION ISOLATION LEVEL READ COMMITTED
```
So when setting up configurations we need to keep this issue in mind.

###### References :
- [Multiple Processes Accessing Django DB](http://stackoverflow.com/questions/1107091/multiple-processes-accessing-django-db-backend-records-not-showing-up-until-man)
- [MySQL Isolation Levels](http://dev.mysql.com/doc/refman/5.0/en/set-transaction.html)

