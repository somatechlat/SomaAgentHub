-- PostgreSQL Schema for Capsule Marketplace
-- Stores capsule catalog, versions, and marketplace metadata

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Capsule publishers (users/orgs who publish capsules)
CREATE TABLE publishers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    reputation_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_publishers_email ON publishers(email);
CREATE INDEX idx_publishers_verified ON publishers(verified);

-- Capsules (marketplace listings)
CREATE TABLE capsules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publisher_id UUID NOT NULL REFERENCES publishers(id),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(100),
    tags TEXT[], -- Array of tags for discovery
    visibility VARCHAR(20) DEFAULT 'public', -- public, private, unlisted
    status VARCHAR(20) DEFAULT 'draft', -- draft, published, deprecated
    
    -- Pricing
    price_model VARCHAR(20) DEFAULT 'free', -- free, paid, usage_based
    base_price DECIMAL(10, 2) DEFAULT 0,
    
    -- Metrics
    total_installs INTEGER DEFAULT 0,
    active_installs INTEGER DEFAULT 0,
    total_downloads INTEGER DEFAULT 0,
    average_rating DECIMAL(3, 2) DEFAULT 0,
    total_reviews INTEGER DEFAULT 0,
    
    -- Performance ranking (calculated periodically)
    performance_score DECIMAL(5, 2) DEFAULT 0,
    quality_score DECIMAL(5, 2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    
    UNIQUE(publisher_id, slug)
);

CREATE INDEX idx_capsules_publisher ON capsules(publisher_id);
CREATE INDEX idx_capsules_slug ON capsules(slug);
CREATE INDEX idx_capsules_status ON capsules(status);
CREATE INDEX idx_capsules_category ON capsules(category);
CREATE INDEX idx_capsules_performance ON capsules(performance_score DESC);
CREATE INDEX idx_capsules_tags ON capsules USING GIN(tags);

-- Capsule versions
CREATE TABLE capsule_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capsule_id UUID NOT NULL REFERENCES capsules(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL, -- semver: 1.2.3
    changelog TEXT,
    
    -- Code storage
    code_hash VARCHAR(64) NOT NULL, -- SHA256 of code
    code_url TEXT NOT NULL, -- S3/storage URL
    signature TEXT, -- Cryptographic signature
    
    -- Requirements
    min_python_version VARCHAR(20),
    dependencies JSONB DEFAULT '{}', -- pip requirements
    
    -- Resource limits
    max_memory_mb INTEGER DEFAULT 512,
    max_cpu_cores DECIMAL(3, 2) DEFAULT 1,
    max_execution_time_sec INTEGER DEFAULT 300,
    
    -- Security
    permissions JSONB DEFAULT '[]', -- Required permissions
    sandboxed BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    size_bytes BIGINT,
    downloads INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(capsule_id, version)
);

CREATE INDEX idx_capsule_versions_capsule ON capsule_versions(capsule_id);
CREATE INDEX idx_capsule_versions_version ON capsule_versions(version);
CREATE INDEX idx_capsule_versions_created ON capsule_versions(created_at DESC);

-- Capsule installations (user installations)
CREATE TABLE capsule_installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capsule_id UUID NOT NULL REFERENCES capsules(id),
    version_id UUID NOT NULL REFERENCES capsule_versions(id),
    user_id VARCHAR(255) NOT NULL,
    
    status VARCHAR(20) DEFAULT 'active', -- active, paused, uninstalled
    
    -- Usage tracking
    total_executions INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP,
    
    installed_at TIMESTAMP DEFAULT NOW(),
    uninstalled_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_installations_user ON capsule_installations(user_id);
CREATE INDEX idx_installations_capsule ON capsule_installations(capsule_id);
CREATE INDEX idx_installations_status ON capsule_installations(status);

-- Capsule reviews
CREATE TABLE capsule_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capsule_id UUID NOT NULL REFERENCES capsules(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(255),
    review_text TEXT,
    
    -- Moderation
    verified_purchase BOOLEAN DEFAULT FALSE,
    flagged BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(capsule_id, user_id)
);

CREATE INDEX idx_reviews_capsule ON capsule_reviews(capsule_id);
CREATE INDEX idx_reviews_rating ON capsule_reviews(rating);
CREATE INDEX idx_reviews_created ON capsule_reviews(created_at DESC);

-- Capsule execution logs (for analytics)
CREATE TABLE capsule_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capsule_id UUID NOT NULL REFERENCES capsules(id),
    version_id UUID NOT NULL REFERENCES capsule_versions(id),
    installation_id UUID REFERENCES capsule_installations(id),
    user_id VARCHAR(255) NOT NULL,
    
    -- Execution metadata
    status VARCHAR(20) NOT NULL, -- success, error, timeout
    execution_time_ms INTEGER,
    memory_used_mb INTEGER,
    cpu_used_percent DECIMAL(5, 2),
    
    -- Error tracking
    error_type VARCHAR(100),
    error_message TEXT,
    
    -- Billing
    compute_cost DECIMAL(10, 6),
    
    executed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_executions_capsule ON capsule_executions(capsule_id);
