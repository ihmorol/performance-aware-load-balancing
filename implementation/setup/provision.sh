#!/usr/bin/env bash
# Set up one VM for its role. Safe to run again after a code or package change.
#   bash ~/plb/implementation/setup/provision.sh gen          # generator VM
#   bash ~/plb/implementation/setup/provision.sh dispatcher   # dispatcher VM
#   bash ~/plb/implementation/setup/provision.sh worker       # both worker VMs
# Run it as the plb user, with the code already at ~/plb (setup/deploy.sh).
set -euo pipefail

role=${1:-}
case "$role" in
  gen|dispatcher|worker) ;;
  *) echo "usage: provision.sh gen|dispatcher|worker" >&2; exit 2 ;;
esac
if [ "$(id -un)" != plb ]; then
  echo "run this as the plb user; the units and the sudo rule name that user" >&2
  exit 2
fi
impl="$HOME/plb/implementation"

sudo apt-get update -q
sudo apt-get install -y -q python3.12-venv git
# Background jobs that could wake up during a run.
sudo systemctl disable --now unattended-upgrades.service apt-daily.timer apt-daily-upgrade.timer man-db.timer || true

mkdir -p "$HOME/plb-run"
[ -d "$impl/.venv" ] || python3.12 -m venv "$impl/.venv"
"$impl/.venv/bin/pip" install -q -r "$impl/requirements.txt"
"$impl/.venv/bin/pip" install -q -e "$impl" --no-deps

if [ "$role" != gen ]; then
  unit="plb-$role.service"
  sudo install -m 0644 "$impl/setup/$unit" "/etc/systemd/system/$unit"
  sudo install -m 0440 "$impl/setup/plb-sudoers" /etc/sudoers.d/plb
  sudo visudo -cf /etc/sudoers.d/plb
  sudo systemctl daemon-reload
fi
echo "provisioned $(hostname) as $role"
