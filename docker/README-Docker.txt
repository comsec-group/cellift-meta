Lightning Introduction To Docker And How CellIFT Uses It

What is docker: system that can build and run containers.

What is a container: Illusion of a seperate computer system, isolated
from the main one (but you can introduce exceptions to the isolation).
This isolation is achieved by employing a number of Linux kernel
features: namespaces (isolation by limiting visible resources, e.g.
filesystem view) and cgroups (control groups, limits resource usage).

What is an image: the filesystem state of a container when it starts
to run. An image is a thing that sits there, the container is the thing
that runs (starting from an image).

How is an image built: using a Dockerfile, which is a recipe to build
a container image. This is done using the 'docker build <environment>'
command. An <environment> is the context, which includes a Dockerfile,
on which docker build operates. A container starts empty. Then you
specify a FROM command, which specifies how the universe is created.

How is the CellIFT tools image is built: a very specific Ubuntu image
which comes from a container registry is specified in FROM. Every
command after that creates a new image layer to add to the base
image. These commands are cacheable and can re-use previously created
image layers. To build we COPY files from the context (cellift-meta repo)
into our container. Then we execute some RUN commands to build the tools.
Each RUN commands creates a new image layer (again, cacheable as long
as the previous images and the Dockerfile commands haven't changed).
Finally, we create a image which contains the CellIFT tools in the prefix.

How do I use the CellIFT tools image: The tools image that is automatically
built by the CellIFT ETH Gitlab CI is stored in the ETH Gitlab container
registry. To retrieve and run it:
$ docker login registry.ethz.ch
$ docker pull registry.ethz.ch/comsec/hardware-information-flow-tracking/cellift-meta:cellift-tools-main
$ docker run -it registry.ethz.ch/comsec/hardware-information-flow-tracking/cellift-meta:cellift-tools-main
