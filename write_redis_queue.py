#  Copyright 2014 Christian Eichelmann
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import collectd

import json
from hotqueue import HotQueue

REDIS_HOST  = 'localhost'
REDIS_PORT  = 6379
REDIS_QUEUE = 'collectd'

TYPES = {}

def parse_types_file(path):
    f = open(path, 'r')

    types = {}
    for line in f:
        fields = line.split()
        if len(fields) < 2:
            continue

        type_name = fields[0]

        if type_name[0] == '#':
            continue

        v = []
        for ds in fields[1:]:
            ds = ds.rstrip(',')
            ds_fields = ds.split(':')

            if len(ds_fields) != 4:
                collectd.warning('write_redis_queue: cannot parse data source %s on type %s' % ( ds, type_name ))
                continue

            v.append(ds_fields)

        types[type_name] = v

    f.close()
    return types


def str_to_num(s):
    """
    Convert type limits from strings to floats for arithmetic.
    Will force U[nlimited] values to be 0.
    """

    try:
        n = float(s)
    except ValueError:
        n = 0

    return n


def redis_queue_config(c):
    global REDIS_HOST
    global REDIS_PORT
    global REDIS_QUEUE
    global TYPES

    for child in c.children:
        if child.key == 'Host':
            REDIS_HOST = child.values[0]
        elif child.key == 'Port':
            REDIS_PORT = int(child.values[0])
        elif child.key == 'Queue':
            REDIS_QUEUE = child.values[0]
        elif child.key == 'TypesDB':
            for v in child.values:
                TYPES.update(parse_types_file(v))


def redis_queue_init():
    import threading

    d = {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'queue': REDIS_QUEUE,
        'hotqueue': None,
        'lock': threading.Lock(),
    }

    create_queue(d)

    collectd.register_write(redis_write, data=d)


def create_queue(data):
    try:
        data['hotqueue'] = HotQueue(data['queue'], serializer=json, host=data['host'], port=data['port'], db=0)
    except:
        return False
    else:
        return True


def redis_write(v, data=None):
    if v.type not in TYPES:
        collectd.warning('write_redis_queue: do not know how to handle type %s. do you have all your types.db files configured?' % v.type)
        return

    v_type = TYPES[v.type]

    if len(v_type) != len(v.values):
        collectd.warning('write_redis_queue: differing number of values for type %s' % v.type)
        return

    metric = {}
    metric['host'] = v.host
    metric['plugin'] = v.plugin
    metric['plugin_instance'] = v.plugin_instance
    metric['type'] = v.type
    metric['type_instance'] = v.type_instance
    metric['time'] = v.time
    metric['interval'] = v.interval

    # prepare metric values lists
    metric['values'] = []
    metric['dstypes'] = []
    metric['dsnames'] = []

    # we update shared recorded values, so lock to prevent race conditions
    data['lock'].acquire()

    i = 0
    for value in v.values:
        ds_name = v_type[i][0]
        ds_type = v_type[i][1]

        metric['dsnames'].append(ds_name)
        metric['dstypes'].append(ds_type)
        metric['values'].append(str_to_num(value))

        i += 1

    data['hotqueue'].put([metric, ])

    data['lock'].release()


collectd.register_config(redis_queue_config)
collectd.register_init(redis_queue_init)
