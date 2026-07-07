#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOWNLOAD_DIR="$ROOT_DIR/downloads"
QUERY_DIR="$ROOT_DIR/queries"
GT_DIR="$ROOT_DIR/ground_truth"
LOG_DIR="$ROOT_DIR/logs"

mkdir -p "$DOWNLOAD_DIR" "$QUERY_DIR" "$GT_DIR" "$LOG_DIR"

download_file() {
  local name="$1"
  local file_id="$2"
  local output="$3"

  if [[ -s "$output" ]]; then
    echo "[$(date '+%F %T')] skip existing $name: $output"
    return
  fi

  echo "[$(date '+%F %T')] download $name -> $output"
  if ! gdown --continue "https://drive.google.com/uc?id=${file_id}" -O "$output"; then
    echo "[$(date '+%F %T')] failed $name (${file_id})"
    return 1
  fi
}

download_folder() {
  local name="$1"
  local folder_id="$2"
  local output_dir="$3"

  echo "[$(date '+%F %T')] download folder $name -> $output_dir"
  if ! gdown --folder --continue "https://drive.google.com/drive/folders/${folder_id}" -O "$output_dir"; then
    echo "[$(date '+%F %T')] failed folder $name (${folder_id})"
    return 1
  fi
}

download_file "OpenData_USA" "1m9gR_kUESc5SWUh2DaxbfSHKTY3eI0h2" "$DOWNLOAD_DIR/datasets_USA.zip" || true

download_file "OpenData_Join_Query" "1ccvFrS8c2XXTnWX0hgnLSpyR4QclMN2B" "$QUERY_DIR/opendata_join_query.csv" || true
download_file "OpenData_Join_Ground_Truth" "1BDNM02If3j1lZOqjt_n-xt5ZFUuzkmpP" "$GT_DIR/opendata_join_ground_truth.csv" || true

download_file "OpenData_CAN" "19omiJuxxCibvRjCWsdrU-1hgTdCd2_q0" "$DOWNLOAD_DIR/datasets_CAN.zip" || true
download_file "OpenData_UK" "1jdl2WwzTxGwV1i2tsfpC-1r_xiA2qDrZ" "$DOWNLOAD_DIR/datasets_UK.zip" || true

echo "[$(date '+%F %T')] done"
