#!/bin/bash

# Find the process ID(s) for the Flask server running on all interfaces (0.0.0.0)
PIDS=$(lsof -t -iTCP -sTCP:LISTEN -P -n | grep python)

# Kill each process
for PID in $PIDS
do
  echo "Killing process ID $PID"
  kill -9 $PID
done


