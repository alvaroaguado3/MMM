#!/usr/bin/env python3
"""
Database initialization script for Meridian MMM Platform.
Creates necessary tables and schema for the platform.
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys
import os

# Database configuration
DB_NAME = "meridian_mmm"
DB_USER = os.getenv("POSTGRES_USER", os.getenv("USER"))
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")


def create_schema():
    """Create database tables and schema."""
    
    schema_sql = """
    -- Media data table
    CREATE TABLE IF NOT EXISTS media_data (
        id SERIAL PRIMARY KEY,
        date DATE NOT NULL,
        channel VARCHAR(100) NOT NULL,
        spend DECIMAL(12, 2),
        impressions BIGINT,
        clicks INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Sales/KPI data table
    CREATE TABLE IF NOT EXISTS sales_data (
        id SERIAL PRIMARY KEY,
        date DATE NOT NULL,
        revenue DECIMAL(12, 2),
        units_sold INTEGER,
        region VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Model runs table
    CREATE TABLE IF NOT EXISTS model_runs (
        id SERIAL PRIMARY KEY,
        run_name VARCHAR(255) NOT NULL,
        config JSONB,
        status VARCHAR(50) DEFAULT 'pending',
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        results JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Budget optimization results table
    CREATE TABLE IF NOT EXISTS optimization_results (
        id SERIAL PRIMARY KEY,
        model_run_id INTEGER REFERENCES model_runs(id),
        scenario_name VARCHAR(255),
        total_budget DECIMAL(12, 2),
        allocations JSONB,
        predicted_revenue DECIMAL(12, 2),
        roi DECIMAL(10, 4),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_media_date ON media_data(date);
    CREATE INDEX IF NOT EXISTS idx_media_channel ON media_data(channel);
    CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_data(date);
    CREATE INDEX IF NOT EXISTS idx_model_runs_status ON model_runs(status);
    """
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        
        cursor = conn.cursor()
        
        print(f"Connected to database '{DB_NAME}'")
        print("Creating schema...")
        
        # Execute schema creation
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✓ Schema created successfully!")
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\nCreated tables ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Database initialization complete!")
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Database error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}", file=sys.stderr)
        return False


def main():
    """Main execution function."""
    print("=" * 60)
    print("Meridian MMM Platform - Database Initialization")
    print("=" * 60)
    print(f"\nDatabase: {DB_NAME}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"User: {DB_USER}\n")
    
    success = create_schema()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
