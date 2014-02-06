myCMS
=====

myCMS is an example RESTful API for content management (ie blog articles, surveys, photo galleries) built on Python Flask and MongoDB. It is the example application used in the ['Building an Application' series](https://www.mongodb.com/webinar/build_app-part_1) of webinars run by MongoDB in EMEA. It will be developed over the course of the series and can be used to get started and play, and may even be the basis for your own project development.

Current functionality
---------------------

* Add an article 
* Retrieve all articles sorted by date
* Retrieve all articles by tag
* Retrieve a article
* Register users
* Record article view/comment interactions by time
* Retrieve all comments or a page of comments for an article
* Basic HTTP authentication with username/ hashed password lookup

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

Install dependencies using pip and the provided [requirements.txt](../master/requirements.txt) file:
```shell
$ pip install –r requirements.txt
```

Start a MongoDB server, using init/service commands, or manually at the shell:
```shell
$ mkdir –p data/db
$ mongod --dbpath=data/db --fork --logpath=mongod.log
```

And now you can start the myCMS API server. By default, it runs on port 5000 on the localhost.

```shell
$ python web.py
```

Optionally, if you're using virtualenv, remember to deactivate it when you shutdown the server and do not require it any further.

```shell
$ deactivate
```

Further reading
---------------

Please read the online documentation for more about data modelling in MongoDB, including sections on common use cases (which myCMS is based in part).

* [Data Models](http://docs.mongodb.org/manual/data-modeling/)
* [Use case - metadata and asset management:](http://docs.mongodb.org/ecosystem/use-cases/metadata-and-asset-management/)
* [Use case - storing comments](http://docs.mongodb.org/ecosystem/use-cases/storing-comments/)

Disclaimer
----------

**Important note:** myCMS is example source code and should not be used for production purposes. MongoDB does not support or maintain myCMS.