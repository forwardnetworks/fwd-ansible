#!/usr/bin/env python

import sys
from enum import Enum
import requests
from ansible.module_utils.forward import *

try:
    from fwd_api import check, fwd, fwd_filter
except:
    print('Error importing check from fwd_api. Check that you ran ' +
          'setup (see README).')
    sys.exit(-1)

# Module documentation for ansible-doc.
DOCUMENTATION = '''
---
module: forward_collect
short_description: Adds/removes/tests a provided check.
description:
  - Adds/removes/tests a provided check.
options:
  url:
    description:
      - URL of Forward server.
    required: true
  username:
    description:
      - Username to login to Forward server.
    required: true
  password:
    description:
      - Password to login to Forward server.
    required: true
  network_name:
    description:
      - Name of the network for which collection will be performed.
    required: true
  snapshot_id:
    description:
      - Snapshot ID to which check action will be applied.
    required: false
  state:
    description:
      - State indicates whether to Present, Absent or Test a check.
        'Present' will add a check if it is not already added and persist the check.
        'Delete' will remove an existing check if it exists.
        'Test' will search for the check but it will
        not persist the check.
    required: false
  mock_snapshot:
    description:
      - Details of the snapshot to upload. Instead of collecting new snapshot, we will upload the snapshot provided with
        this option.
    required: true
  data:
    description:
      - source (or) source_host (to search from host)
      - ipv4_dst
      - ip_proto
      - tp_src
      - tp_dst
'''

# Example usage for ansible-doc.
EXAMPLES = '''
---
- name: Check from device_A to 20.1.1.1:88000
  forward_collect:
    url: https://localhost:8443
    username: admin
    password: password
    snapshot_id: 100
    state: present
    data:
      source: device_A
      ipv4_dst: 20.1.1.1
      ip_proto: tcp
      tp_src: 443
      tp_dst: 88000
'''


class State(Enum):
    PRESENT = 'Present'
    ABSENT = 'Absent'


class Type(Enum):
    TYPICAL_5_TUPLE = 'typical_5_tuple'


STATES = [e.value for e in State]
TYPES = [e.value for e in Type]


# Delete keys from check definition which are not useful for check comparision.
def cleanup_check_definition(check_definition):
    try:
        del check_definition['filters']['from']['type']
    except KeyError:
        pass
    try:
        del check_definition['name']
    except KeyError:
        pass
    try:
        del check_definition['note']
    except KeyError:
        pass


def perform_check_action(module, fwd_client_instance, snapshot_id, state, data, name, check_id):
    response = None
    if state is State.PRESENT:
        if 'source' not in data and 'source_host' not in data:
            module.fail_json(rc=256, msg="'source' or 'source_host' is mandatory in check data")

        if 'source' in data and 'source_host' in data:
            module.fail_json(rc=256, msg="Either 'source' or 'source_host' is allowed in check data")

        packet_filters = []
        if 'ipv4_dst' in data:
            packet_filters.append(fwd_filter.PacketFilter([fwd_filter.IpDstField(data['ipv4_dst'])]))
        if 'ip_proto' in data:
            packet_filters.append(fwd_filter.PacketFilter([fwd_filter.IpProtoField(data['ip_proto'])]))
        if 'tp_src' in data:
            packet_filters.append(fwd_filter.PacketFilter([fwd_filter.L4SrcField(data['tp_src'])]))
        if 'tp_dst' in data:
            packet_filters.append(fwd_filter.PacketFilter([fwd_filter.L4DstField(data['tp_dst'])]))

        source_filter = None
        if 'source' in data:
            source_filter = fwd_filter.DeviceFilter(data['source'])
        elif 'source_host' in data:
            source_filter = fwd_filter.HostFilter(data['source_host'])

        if len(packet_filters) == 0:
            packet_filters = None

        from_filter = fwd_filter.EndpointFilter(source_filter, packet_filters)
        c = check.ExistenceCheck(from_filter, None, name)

        check_definition = c.to_check_dict()
        cleanup_check_definition(check_definition)

        # If check already exists, don't add it.
        for item in fwd_client_instance.get_checks(snapshot_id, verbose=False):
            item_definition = item.get_response()['definition']
            cleanup_check_definition(item_definition)
            if item_definition['checkType'] == 'Existential' and\
                    sorted(item_definition.items()) == sorted(check_definition.items()):
                module.exit_json(changed=False, result=item.get_response(),
                                 message="Matched a check for snapshot %s" % snapshot_id)

        response = fwd_client_instance.upload_check(c, snapshot_id, verbose=False)
        module.exit_json(changed=(response is not None and response.get_check_id() is not None),
                         result=response.get_response())
    elif state is State.ABSENT:
        fwd_client_instance.delete_check(snapshot_id, check_id, verbose=False)
        for item in fwd_client_instance.get_checks(snapshot_id, verbose=False):
            if item.get_check_id() == check_id:
                response = item
        module.exit_json(changed=(response is None), result=None)


def get_latest_snapshot_id(fwd_client_instance, network_id):
    r = fwd_client_instance.get_snapshots_info(network_id, verbose=False)
    snapshots = r.get_snapshots()
    if len(snapshots) == 0:
        return None
    return snapshots[0].get_id()


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
            network_name=dict(type='str', required=False),
            snapshot_id=dict(type='int', required=False),
            type=dict(type='str', required=False, choices=TYPES),
            data=dict(type='dict', required=False),
            state=dict(type='str', required=False, default=State.PRESENT.value, choices=STATES),
            name=dict(type='str', required=False, default=''),
            check_id=dict(type='int', required=False),
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

    network_name = properties.get_network_name()
    snapshot_id = module.params['snapshot_id']
    if network_name is None and snapshot_id is None:
        module.fail_json(rc=256, msg="Network ID or snapshot ID is required.")

    name = module.params['name']

    check_id = module.params['check_id']
    state = State(module.params['state'])

    fwd_client_instance = fwd.Fwd(url, username, password, verbose=False, verify_ssl_cert=False)

    if snapshot_id is None:
        if network_name is None:
            module.fail_json(rc=256, msg="Either network_name or snapshot_id is mandatory for this module")

        network_id = Utils.get_network_id(fwd_client_instance, network_name)
        if network_id < 0:
            module.fail_json(rc=256, msg="No network present with given name '%s'." % network_name)

        snapshot_id = get_latest_snapshot_id(fwd_client_instance, network_id)
        if snapshot_id is None:
            module.fail_json(rc=256, msg="No snapshots available in the network.")

    if state is State.ABSENT and check_id is None:
        module.fail_json(rc=256, msg="Check ID is required to delete a check.")

    if check_id is not None:
        c = fwd_client_instance.get_check(snapshot_id, check_id, verbose=False)
        if state is State.PRESENT:
            module.exit_json(changed=False, result=c.get_response())
        if c.get_check_id() is None:
            module.exit_json(changed=False, msg="Check with ID %d doesn't exist." % check_id)

    data = module.params['data']
    if data is None and state is State.PRESENT:
        module.fail_json(rc=256, msg="Check data is not provided.")

    perform_check_action(module, fwd_client_instance, snapshot_id, state, data, name, check_id)


# Although PEP-8 prohibits wildcard imports, ansible modules _must_ use them:
# https://github.com/ansible/ansible/blob/devel/lib/ansible/module_common.py#L116
from ansible.module_utils.basic import *  # noqa
main()
