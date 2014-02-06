myCMS
=====

myCMS is an example RESTful API for content management built on Python Flask and MongoDB. It is the example application used in the 'Building an Application' series of webinars run by MongoDB Inc.

Getting started
---------------

Clone this Github repo:
```shell
$ git clone http://www.github.com/mattbates/mycms_mongodb
$ cd mycms-mongodb
```

Optionally, create a Python virtualenv and activate it.
```shell
$ virtualenv venv
$ source venv/bin/activate
```

Install dependencies using pip:
```shell
$ pip install –r requirements.txt
```

Start a MongoDB server, using init/service commands, or manually at the shell:

```shell
$ mkdir –p data/db
$ mongod --dbpath=data/db --fork --logpath=mongod.log
```

And now you can start the myCMS API server:

```shell
$ python web.py
```

Optionally, if you're using virtualenv, remember to deactivate it when you shutdown the server and do not require it any further.

```shell
$ deactivate
```

**Note:** myCMS is example source code and should not be used for production purposes. MongoDB does not support or maintain myCMS.
