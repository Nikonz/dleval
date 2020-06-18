# dleval
New and fancy exercises evaluation system for the "Deep Learning" course!

## Prerequisites
You need **Python3**, **Docker** and python library **Robobrowser**:
* Instructions for installing **Docker** are available on the official docker website: https://docs.docker.com/engine/install/.
* Instructions for installing **Robobrowser** are available on https://robobrowser.readthedocs.io/en/latest/installation.html.

Additionally you may need to install some other libraries, e.g. **yaml**:

` pip install yaml`

## Building

By default docker requires root access, so it is convinient to be able to manage Docker as a non-root user. You can find the instructions on https://docs.docker.com/engine/install/linux-postinstall/. Please be aware of the warnings mentioned there.

Run the following command to install Anaconda image to Docker:

` docker pull continuumio/anaconda3 `

Now create a Docker image for further submissions evaluation. It includes all packages from the Anaconda image plus pytorch and torchvision. To install more packages you must specify them in Dockerfile.dleval.

` docker build -t dleval -f eval/docker/Dockerfile.dleval . `

## Running

Create a **config.yml** and put there your credentials for the CAS system and the course id. There is **config.yml.example**, which you can use as an example. If you explicitly specify the parameter *interval*, make sure its value is at least 120 (sec, = 2 min). It is important due to the fact that some submissions might be retested to prevent the consequences of possible race conditions between a student and an evaluator.

You need to put evaluating code for a moodle assignment into *\`eval/data/folder'*, where instead of *\`folder\`* you must use either assignment id (is a part of an assignment URL) or assignment name. Your code must not contain any subfolders and have a **eval.py** with a evaluate() function as an entry point. evalute() must return a dictionary, where keys are criterias and values are points. You can find an example in *\`eval/data/EXAMPLE'*. Make sure that the maximum number of total points match the number specified in moodle.

To run:

` python dleval.py `

For help:

` python dleval.py -h `


