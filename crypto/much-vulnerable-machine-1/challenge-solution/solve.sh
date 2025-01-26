#!/bin/sh

rm -rf tmp

cp -r ../challenge-src/api tmp
cp solve.py tmp

cd tmp && git clone https://github.com/jvdsn/crypto-attacks/ ./cryptoattacks

python3 ./solve.py

cd ..

rm -rf tmp