#!/usr/bin/python
# coding=utf-8

import logging
import sys

from bottle import request, run

sys.path.insert(0, '..')

from apps import (error_wrap, get_json, Route,
                  send_result, setup_versioned_routes)
from lib.common import *
from lib.sharded_clusters import ShardedClusters

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _sh_create(params):
    cluster_id = ShardedClusters().create(params)
    result = ShardedClusters().info(cluster_id)
    return send_result(200, result)


def _build_server_uris(docs):
    return [{'uri': '/servers/' + doc['id']} for doc in docs]


def _build_shard_info(shard_docs):
    resource_info = []
    for shard_doc in shard_docs:
        repl_set = shard_doc.get('isReplicaSet')
        resource = 'replica_sets' if repl_set else 'servers'
        info = {
            "shard_id": shard_doc['id'],
            "tags": shard_doc['tags'],
            "uri": '/' + resource + '/' + shard_doc['_id']}
        info['isReplicaSet' if repl_set else 'isServer'] = True
        resource_info.append(info)
    return resource_info


@error_wrap
def sh_create():
    logger.debug("sh_create()")
    data = {}
    json_data = request.body.read()
    if json_data:
        data = get_json(json_data)
    data = preset_merge(data, 'sharded_clusters')
    return _sh_create(data)


@error_wrap
def sh_list():
    logger.debug("sh_list()")
    data = [sh_info for sh_info in ShardedClusters()]
    return send_result(200, data)


@error_wrap
def info(cluster_id):
    logger.debug("info({cluster_id})".format(**locals()))
    if cluster_id not in ShardedClusters():
        return send_result(404)
    result = ShardedClusters().info(cluster_id)
    return send_result(200, result)


@error_wrap
def sh_create_by_id(cluster_id):
    logger.debug("sh_create()")
    data = {}
    json_data = request.body.read()
    if json_data:
        data = get_json(json_data)
    data = preset_merge(data, 'sharded_clusters')
    data['id'] = cluster_id
    return _sh_create(data)


@error_wrap
def sh_del(cluster_id):
    logger.debug("sh_del({cluster_id})".format(**locals()))
    if cluster_id not in ShardedClusters():
        return send_result(404)
    result = ShardedClusters().remove(cluster_id)
    return send_result(204, result)


@error_wrap
def shard_add(cluster_id):
    logger.debug("shard_add({cluster_id})".format(**locals()))
    if cluster_id not in ShardedClusters():
        return send_result(404)
    data = {}
    json_data = request.body.read()
    if json_data:
        data = get_json(json_data)
    result = ShardedClusters().member_add(cluster_id, data)
    return send_result(200, result)


@error_wrap
def shards(cluster_id):
    logger.debug("shards({cluster_id})".format(**locals()))
    if cluster_id not in ShardedClusters():
        return send_result(404)
    members = ShardedClusters().members(cluster_id)
    return send_result(200, _build_shard_info(members))


@error_wrap
def configsvrs(cluster_id):
    logger.debug("configsvrs({cluster_id})".format(**locals()))
    if cluster_id not in ShardedClusters():
        return send_result(404)
    result = _build_server_uris(ShardedClusters().configsvrs(cluster_id))
    return send_result(200, result)


@error_wrap
def routers(cluster_id):
    logger.debug("routers({cluster_id})".format(**locals()))
    if cluster_id not in ShardedClusters():
        return send_result(404)
    result = _build_server_uris(ShardedClusters().routers(cluster_id))
    return send_result(200, result)


@error_wrap
def router_add(cluster_id):
    logger.debug("router_add({cluster_id})".format(**locals()))
    if cluster_id not in ShardedClusters():
        return send_result(404)
    data = {}
    json_data = request.body.read()
    if json_data:
        data = get_json(json_data)
    result = ShardedClusters().router_add(cluster_id, data)
    return send_result(200, result)


@error_wrap
def router_del(cluster_id, router_id):
    logger.debug("router_del({cluster_id}), {router_id}".format(**locals()))
    if cluster_id not in ShardedClusters():
        return send_result(404)
    result = ShardedClusters().router_del(cluster_id, router_id)
    return send_result(200, result)


@error_wrap
def shard_info(cluster_id, shard_id):
    logger.debug("shard_info({cluster_id}, {shard_id})".format(**locals()))
    if cluster_id not in ShardedClusters():
        return send_result(404)
    result = ShardedClusters().member_info(cluster_id, shard_id)
    return send_result(200, result)


@error_wrap
def shard_del(cluster_id, shard_id):
    logger.debug("member_del({cluster_id}), {shard_id}".format(**locals()))
    if cluster_id not in ShardedClusters():
        return send_result(404)
    result = ShardedClusters().member_del(cluster_id, shard_id)
    return send_result(200, result)


ROUTES = {
    Route('/sharded_clusters', method='POST'): sh_create,
    Route('/sharded_clusters', method='GET'): sh_list,
    Route('/sharded_clusters/<cluster_id>', method='GET'): info,
    Route('/sharded_clusters/<cluster_id>', method='PUT'): sh_create_by_id,
    Route('/sharded_clusters/<cluster_id>', method='DELETE'): sh_del,
    Route('/sharded_clusters/<cluster_id>/shards', method='POST'): shard_add,
    Route('/sharded_clusters/<cluster_id>/shards', method='GET'): shards,
    Route('/sharded_clusters/<cluster_id>/configsvrs',
          method='GET'): configsvrs,
    Route('/sharded_clusters/<cluster_id>/routers', method='GET'): routers,
    Route('/sharded_clusters/<cluster_id>/routers', method='POST'): router_add,
    Route('/sharded_clusters/<cluster_id>/routers/<router_id>',
          method='DELETE'): router_del,
    Route('/sharded_clusters/<cluster_id>/shards/<shard_id>',
          method='GET'): shard_info,
    Route('/sharded_clusters/<cluster_id>/shards/<shard_id>',
          method='DELETE'): shard_del
}

setup_versioned_routes(ROUTES, version='v1')
# Assume v1 if no version is specified.
setup_versioned_routes(ROUTES)

if __name__ == '__main__':
    rs = ShardedClusters()
    rs.set_settings()
    run(host='localhost', port=8889, debug=True, reloader=False)
