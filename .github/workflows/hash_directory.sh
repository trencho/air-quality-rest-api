#!/bin/bash

hash_directory() {
  directory="$1"
  exclude_directory="$2"
  hash=""

  while IFS= read -r -d '' file; do
    # Exclude the specified directory if provided
    if [[ -n "$exclude_directory" && "$file" == *"$exclude_directory"* ]]; then
      continue
    fi

    # Calculate hash of each file
    file_hash=$(sha256sum "$file" | awk '{print $1}')
    hash="$hash$file_hash"
  done < <(find "$directory" -type f -print0 | LC_ALL=C sort -z)

  echo -n "$hash" | sha256sum | awk '{print $1}'
}
