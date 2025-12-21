"""
Diagnostic script to check if performance optimizations are in place.
Run this to verify your database setup.
"""

import asyncio
import asyncpg
from pgvector.asyncpg import register_vector
import os
from dotenv import load_dotenv

load_dotenv()


async def check_performance_setup():
    """Check if IVFFLAT index and stored function exist."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    try:
        conn = await asyncpg.connect(database_url)
        await register_vector(conn)
        
        print("🔍 Checking performance optimizations...\n")
        
        # Check for IVFFLAT index
        index_check = await conn.fetch("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'patient_chunks' 
            AND indexname LIKE '%embedding%'
        """)
        
        if index_check:
            print("✅ IVFFLAT Index found:")
            for row in index_check:
                if 'ivfflat' in row['indexdef'].lower():
                    print(f"   - {row['indexname']}")
                    # Extract lists parameter
                    if 'lists' in row['indexdef']:
                        lists_match = [s for s in row['indexdef'].split() if 'lists' in s.lower()]
                        if lists_match:
                            print(f"   - Configuration: {lists_match[0]}")
                else:
                    print(f"   ⚠️  {row['indexname']} (not IVFFLAT)")
        else:
            print("❌ No IVFFLAT index found!")
            print("   Run the migration: backend/migrations/001_add_ivfflat_index_and_function.sql")
        
        # Check for stored function
        function_check = await conn.fetch("""
            SELECT proname, prosrc 
            FROM pg_proc 
            WHERE proname = 'match_patient_chunks'
        """)
        
        if function_check:
            print("\n✅ Stored function 'match_patient_chunks' found")
        else:
            print("\n❌ Stored function 'match_patient_chunks' not found!")
            print("   Run the migration: backend/migrations/001_add_ivfflat_index_and_function.sql")
        
        # Check table size
        table_size = await conn.fetchval("""
            SELECT COUNT(*) FROM patient_chunks
        """)
        print(f"\n📊 Patient chunks in database: {table_size}")
        
        if table_size < 100:
            print("   ⚠️  Warning: IVFFLAT index works best with 100+ rows")
        
        # Check for embeddings
        embedding_count = await conn.fetchval("""
            SELECT COUNT(*) FROM patient_chunks WHERE embedding IS NOT NULL
        """)
        print(f"📊 Chunks with embeddings: {embedding_count}")
        
        await conn.close()
        
        print("\n💡 Performance Tips:")
        print("   - Set IVFFLAT_PROBES=1 in .env for maximum speed")
        print("   - Reduce MAX_RETRIEVAL_CHUNKS for faster queries")
        print("   - Check OpenAI API latency (external dependency)")
        
    except Exception as e:
        print(f"❌ Error checking setup: {e}")


if __name__ == "__main__":
    asyncio.run(check_performance_setup())

