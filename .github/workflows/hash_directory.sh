#!/bin/bash

hash_directory() {
  local directory="$1"
  shift
  local exclude_directories=("$@")

  # Start building the find command
  local find_command=(find "$directory" -type f)

  # Add exclusion paths
  for exclude in "${exclude_directories[@]}"; do
    find_command+=(! -path "*/$exclude/*")
  done

  # Execute the find command and hash files
  "${find_command[@]}" -print0 |
    LC_ALL=C sort -z |
    xargs -0 sha256sum |
    awk '{print $1}' |
    sha256sum |
    awk '{print $1}'
}
