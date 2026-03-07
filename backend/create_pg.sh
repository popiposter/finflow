#!/bin/bash
docker run \
  --name pg-test \
  --rm \
  -e POSTGRES_USER=finflow \
  -e POSTGRES_PASSWORD=finflow \
  -e POSTGRES_DB=finflow \
  -p 5432:5432 \
  -d postgres:16-alpine sh -c "cp /var/lib/postgresql/data/pg_hba.conf /var/lib/postgresql/data/pg_hba.conf.bak && cat > /var/lib/postgresql/data/pg_hba.conf << 'EOF'
# PostgreSQL Client Authentication Configuration File

# "local" is for Unix domain socket connections only
local   all             all                                     trust
# IPv4 local connections:
host    all             all             127.0.0.1/32            trust
# IPv6 local connections:
host    all             all             ::1/128                 trust
# Allow replication connections from localhost, by a user with the
# replication privilege.
local   replication     all                                     trust
host    replication     all             127.0.0.1/32            trust
host    replication     all             ::1/128                 trust

# Docker internal network (from host via port forwarding)
host all all 172.17.0.0/16 trust

# Local network from Windows host (Docker gateway)
host all all 127.0.0.1/32 trust
EOF
exec docker-entrypoint.sh postgres"
