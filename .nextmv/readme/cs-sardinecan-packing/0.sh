export OS=linux
export ARCH=x64
dotnet publish --os $OS --arch $ARCH --self-contained
cp -v bin/Release/net8.0/$OS-$ARCH/publish/cs-sardinecan-packing ./main
