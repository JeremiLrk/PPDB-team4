-- Migration: add achievement tracking columns to ladder_team
-- Run this once on an existing database; safe to skip if resetting via reset_db.py

ALTER TABLE ladder_team
    ADD COLUMN IF NOT EXISTS wins             INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS win_streak       INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS best_win_streak  INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS rank1_streak     INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS best_rank1_streak INT NOT NULL DEFAULT 0;
