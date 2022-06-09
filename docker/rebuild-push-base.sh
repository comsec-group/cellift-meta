set -e
IMAGE_TAG=registry.ethz.ch/comsec/hardware-information-flow-tracking/cellift-meta:cellift-tools-base-main
echo building $IMAGE_TAG
docker login registry.ethz.ch
docker build -f Dockerfile-base -t $IMAGE_TAG .
echo "To push image, do:"
echo "docker push $IMAGE_TAG"

