#!/usr/bin/env python3
"""
Setup script for analytics database tables.

This script creates the necessary database tables for analytics metrics storage,
including time-series tables with optional TimescaleDB partitioning.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import logging
from pathlib import Path

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment or construct from parts."""
    # Try direct DATABASE_URL first
    db_url = os.getenv('DATABASE_URL')
    
    if not db_url:
        # Construct from individual variables
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'postgres')
        database = os.getenv('DB_NAME', 'xenodex_phase2')
        
        db_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    return db_url


def parse_database_url(db_url):
    """Parse database URL to extract connection parameters."""
    # Handle Heroku-style postgres:// URLs
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    # Parse URL
    from urllib.parse import urlparse
    result = urlparse(db_url)
    
    return {
        'host': result.hostname,
        'port': result.port or 5432,
        'user': result.username,
        'password': result.password,
        'database': result.path.lstrip('/')
    }


def check_timescaledb_extension(conn):
    """Check if TimescaleDB extension is available."""
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM pg_available_extensions WHERE name = 'timescaledb'"
        )
        result = cur.fetchone()
        return result[0] > 0
    except Exception as e:
        logger.warning(f"Could not check for TimescaleDB: {e}")
        return False


def setup_database():
    """Set up analytics database tables."""
    # Get database connection
    db_url = get_database_url()
    conn_params = parse_database_url(db_url)
    
    logger.info(f"Connecting to database at {conn_params['host']}:{conn_params['port']}")
    
    try:
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if TimescaleDB is available
        has_timescale = check_timescaledb_extension(conn)
        if has_timescale:
            logger.info("TimescaleDB extension is available")
        else:
            logger.warning(
                "TimescaleDB extension not available. "
                "Tables will be created without time-series partitioning."
            )
        
        # Read and execute the schema file
        schema_path = Path(__file__).parent / 'analytics_schema.sql'
        if not schema_path.exists():
            logger.error(f"Schema file not found: {schema_path}")
            return False
        
        logger.info(f"Executing schema from {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute the schema
        try:
            cur.execute(schema_sql)
            logger.info("Analytics schema created successfully")
        except psycopg2.errors.DuplicateTable:
            logger.info("Some tables already exist, skipping creation")
        except Exception as e:
            logger.error(f"Error creating schema: {e}")
            raise
        
        # Verify tables were created
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'analytics_%'
            ORDER BY table_name;
        """)
        
        tables = cur.fetchall()
        logger.info(f"\nCreated/verified {len(tables)} analytics tables:")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        # Check if TimescaleDB hypertables were created
        if has_timescale:
            cur.execute("""
                SELECT hypertable_name 
                FROM timescaledb_information.hypertables 
                WHERE hypertable_name = 'analytics_metrics';
            """)
            hypertables = cur.fetchall()
            if hypertables:
                logger.info("\nTimescaleDB hypertables created:")
                for ht in hypertables:
                    logger.info(f"  - {ht[0]} (with automatic time-based partitioning)")
        
        # Create initial aggregation job (if using TimescaleDB)
        if has_timescale:
            try:
                cur.execute("""
                    SELECT add_continuous_aggregate_policy(
                        'analytics_metrics_hourly',
                        start_offset => INTERVAL '2 hours',
                        end_offset => INTERVAL '1 hour',
                        schedule_interval => INTERVAL '30 minutes',
                        if_not_exists => TRUE
                    );
                """)
                logger.info("TimescaleDB continuous aggregation policy created")
            except Exception as e:
                logger.warning(f"Could not create continuous aggregate policy: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()


def create_test_data():
    """Insert some test data for verification."""
    db_url = get_database_url()
    conn_params = parse_database_url(db_url)
    
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Insert test metric
        cur.execute("""
            INSERT INTO analytics_metrics 
            (service_name, metric_name, metric_value, session_id, participant_id, tags)
            VALUES 
            ('test_service', 'test_metric', 42.0, 'test-session-123', 'test-participant-1', 
             '{"test": true}');
        """)
        
        conn.commit()
        logger.info("Test data inserted successfully")
        
        # Query it back
        cur.execute("""
            SELECT id, service_name, metric_value, timestamp 
            FROM analytics_metrics 
            WHERE session_id = 'test-session-123';
        """)
        
        result = cur.fetchone()
        if result:
            logger.info(f"Test query successful: ID={result[0]}, timestamp={result[3]}")
        
    except Exception as e:
        logger.error(f"Test data creation failed: {e}")
    
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--test':
            logger.info("Setting up database with test data...")
            if setup_database():
                create_test_data()
        elif sys.argv[1] == '--help':
            print("Usage: python setup_database.py [--test]")
            print("  --test  Create test data after setting up tables")
            sys.exit(0)
    else:
        # Just set up the database
        if setup_database():
            logger.info("\nDatabase setup complete!")
            logger.info("Run with --test flag to create test data")
        else:
            sys.exit(1)
