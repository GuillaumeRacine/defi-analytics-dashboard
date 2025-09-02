#!/usr/bin/env python3
"""
Initialize DuckDB database with schema using contract addresses as identifiers.
"""

import os
import duckdb
from pathlib import Path
from src.schema import create_all_tables, example_queries

def init_database():
    """Initialize the DuckDB database with all tables"""
    
    # Create directories if they don't exist
    db_dir = Path("data/duckdb")
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Database path
    db_path = db_dir / "defillama.db"
    
    print(f"🗄️  Initializing database at: {db_path}")
    
    # Connect to database (creates if doesn't exist)
    conn = duckdb.connect(str(db_path))
    
    try:
        # Create all tables
        create_all_tables(conn)
        
        # Verify tables were created
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   • {table[0]}")
        
        # Insert some example token data
        print("\n➕ Adding example tokens...")
        example_tokens = [
            ("ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "ethereum", 
             "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "USDC", "USD Coin", 6),
            ("ethereum:0xdac17f958d2ee523a2206206994597c13d831ec7", "ethereum",
             "0xdac17f958d2ee523a2206206994597c13d831ec7", "USDT", "Tether", 6),
            ("ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "ethereum",
             "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2", "WETH", "Wrapped Ether", 18),
            ("ethereum:0x6b175474e89094c44da98b954eedeac495271d0f", "ethereum",
             "0x6b175474e89094c44da98b954eedeac495271d0f", "DAI", "Dai Stablecoin", 18),
        ]
        
        for token_data in example_tokens:
            try:
                conn.execute("""
                    INSERT INTO tokens (contract_id, chain, contract_address, symbol, name, decimals)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (contract_id) DO NOTHING
                """, token_data)
                print(f"   ✅ Added {token_data[3]}")
            except Exception as e:
                print(f"   ⚠️  Skipped {token_data[3]}: {e}")
        
        # Add example LP pools
        print("\n➕ Adding example LP pools...")
        example_pools = [
            ("ethereum:0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", "ethereum",
             "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640", "uniswap-v3", "concentrated",
             '["ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"]',
             '["USDC", "WETH"]', None, 500, 10),
            ("ethereum:0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8", "ethereum",
             "0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8", "uniswap-v3", "concentrated",
             '["ethereum:0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "ethereum:0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"]',
             '["USDC", "WETH"]', None, 3000, 60),
        ]
        
        for pool_data in example_pools:
            try:
                conn.execute("""
                    INSERT INTO lp_pools (pool_contract_id, chain, pool_address, protocol, 
                                         pool_type, token_addresses, token_symbols, token_weights,
                                         fee_tier, tick_spacing)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (pool_contract_id) DO NOTHING
                """, pool_data)
                fee = pool_data[7] / 10000 if pool_data[7] else 0
                print(f"   ✅ Added Uniswap V3 pool ({fee:.2f}% fee)")
            except Exception as e:
                print(f"   ⚠️  Skipped pool: {e}")
        
        # Commit changes
        conn.commit()
        
        # Show example queries
        print("\n📝 Example Queries:")
        queries = example_queries()
        for name, query in list(queries.items())[:2]:
            print(f"\n{name}:")
            print(f"   {query[:100]}...")
        
        print("\n✅ Database initialization complete!")
        
        # Return connection for further use
        return conn
        
    except Exception as e:
        print(f"❌ Error during initialization: {e}")
        conn.close()
        raise
    
    finally:
        # Don't close connection - return it for use
        pass


def verify_database():
    """Verify database is properly set up"""
    db_path = Path("data/duckdb/defillama.db")
    
    if not db_path.exists():
        print("❌ Database not found. Run init_database() first.")
        return False
    
    conn = duckdb.connect(str(db_path))
    
    try:
        # Check tables
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"📊 Found {len(tables)} tables")
        
        # Check token count
        token_count = conn.execute("SELECT COUNT(*) FROM tokens").fetchone()[0]
        print(f"🪙  Found {token_count} tokens")
        
        # Check pool count
        pool_count = conn.execute("SELECT COUNT(*) FROM lp_pools").fetchone()[0]
        print(f"🏊  Found {pool_count} LP pools")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying database: {e}")
        return False
    
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("🗄️  DuckDB Database Initialization")
    print("=" * 60)
    
    # Initialize database
    conn = init_database()
    
    # Verify setup
    print("\n" + "=" * 60)
    print("🔍 Verifying database setup...")
    print("=" * 60)
    verify_database()
    
    # Close connection
    conn.close()
    
    print("\n💡 Next steps:")
    print("   1. Run 'python test_api.py' to test API connection")
    print("   2. Start collecting data with collectors")
    print("   3. Use DuckDB CLI or Python to query the database")