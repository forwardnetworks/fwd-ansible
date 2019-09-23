#!/usr/bin/env python

import os.path


class Properties:

    _default_properties_file = "fwd-ansible.properties"

    def __init__(self, module, properties_file_path):
        if properties_file_path is not None and not os.path.isfile(properties_file_path):
            module.fail_json(rc=256, msg="Forward server properties file '%s' does not exist." % properties_file_path)

        self.properties = Properties._get_properties(properties_file_path)
        if 'url' in module.params and module.params['url'] is not None and module.params['url'].strip() != '':
            self.properties['url'] = module.params['url']
        if 'username' in module.params and module.params['username'] is not None and module.params[
            'username'].strip() != '':
            self.properties['username'] = module.params['username']
        if 'password' in module.params and module.params['password'] is not None and module.params[
            'password'].strip() != '':
            self.properties['password'] = module.params['password']
        if 'network_name' in module.params and module.params['network_name'] is not None and module.params[
            'network_name'].strip() != '':
            self.properties['network_name'] = module.params['network_name']

    @staticmethod
    def _get_properties(properties_file_path):
        properties = {}

        if properties_file_path is None:
            properties_file_path = Properties._default_properties_file

        if not os.path.isfile(properties_file_path):
            return properties

        with open(properties_file_path) as properties_file:
            for line in properties_file:
                name, var = line.partition("=")[::2]
                properties[name.strip()] = var.strip()

        return properties

    def get_url(self):
        if 'url' not in self.properties or self.properties['url'] is None or self.properties['url'].strip() == '':
            return None
        return self.properties['url']

    def get_username(self):
        if 'username' not in self.properties or self.properties['username'] is None or self.properties['username'].strip() == '':
            return None
        return self.properties['username']

    def get_password(self):
        if 'password' not in self.properties or self.properties['password'] is None or self.properties['password'].strip() == '':
            return None
        return self.properties['password']

    def get_network_name(self):
        if 'network_name' not in self.properties or self.properties['network_name'] is None:
            return None
        return self.properties['network_name']


class Utils:

    def __init__(self):
        return

    @staticmethod
    def get_network_id(fwd_client_instance, network_name):
        result = fwd_client_instance.get_networks_info(verbose=False)
        if len(result) == 0:
            return -1

        for network in result:
            if network.get_name() == network_name:
                return network.get_id()

        return -1

    @staticmethod
    def search_networks(fwd_client_instance, search_keyword):
        networks = fwd_client_instance.get_networks_info(verbose=False)
        if len(networks) == 0:
            return -1

        result = []
        for network in networks:
            if search_keyword in network.get_name():
                result.append({'name': network.get_name(), 'id': network.get_id()})

        return result
