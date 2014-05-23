redis-queue-collectd-plugin
===========================

A [Redis](http://redis.io) plugin for [collectd](http://collectd.org) using collectd's [Python plugin](http://collectd.org/documentation/manpages/collectd-python.5.shtml).

This plugin is an output plugin (writer). Instead of using Redis as a datastore like the native ```write_redis``` plugin which is part of collectd, it uses Redis as a queue. So this can be seen as an alternative to the amqp-plugin (which is not very cool if you want to use json and a lot of custom types).

The format of the data is collectd's JSON format (the same that can be used for rabbitmq).

Install
-------
 1. Place ```write_redis_queue.py``` in ```${COLLECTD_PLUGINDIR}/python/write_redis_queue.py```
 3. Configure the plugin (see below).
 4. Restart collectd.

Configuration
-------------
Add the following to your collectd config:

```
    <LoadPlugin python>
      Globals true
    </LoadPlugin>

    <Plugin python>
      ModulePath "/usr/lib/collectd/python"
      Import "write_redis_queue"

      <Module write_redis_queue>
        Host "localhost"
        Port 6379
        Queue "collectd"
        TypesDB "/usr/share/collectd/types.db"
      </Module>
    </Plugin>
```

You can add multiple typesdb files here, but they are needed to construct the json structure. 

Contribution
------------

If you experience any errors, please open an issue on github!
