-- Cria users
CREATE USER orchestrator WITH PASSWORD 'orchestrator_pw';
CREATE USER catalog       WITH PASSWORD 'catalog_pw';
CREATE USER approval      WITH PASSWORD 'approval_pw';
CREATE USER provisioning  WITH PASSWORD 'provisioning_pw';

-- Cria databases (owner = user homônimo)
CREATE DATABASE orchestrator_db OWNER orchestrator;
CREATE DATABASE catalog_db       OWNER catalog;
CREATE DATABASE approval_db      OWNER approval;
CREATE DATABASE provisioning_db  OWNER provisioning;

-- Garante que cada user só vê seu DB (revoga CONNECT dos outros)
REVOKE CONNECT ON DATABASE orchestrator_db FROM PUBLIC;
REVOKE CONNECT ON DATABASE catalog_db       FROM PUBLIC;
REVOKE CONNECT ON DATABASE approval_db      FROM PUBLIC;
REVOKE CONNECT ON DATABASE provisioning_db  FROM PUBLIC;

GRANT CONNECT ON DATABASE orchestrator_db TO orchestrator;
GRANT CONNECT ON DATABASE catalog_db       TO catalog;
GRANT CONNECT ON DATABASE approval_db      TO approval;
GRANT CONNECT ON DATABASE provisioning_db  TO provisioning;
