#!/bin/sh
# Inert visual/parser oracle; inspect without executing.
set -eu

readonly READY_LIMIT=40
mutable_count=3
label='--help is literal text'

show_status() {
    printf '%s: %s\n' "$label" "$1"
}

show_status "$READY_LIMIT"
date -u
printf '%s\n' '--help' "--" -
