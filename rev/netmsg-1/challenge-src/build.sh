#!/bin/bash

# use go1.22 for better rev-ability i guess lol

for goos in linux windows darwin; do
	for goarch in amd64 arm64 386; do
		if [[ $goos == darwin ]] && [[ $goarch == 386 ]]; then
			# skip
			continue
		fi
		GOOS=$goos GOARCH=$goarch go build -C client -trimpath -o ../../challenge-handout/netmsg_${goos}_${goarch}
	done
done
