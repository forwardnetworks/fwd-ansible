Docker instructions
========================

Building
----------------

If you have `fwd-ansible-[VERSION].tar` docker image file, skip this step. This step is to build docker image from
source code.

From the base directory, run below command. It should generate `fwd-ansible-[VERSION].tar` file.

    ./build.sh

Importing
----------------

    docker load -i fwd-ansible-[VERSION].tar

Running
-----------------

    docker run -it fwd-ansible:[VERSION] bash

