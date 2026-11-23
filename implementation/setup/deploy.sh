#!/usr/bin/env bash
# Put this clone's current commit on the other VMs, from the generator VM.
#   bash setup/deploy.sh 10.128.0.20 10.128.0.21 10.128.0.22
# The commit travels as a git bundle, so the VMs need no GitHub access, and
# each VM ends up with a real clone, which the main-stage git check needs.
# Only committed code is sent. Run setup/provision.sh on a VM after its first
# deploy and after requirements.txt changes.
set -euo pipefail

if [ $# -eq 0 ]; then
  echo "usage: deploy.sh <vm address>..." >&2
  exit 2
fi
key="${PLB_SSH_KEY:-$HOME/.ssh/plb}"
repo=$(git rev-parse --show-toplevel)
commit=$(git -C "$repo" rev-parse HEAD)
bundle=$(mktemp --suffix=.bundle)
trap 'rm -f "$bundle"' EXIT
git -C "$repo" bundle create -q "$bundle" HEAD

for host in "$@"; do
  scp -i "$key" -o BatchMode=yes "$bundle" "plb@$host:plb.bundle"
  ssh -i "$key" -o BatchMode=yes "plb@$host" "set -e
    [ -d plb/.git ] || git clone -q plb.bundle plb
    git -C plb fetch -q ~/plb.bundle HEAD
    git -C plb checkout -q --detach $commit
    rm plb.bundle
    echo \"\$(hostname) is at \$(git -C plb rev-parse --short HEAD)\""
done
