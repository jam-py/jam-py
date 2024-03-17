#!/usr/bin/env bash

if [ -d /app ]; then
  echo "Directory /app exists."
else
  mkdir /app
  echo "##########################################################"
  echo "## Be carefull, /app folder seems not being persistent, ##"
  echo "## Your modifications won't be stored.                  ##"
  echo "##########################################################"
fi

cd /app

if [ -f /app/server.py ]; then
    echo "File /app/server.py exists."
else
    echo "Installing demo into /app folder."
    cp -R /opt/jam-py/demo/* .
fi

./server.py
