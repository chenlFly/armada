import random
import time

from armada_backend import docker_client
from armada_backend.utils import deregister_services, shorten_container_id, get_container_parameters, get_ship_name
from armada_command.consul.consul import consul_query
from armada_command.consul import kv


def get_local_services_ids():
    return consul_query('agent/services').keys()


def get_running_container_ids():
    docker_api = docker_client.api()
    return set(shorten_container_id(container['Id']) for container in docker_api.containers())


def deregister_not_running_services():
    services_ids = get_local_services_ids()
    containers_ids = get_running_container_ids()
    for service_id in services_ids:
        if service_id != 'consul':
            container_id = service_id.split(':')[0]
            if container_id not in containers_ids:
                name = consul_query('agent/services')[service_id]['Service']
                params = get_container_parameters(container_id)
                kv_index = 0
                if kv.kv_list('service/{}/'.format(name)):
                    kv_index = int(kv.kv_list('service/{}/'.format(name))[-1].split('/')[2]) + 1
                kv.save_service(name, kv_index, 'crashed', params, container_id)
                deregister_services(container_id)


def main():
    while True:
        deregister_not_running_services()
        time.sleep(60 + random.uniform(-5, 5))


if __name__ == '__main__':
    main()
