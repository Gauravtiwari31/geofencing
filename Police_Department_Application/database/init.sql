-- Police SEDI Database Schema
-- Minimal incident mirror and audit tables

-- Incidents table (minimal mirror from MoD)
CREATE TABLE IF NOT EXISTS incidents (
    alert_id BIGINT PRIMARY KEY,
    tourist_id VARCHAR(36) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('SOS', 'RED_ZONE', 'DISCONNECTION')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_status VARCHAR(20) NOT NULL CHECK (last_status IN ('ACTIVE', 'ACKNOWLEDGED', 'RESOLVED')),
    last_update_at TIMESTAMP WITH TIME ZONE NOT NULL,
    location JSONB,
    score_band VARCHAR(10) CHECK (score_band IN ('HIGH', 'MEDIUM', 'LOW')),
    details TEXT
);

-- Actions audit table
CREATE TABLE IF NOT EXISTS actions (
    id SERIAL PRIMARY KEY,
    alert_id BIGINT REFERENCES incidents(alert_id) ON DELETE CASCADE,
    officer_id VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('ACK', 'VIEW', 'NOTE')),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    note TEXT
);

-- Application settings
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(50) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(last_status);
CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_type ON incidents(type);
CREATE INDEX IF NOT EXISTS idx_actions_alert ON actions(alert_id);
CREATE INDEX IF NOT EXISTS idx_actions_officer ON actions(officer_id);

-- Insert default settings
INSERT INTO settings (key, value) VALUES 
    ('app_version', '1.0.0'),
    ('last_stream_sync', '1970-01-01T00:00:00Z')
ON CONFLICT (key) DO NOTHING;

-- Sample data for testing (can be removed in production)
INSERT INTO incidents (alert_id, tourist_id, type, created_at, last_status, last_update_at, location, score_band, details) VALUES
    (123456, 'b1d0b691-1234-5678-9abc-123456789012', 'SOS', NOW() - INTERVAL '5 minutes', 'ACTIVE', NOW() - INTERVAL '5 minutes', '{"lat": 40.7128, "lng": -74.0060, "accuracy": 10}', 'HIGH', 'Emergency SOS signal received'),
    (123457, 'c2e1c7a2-2345-6789-abcd-234567890123', 'RED_ZONE', NOW() - INTERVAL '10 minutes', 'ACKNOWLEDGED', NOW() - INTERVAL '2 minutes', '{"lat": 40.7589, "lng": -73.9851, "accuracy": 15}', 'MEDIUM', 'Tourist entered restricted area'),
    (123458, 'd3f2d8b3-3456-789a-bcde-345678901234', 'DISCONNECTION', NOW() - INTERVAL '15 minutes', 'ACTIVE', NOW() - INTERVAL '15 minutes', '{"lat": 40.7506, "lng": -73.9938, "accuracy": 20}', 'LOW', 'Device disconnected unexpectedly')
ON CONFLICT (alert_id) DO NOTHING;
