-- Run this once to set up the database
-- mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS docvault CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE docvault;

CREATE TABLE IF NOT EXISTS documents (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    original_name VARCHAR(255)  NOT NULL,
    stored_name   VARCHAR(255)  NOT NULL UNIQUE,
    size_bytes    BIGINT        NOT NULL DEFAULT 0,
    mime_type     VARCHAR(120)  DEFAULT '',
    uploaded_at   DATETIME      NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
