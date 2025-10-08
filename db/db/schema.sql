-- Advanced relational schema for MetaGPT backend
-- PostgreSQL-compatible

CREATE TABLE companies (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  domain TEXT UNIQUE,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  company_id INTEGER REFERENCES companies(id) ON DELETE SET NULL,
  email CITEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'member',
  is_admin BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE agents (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  profile TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE actions (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  UNIQUE(name)
);

CREATE TABLE workflows (
  id SERIAL PRIMARY KEY,
  company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE workflow_agents (
  workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  position SMALLINT NOT NULL,
  PRIMARY KEY (workflow_id, agent_id)
);

CREATE TABLE agent_actions (
  agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
  action_id INTEGER NOT NULL REFERENCES actions(id) ON DELETE CASCADE,
  PRIMARY KEY (agent_id, action_id)
);

CREATE TABLE workflow_runs (
  id BIGSERIAL PRIMARY KEY,
  workflow_id INTEGER NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  status TEXT NOT NULL DEFAULT 'running'
);

CREATE TABLE task_messages (
  id BIGSERIAL PRIMARY KEY,
  run_id BIGINT NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
  agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE SET NULL,
  step_key TEXT NOT NULL,
  content TEXT NOT NULL,
  priority SMALLINT NOT NULL DEFAULT 0,
  depends_on TEXT[] DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_users_company ON users(company_id);
CREATE INDEX idx_agents_company ON agents(company_id);
CREATE INDEX idx_workflows_company ON workflows(company_id);
CREATE INDEX idx_workflow_agents_position ON workflow_agents(workflow_id, position);
CREATE INDEX idx_task_messages_run ON task_messages(run_id);

-- Example seed for actions aligning with demo_workflow
INSERT INTO actions(name, description) VALUES
  ('ProductPlanning', 'Define product features and roadmap'),
  ('MarketingCampaign', 'Develop marketing campaigns'),
  ('SalesStrategy', 'Create sales strategies'),
  ('CustomerSupport', 'Plan customer support processes')
ON CONFLICT DO NOTHING;
