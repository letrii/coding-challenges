#!/bin/sh

set -e

host="$1"
shift
cmd="$@"

until ping -c 1 "$host" > /dev/null 2>&1; do
  >&2 echo "Waiting for $host to be available..."
  sleep 1
done

>&2 echo "$host is available"
exec $cmd
