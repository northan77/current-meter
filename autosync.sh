#!/bin/bash

cd /home/tim/Projects/current-meter || exit 1

git add .

if ! git diff --cached --quiet; then
    git commit -m "autosave"
    git push
fi
