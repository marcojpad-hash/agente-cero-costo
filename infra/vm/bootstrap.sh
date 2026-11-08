#!/usr/bin/env bash
set -Eeuo pipefail
# Ubuntu/Debian. Ejecutar como root. Nunca copiar claves privadas a la VM.
if [[ "${EUID}" -ne 0 ]]; then echo "ERROR: ejecuta como root (sudo)." >&2; exit 1; fi
KEY_DIR="${KEY_DIR:-/root/agent-keys}"
AGENT_USERS="${AGENT_USERS:-}"
SHARED_ROOT="${SHARED_ROOT:-/srv/agentes}"
GROUP_NAME="agentes"
if [[ -z "$AGENT_USERS" ]]; then echo "ERROR: define AGENT_USERS, por ejemplo chatgpt,muse." >&2; exit 1; fi
if [[ ! -d "$KEY_DIR" ]]; then echo "ERROR: falta $KEY_DIR con claves públicas <usuario>.pub." >&2; exit 1; fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y openssh-server git python3 python3-venv rsync acl
getent group "$GROUP_NAME" >/dev/null || groupadd "$GROUP_NAME"
install -d -o root -g root -m 0700 "$KEY_DIR"
install -d -o root -g "$GROUP_NAME" -m 2770 "$SHARED_ROOT/compartido" "$SHARED_ROOT/repos"
setfacl -m "g:$GROUP_NAME:rwx,m:rwx" "$SHARED_ROOT/compartido" "$SHARED_ROOT/repos"
setfacl -d -m "u::rwx,g::rwx,g:$GROUP_NAME:rwx,m:rwx,o::---" "$SHARED_ROOT/compartido" "$SHARED_ROOT/repos"
created=0; skipped=0
IFS=',' read -r -a users <<< "$AGENT_USERS"
for raw in "${users[@]}"; do
  user="$(printf '%s' "$raw" | xargs)"
  [[ -z "$user" ]] && continue
  if [[ ! "$user" =~ ^[a-z_][a-z0-9_-]{0,31}$ ]]; then echo "OMITIDO: nombre inválido: $user" >&2; skipped=$((skipped+1)); continue; fi
  pub="$KEY_DIR/$user.pub"
  if [[ ! -s "$pub" ]]; then echo "OMITIDO: falta $pub"; skipped=$((skipped+1)); continue; fi
  if ! id "$user" >/dev/null 2>&1; then useradd --create-home --shell /bin/bash --groups "$GROUP_NAME" "$user"; else usermod --append --groups "$GROUP_NAME" "$user"; fi
  home="$(getent passwd "$user" | cut -d: -f6)"
  install -d -o "$user" -g "$user" -m 0700 "$home/.ssh"
  install -o "$user" -g "$user" -m 0600 "$pub" "$home/.ssh/authorized_keys"
  created=$((created+1)); echo "OK: cuenta $user configurada."
done
systemctl enable --now ssh
systemctl reload ssh || systemctl restart ssh
echo "Cuentas configuradas: $created; omitidas: $skipped"
echo "Compartido: $SHARED_ROOT/compartido ; repos: $SHARED_ROOT/repos"
echo "No se modificó la política global SSH ni el firewall; restringe SSH en el proveedor antes de exponerlo."
