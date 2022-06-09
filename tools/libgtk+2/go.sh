set -e
if [ "$CELLIFT_ENV_SOURCED" != "yes" ]
then
    echo "Pleas source cellift env.sh."
    exit 1
fi
root=gtk+-2.0.9
tar xf ${root}.tar.gz
cd ${root}
./configure --prefix=$PREFIX_CELLIFT gdktarget=linux-fb
make -j$CELLIFT_JOBS  
make -j$CELLIFT_JOBS install 
