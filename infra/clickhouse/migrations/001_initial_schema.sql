-- ClickHouse Migration 001: Initial Schema
-- Sprint-7: Analytics tables for SomaAgent
--
-- Run this migration to create the initial database schema

-- Database setup
CREATE DATABASE IF NOT EXISTS somaagent;

USE somaagent;

-- Migration tracking table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version UInt32,
    description String,
    applied_at DateTime64(3) DEFAULT now64(3),
    success Boolean DEFAULT true
) ENGINE = MergeTree()
ORDER BY version;

-- Record this migration
INSERT INTO schema_migrations (version, description) VALUES (1, 'Initial schema with analytics tables');

-- Load main schema
-- Note: This file should be run after schema.sql is loaded
-- The schema.sql file contains the full table definitions
