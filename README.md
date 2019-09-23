[Forward Enterprise](https://www.forwardnetworks.com/network-automation-software/) documents, searches, verifies, and predicts
the behavior of your network by creating an always-accurate software copy of your entire network infrastructure for both on-prem and cloud.

This repository includes sample Ansible modules to automate interactions with a Forward Enterprise server:

- forward_check:     Add/Remove/Verify a provided check
- forward_network:   Get networks from Forward instance
- forward_snapshot:  Collect a new snapshot for a given network, or upload a previously saved one

The instructions below explain how to install the main pre-req (the fwd-api Python bindings),
then set up a Forward properties file.

DISCLAIMER:
All the code in this repository is distributed with no warranty and no support from Forward Networks.

# Install the ```fwd_api``` python module

## Get the fwd-api submodules

git submodule update --init --recursive
cd deps/fwd-api

## Install the python module

You can either scope the installation of the ```fwd_api``` python
module to a virtual environment or install it system-wide.
The first is recommended.

### Installing in a virtual env
Get virtualenv

   pip install virtualenv

From the ```fwd-api``` directory, create a virtual environment for Python:

   virtualenv fwd_virtual

This should produce a folder named ```fwd_virtual```.
Use the virtual environment by calling:

   source fwd_virtual/bin/activate

From this same terminal, follow the instructions in the system-wide
instructions.

### Installing system-wide
fwd-api depends on python's request module. To get it, use pip:

   pip install requests

After installing requests, use ```setup.py``` to install the fwd_api
module; from the fwd-api directory, run:

   python setup.py install

Return to the original top-level repository directory:

   cd ../..

# Set up local properties file

Set up properties file from the sample

    cp fwd-ansible.properties.sample fwd-ansible.properties

Fill in the content to match your Forward instance and network:

url = <Forward Enterprise url>
username = <username>
password = <password>
network_name = <Network name>

Forward modules may take a 'properties_file_path' value to enable overriding
the default location:

        properties_file_path: <path to properties file>

Note:
If a property is both in the properties file and passed to an Ansible module,
the property passed to the Ansible module will take a higher priority.

# Try out examples

Check the playbooks in the examples directory to get started.

For example, we recommend:

     ansible-playbook examples/networks.yml

... to see a list of networks for your user account.

# Provide Feedback

If you're interested in using these modules or have any feedback, please let us know at info@forwardnetworks.com.

We're making this code available to enable early feedback, so that these modules might
be more actively developed, tested, and even officially supported.
