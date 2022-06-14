set -e
IMAGE_TAG=ethcomsec/cellift:cellift-tools-base-main
echo building $IMAGE_TAG
docker login registry-1.docker.io
docker build -f Dockerfile-base -t $IMAGE_TAG .
echo "To push image, do:"
echo "docker push $IMAGE_TAG"