CREATE INDEX idx_executions_user ON capsule_executions(user_id);
CREATE INDEX idx_executions_status ON capsule_executions(status);
CREATE INDEX idx_executions_executed ON capsule_executions(executed_at DESC);

-- Marketplace transactions (for paid capsules)
CREATE TABLE marketplace_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capsule_id UUID NOT NULL REFERENCES capsules(id),
    buyer_id VARCHAR(255) NOT NULL,
    publisher_id UUID NOT NULL REFERENCES publishers(id),
    
    transaction_type VARCHAR(20) NOT NULL, -- purchase, subscription, usage_fee
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Payment gateway
    stripe_payment_id VARCHAR(255),
    stripe_charge_id VARCHAR(255),
    
    status VARCHAR(20) DEFAULT 'pending', -- pending, completed, refunded, failed
    
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_transactions_buyer ON marketplace_transactions(buyer_id);
CREATE INDEX idx_transactions_publisher ON marketplace_transactions(publisher_id);
CREATE INDEX idx_transactions_status ON marketplace_transactions(status);
CREATE INDEX idx_transactions_created ON marketplace_transactions(created_at DESC);

-- Featured capsules (curated by platform)
CREATE TABLE featured_capsules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    capsule_id UUID NOT NULL REFERENCES capsules(id),
    featured_position INTEGER, -- 1 = top spot
    start_date TIMESTAMP DEFAULT NOW(),
    end_date TIMESTAMP,
    
    UNIQUE(capsule_id, start_date)
);

CREATE INDEX idx_featured_position ON featured_capsules(featured_position);
CREATE INDEX idx_featured_dates ON featured_capsules(start_date, end_date);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_publishers_updated_at BEFORE UPDATE ON publishers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_capsules_updated_at BEFORE UPDATE ON capsules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_installations_updated_at BEFORE UPDATE ON capsule_installations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View: Popular capsules (for discovery)
CREATE VIEW popular_capsules AS
SELECT 
    c.*,
    p.display_name as publisher_name,
    p.verified as publisher_verified,
    cv.version as latest_version
FROM capsules c
JOIN publishers p ON c.publisher_id = p.id
LEFT JOIN LATERAL (
    SELECT version FROM capsule_versions 
    WHERE capsule_id = c.id 
    ORDER BY created_at DESC 
    LIMIT 1
) cv ON TRUE
WHERE c.status = 'published'
ORDER BY c.performance_score DESC, c.total_installs DESC;

-- View: Trending capsules (last 7 days)
CREATE VIEW trending_capsules AS
SELECT 
    c.*,
    COUNT(DISTINCT ce.id) as executions_last_week,
    COUNT(DISTINCT ci.id) as installs_last_week
FROM capsules c
LEFT JOIN capsule_executions ce ON c.id = ce.capsule_id 
    AND ce.executed_at > NOW() - INTERVAL '7 days'
LEFT JOIN capsule_installations ci ON c.id = ci.capsule_id 
    AND ci.installed_at > NOW() - INTERVAL '7 days'
WHERE c.status = 'published'
GROUP BY c.id
ORDER BY installs_last_week DESC, executions_last_week DESC;

-- Seed data: Demo publishers
INSERT INTO publishers (name, display_name, email, verified) VALUES
    ('somaagent', 'SomaAgent Official', 'team@somaagent.io', TRUE),
    ('ai-tools', 'AI Tools Collective', 'hello@aitools.dev', TRUE),
    ('indie-dev', 'Indie Developer', 'dev@example.com', FALSE);

-- Seed data: Demo capsules
INSERT INTO capsules (publisher_id, name, slug, description, category, tags, status, published_at) 
SELECT 
    p.id,
    'Code Reviewer',
    'code-reviewer',
    'Automatically reviews code for best practices and potential bugs',
    'development',
    ARRAY['code-review', 'quality', 'automation'],
    'published',
    NOW() - INTERVAL '30 days'
FROM publishers p WHERE p.name = 'somaagent';

INSERT INTO capsules (publisher_id, name, slug, description, category, tags, status, published_at)
SELECT 
    p.id,
    'Data Analyzer',
    'data-analyzer',
    'Analyzes datasets and generates insights with visualizations',
    'analytics',
    ARRAY['data', 'analytics', 'visualization'],
    'published',
    NOW() - INTERVAL '15 days'
FROM publishers p WHERE p.name = 'ai-tools';
