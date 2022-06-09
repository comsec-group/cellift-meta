set -e
if [ "$CELLIFT_ENV_SOURCED" != "yes" ]
then
    echo "Please source cellift env.sh."
    exit 1
fi
root=gcc-11.2.0
objdir=${root}.obj
tar xf ${root}.tar.xz
( cd ${root} && sh contrib/download_prerequisites ) 
mkdir -p $objdir
cd $objdir
../$root/configure --prefix=$PREFIX_CELLIFT --enable-languages=c,c++ --disable-multilib
make -j$CELLIFT_JOBS bootstrap 
make -j$CELLIFT_JOBS install 
