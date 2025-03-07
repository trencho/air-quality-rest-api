#!/bin/bash

hash_directory() {
  local directory="$1"
  local exclude_directory="$2"

  find "$directory" -type f ! -path "*/$exclude_directory/*" -print0 |
    LC_ALL=C sort -z |
    xargs -0 sha256sum |
    awk '{print $1}' |
    sha256sum |
    awk '{print $1}'
}
