mkdir -p build/aarch64 && cd build/aarch64
cmake -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++ ../..
make
