#!/usr/bin/env python

import sys
from ansible.module_utils.forward import *
try:
    from fwd_api import fwd
except:
    print('Error importing fwd from fwd_api. Check that you ran ' +
          'setup (see README).')
    sys.exit(-1)

# Module documentation for ansible-doc.
DOCUMENTATION = '''
---
module: forward_network
short_description: Returns information about the networks matching keyword in their name
description:
    - Returns information about the networks matching keyword in their name
options:
  keyword:
    description:
      - Keyword to search for in network names
'''

# Example usage for ansible-doc.
EXAMPLES = '''
---
- name: Get networks which have name with keyword 'demo'
  forward_network:
    url: https://localhost:8443
    username: admin
    password: password
    keyword: demo
- name: Get all networks
  forward_network:
    url: https://localhost:8443
    username: admin
    password: password
'''


def main():
    '''The entrypoint for this module.

    Prints ansible facts in JSON format on STDOUT and exits.
    '''
    module = AnsibleModule(
        argument_spec=dict(
            properties_file_path=dict(type='str', required=False),
            url=dict(type='str', required=False),
            username=dict(type='str', required=False),
            password=dict(type='str', required=False, no_log=True),
            keyword=dict(type='str', required=False, default=''),
        )
    )

    properties_file_path = module.params['properties_file_path']
    properties = Properties(module, properties_file_path)

    url = properties.get_url()
    if url is None:
        module.fail_json(rc=256, msg="Forward server URL is not provided.")

    username = properties.get_username()
    if username is None:
        module.fail_json(rc=256, msg="Username to login to Forward server is not provided.")

    password = properties.get_password()
    if password is None:
        module.fail_json(rc=256, msg="Password to login to Forward server is not provided.")

    fwd_client_instance = fwd.Fwd(url, username, password, verbose=False, verify_ssl_cert=False)

    keyword = module.params['keyword']

    networks = Utils.search_networks(fwd_client_instance, keyword)
    module.exit_json(changed=False, result=networks)

# Although PEP-8 prohibits wildcard imports, ansible modules _must_ use them:
# https://github.com/ansible/ansible/blob/devel/lib/ansible/module_common.py#L116
from ansible.module_utils.basic import *  # noqa
main()
