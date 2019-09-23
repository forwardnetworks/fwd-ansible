#!/usr/bin/env python

import sys
import time
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
module: forward_snapshot
short_description: Collects new snapshot for a given network
description:
  - Collects new snapshot for a given network.
options:
  properties_file_path:
    description:
      - Local properties file name.
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
  freshness:
    description:
      - Freshness duration of the latest snapshot. If latest was not collected with in the duration provided, this
        module perform new collection.
        Freshness duration is in the form of Minutes, Hours and Days (examples 20m, 2h, 1h10m or 1d1h30m).
  type:
    description:
      - Type could be either 'collect' or 'mock'.
        With a collection, the Forward Collector collects configuration and state from every device in the Device page.
        If 'devices' param is present to the module, only those user-specified devices are collected.
  mock_snapshot:
    description:
      - Details of the snapshot to upload. Instead of collecting new snapshot, we will upload the snapshot provided with
        this option.
'''

# Example usage for ansible-doc.
EXAMPLES = '''
---
- name: Ensure up-to-date network collection
  forward_snapshot:
    url: https://localhost:8443
    username: admin
    password: password
    network_name: test-network
    freshness: 10m
    type: mock
    mock_snapshot:
      name: snapshot_1
      path: /snapshots/1.zip

- name: Take a new partial collection
  forward_snapshot:
    url: https://localhost:8443
    username: admin
    password: password
    network_name: test-network
    type: collect
    devices:
      - sjc-te-fw01
      - atl-edge-fw01
'''


def parse_freshness(module, freshness):
    seconds = 0
    current_val = 0
    for c in freshness:
        if c.isdigit():
            current_val = current_val * 10 + int(c)
        elif c in ['s', 'S']:
            seconds += current_val
        elif c in ['m', 'M']:
            seconds += (current_val * 60)
        elif c in ['h', 'H']:
            seconds += (current_val * 60 * 60)
        elif c in ['d', 'D']:
            seconds += (current_val * 60 * 60 * 24)
        else:
            module.fail_json(rc=256, msg="Freshness string is invalid.")

    return seconds


def get_snapshots(fwd_client_instance, network_id):
    r = fwd_client_instance.get_snapshots_info(network_id, verbose=False)
    return r.get_snapshots()


def is_latest_snapshot_non_fresh(snapshots, freshness_duration):
    if len(snapshots) == 0:
        return True
    snapshot_create_time = snapshots[0].get_creation_time() / 1000
    elapsed_time = time.time() - snapshot_create_time
    if freshness_duration < elapsed_time:
        return True
    else:
        return False


def upload_snapshot(fwd_client_instance, network_id, mock_snapshot):
    return fwd_client_instance.upload_snapshot(network_id, mock_snapshot['path'], mock_snapshot['name'])


def take_snapshot(fwd_client_instance, network_id, snapshots, devices, wait_time):
    latest_snapshot = snapshots[0] if len(snapshots) != 0 else None
    if not fwd_client_instance.take_snapshot(network_id, devices):
        return None

    while fwd_client_instance.is_collection_inprogress(network_id) and (wait_time is None or wait_time > 0):
        time.sleep(10)
        if wait_time is not None:
            wait_time -= 10

    snapshots = get_snapshots(fwd_client_instance, network_id)
    if len(snapshots) < 1:
        return None
    if snapshots[0].get_id() == latest_snapshot.get_id():
        return None
    return snapshots[0]


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
            freshness=dict(type='str', required=False),
            type=dict(type='str', required=False, default='collect', choices=['collect', 'mock']),
            devices=dict(type='list', required=False),
            mock_snapshot=dict(type='dict', required=False),
            wait_time=dict(type='int', required=False),
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
    if network_name is None:
        module.fail_json(rc=256, msg="Network for which collection need to be performed is not provided.")

    fwd_client_instance = fwd.Fwd(url, username, password, verbose=False, verify_ssl_cert=False)

    freshness_duration = 0
    freshness = module.params['freshness']
    if freshness is not None:
        freshness_duration = parse_freshness(module, freshness)

    network_id = Utils.get_network_id(fwd_client_instance, network_name)
    if network_id < 0:
        module.fail_json(rc=256, msg="No network present with given name '%s'." % network_name)

    wait_time = module.params['wait_time']
    devices = module.params['devices']

    snapshots = get_snapshots(fwd_client_instance, network_id)

    if is_latest_snapshot_non_fresh(snapshots, freshness_duration):
        new_snapshot = None
        snapshot_type = module.params['type']
        if snapshot_type == 'collect':
            new_snapshot = take_snapshot(fwd_client_instance, network_id, snapshots, devices, wait_time)
        elif snapshot_type == 'mock':
            mock_snapshot = module.params['mock_snapshot']
            if mock_snapshot is None:
                module.fail_json(rc=256, msg="Mock snapshot details not provided.")
            if 'name' not in mock_snapshot:
                module.fail_json(rc=256, msg="Mock snapshot name not provided.")
            if 'path' not in mock_snapshot:
                module.fail_json(rc=256, msg="Mock snapshot file path not provided.")
            new_snapshot = upload_snapshot(fwd_client_instance, network_id, mock_snapshot)
        else:
            module.fail_json(rc=256, msg="Type '%s' is not supported." % snapshot_type)

        if new_snapshot is None:
            module.exit_json(changed=False, failed=True)

        snapshot_link = "%s/?/search?networkId=%d&snapshotId=%d" % (url, network_id, new_snapshot.get_id())
        module.exit_json(changed=True, snapshot_id=new_snapshot.get_id(), snapshot_link=snapshot_link)

    snapshot_link = "%s/?/search?networkId=%d&snapshotId=%d" % (url, network_id, snapshots[0].get_id())
    module.exit_json(changed=False, snapshot_id=snapshots[0].get_id(), snapshot_link=snapshot_link)

# Although PEP-8 prohibits wildcard imports, ansible modules _must_ use them:
# https://github.com/ansible/ansible/blob/devel/lib/ansible/module_common.py#L116
from ansible.module_utils.basic import *  # noqa
main()
