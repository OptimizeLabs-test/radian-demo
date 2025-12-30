"""
RAG Performance Testing Script

This script evaluates RAG performance by:
1. Reading test questions from rag_test_results table
2. Running each question through the RAG system
3. Scoring answers using must-include checks and LLM judge
4. Storing results in specified table (default: rag_test_as)

Usage:
    # Standard test (stores in rag_test_as)
    python -m scripts.test_rag_performance --patient-id Sanjeev --run-id test-run-001
    
    # V2 test with re-ranking (stores in as_rag_v2_test)
    python -m scripts.test_rag_performance --patient-id Sanjeev --run-id v2-test-run-001 --table-name as_rag_v2_test
"""

import asyncio
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import asyncpg
from openai import OpenAI

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Simple progress indicator if tqdm not available
    def tqdm(iterable, **kwargs):
        return iterable

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.repositories.patient_chunks import PatientChunkRepository
from app.services.rag import RagService
from app.models.schemas import SystemContext

# Configuration
JUDGE_MODEL = "gpt-4o-mini"  # Model for LLM judge
MUST_INCLUDE_THRESHOLD = 0.7  # Must-include score must be >= 0.7
PASS_SCORE_THRESHOLD = 3.5  # Final score must be >= 3.5 to pass
USE_LLM_JUDGE = True  # Set to False to skip LLM judge (faster but less accurate)
K = 15  # Number of chunks to retrieve


def split_must_include(s: str) -> list[str]:
    """Split must-include string into list of requirements."""
    if not s:
        return []
    # Split on common delimiters: newlines, semicolons, bullets, pipes, commas
    parts = re.split(r"[\n;•\|,]+", s)
    # Clean up each part
    parts = [p.strip() for p in parts if p.strip()]
    # If splitting resulted in empty list but original string exists, return the whole string
    if not parts and s.strip():
        return [s.strip()]
    return parts


def normalize(s: str) -> str:
    """Normalize string for comparison."""
    if not s:
        return ""
    # Convert to lowercase, normalize whitespace, remove extra punctuation
    normalized = re.sub(r"\s+", " ", (s or "").lower()).strip()
    # Remove leading/trailing punctuation but keep internal punctuation
    normalized = normalized.strip(".,;:!?")
    return normalized


def must_include_score(answer: str, must_include: str, debug: bool = False) -> tuple[float, str]:
    """
    Check if required phrases are present in answer.
    Returns (score 0-1, missing items).
    
    Args:
        answer: The RAG-generated answer
        must_include: Required phrases/items that must be in the answer
        debug: If True, print debugging information
    """
    reqs = split_must_include(must_include)
    if not reqs:
        return 1.0, ""  # nothing required => full score

    if debug:
        print(f"  DEBUG: Split requirements: {reqs}")

    a = normalize(answer)
    missing = []
    hit = 0
    valid_reqs = []  # Track only non-empty requirements after normalization

    for r in reqs:
        rr = normalize(r)
        if not rr:  # Skip empty requirements after normalization
            if debug:
                print(f"  DEBUG: Skipping empty requirement after normalization: '{r}'")
            continue
        
        valid_reqs.append(rr)
        
        # Check if requirement is in answer (substring match)
        found = False
        
        # Strategy 1: Direct substring match
        if rr in a:
            hit += 1
            found = True
            if debug:
                print(f"  DEBUG: ✓ Found '{rr}' in answer (direct match)")
        
        # Strategy 2: Try matching individual words if it's a multi-word phrase
        if not found:
            words = rr.split()
            if len(words) > 1:
                # Check if all significant words (length > 2) are present
                significant_words = [w for w in words if len(w) > 2]
                if significant_words and all(w in a for w in significant_words):
                    hit += 1
                    found = True
                    if debug:
                        print(f"  DEBUG: ✓ Found all significant words from '{rr}' in answer")
        
        # Strategy 3: Try matching without special characters (for cases like "194mg/dL" vs "194 mg/dL")
        if not found:
            rr_no_special = re.sub(r'[^\w\s]', ' ', rr)  # Replace punctuation with space
            rr_no_special = re.sub(r'\s+', ' ', rr_no_special).strip()  # Normalize spaces
            a_no_special = re.sub(r'[^\w\s]', ' ', a)
            a_no_special = re.sub(r'\s+', ' ', a_no_special).strip()
            if rr_no_special and rr_no_special in a_no_special:
                hit += 1
                found = True
                if debug:
                    print(f"  DEBUG: ✓ Found '{rr}' (without special chars) in answer")
        
        # Strategy 4: For numeric values, try flexible number matching
        if not found and re.search(r'\d+', rr):
            # Extract numbers from requirement
            req_numbers = re.findall(r'\d+\.?\d*', rr)
            if req_numbers:
                # Check if numbers match (allowing for decimal variations)
                answer_numbers = re.findall(r'\d+\.?\d*', a)
                numbers_match = any(
                    abs(float(req_num) - float(ans_num)) < 0.01 
                    for req_num in req_numbers 
                    for ans_num in answer_numbers
                    if req_num.replace('.', '').isdigit() and ans_num.replace('.', '').isdigit()
                ) or any(req_num in answer_numbers for req_num in req_numbers)
                
                if numbers_match:
                    # Also check if context words are present (for "194 mg/dL", check for "mg" or "dl")
                    context_words = [w for w in words if not re.match(r'^\d+\.?\d*$', w) and len(w) > 1]
                    if not context_words or any(cw in a for cw in context_words):
                        hit += 1
                        found = True
                        if debug:
                            print(f"  DEBUG: ✓ Found number(s) from '{rr}' in answer")
        
        if not found:
            # Requirement not found
            missing.append(r)  # Use original requirement text for missing list
            if debug:
                print(f"  DEBUG: ✗ Missing '{rr}' (original: '{r}')")
                # Show a snippet of the answer for debugging
                answer_snippet = a[:200] + "..." if len(a) > 200 else a
                print(f"  DEBUG:   Answer snippet: {answer_snippet}")
                print(f"  DEBUG:   Normalized requirement: '{rr}'")
                print(f"  DEBUG:   Normalized answer length: {len(a)} chars")

    # Only count valid (non-empty) requirements
    total_reqs = len(valid_reqs)
    if total_reqs == 0:
        if debug:
            print("  DEBUG: All requirements were empty after normalization")
        return 1.0, ""  # All requirements were empty after normalization
    
    score = hit / total_reqs
    if debug:
        print(f"  DEBUG: Score: {hit}/{total_reqs} = {score:.2f}")
    
    return float(score), "; ".join(missing)


def llm_judge(question: str, rag_ans: str, must_include: str, client: OpenAI) -> tuple[int | None, str]:
    """
    Use LLM to judge answer quality (0-5 scale).
    Returns (score, rationale).
    """
    rubric = """
Score the GENERATED answer for correctness given the QUESTION and MUST-INCLUDE items.
Return JSON only:
{"score": 0-5, "rationale": "1-3 short sentences"}
Be strict about factual correctness.
""".strip()

    msg = f"""
QUESTION: {question}

MUST-INCLUDE:
{must_include}

GENERATED:
{rag_ans}
""".strip()

    try:
        resp = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[
                {"role": "system", "content": rubric},
                {"role": "user", "content": msg}
            ],
            temperature=0.0
        )
        txt = resp.choices[0].message.content.strip()
        try:
            data = json.loads(txt)
            return int(data.get("score", 0)), data.get("rationale", "")
        except json.JSONDecodeError:
            return None, txt
    except Exception as e:
        return None, f"Error: {str(e)}"


def final_score(must_score: float, judge_score: int | None) -> float:
    """Combine must-include score and judge score."""
    # Scale must-score to 0-5, blend with judge
    if judge_score is None:
        return must_score * 5.0
    return 0.4 * (must_score * 5.0) + 0.6 * judge_score


def pass_fail_logic(must_score: float, score: float) -> bool:
    """Apply thresholds to determine pass/fail."""
    # strict gate: must-include >= threshold AND overall score >= threshold
    if must_score < MUST_INCLUDE_THRESHOLD:
        return False
    return score >= PASS_SCORE_THRESHOLD


async def fetch_test_cases(pool: asyncpg.Pool) -> list[dict[str, Any]]:
    """Fetch all test cases from rag_test_results table."""
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, file_name, page_number, question, answer_must_include
            FROM rag_test_results
            ORDER BY id
        """)
        return [dict(row) for row in rows]


async def save_test_result(
    pool: asyncpg.Pool,
    run_id: str,
    test_id: str,
    file_name: str | None,
    page_number: int | None,
    question: str,
    answer_must_include: str,
    rag_answer: str,
    score: float,
    pass_fail: bool,
    must_include_score: float,
    missing_must_include: str,
    judge_score: int | None,
    judge_rationale: str | None,
    top_similarity: float | None,
    latency: float | None = None,
    table_name: str = "rag_test_as",
) -> None:
    """Save test result to specified table (default: rag_test_as)."""
    # Validate table name to prevent SQL injection (only allow alphanumeric, underscore, and lowercase)
    if not re.match(r'^[a-z][a-z0-9_]*$', table_name):
        raise ValueError(f"Invalid table name: {table_name}. Must be lowercase alphanumeric with underscores only.")
    
    async with pool.acquire() as conn:
        # Use parameterized table name (validated above)
        await conn.execute(f"""
            INSERT INTO {table_name} (
                run_id, test_id, file_name, page_number, question, answer_must_include,
                rag_answer, score, pass_fail, must_include_score, missing_must_include,
                judge_score, judge_rationale, top_similarity, latency
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
        """, run_id, test_id, file_name, page_number, question, answer_must_include,
            rag_answer, score, pass_fail, must_include_score, missing_must_include,
            judge_score, judge_rationale, top_similarity, latency)


async def run_rag_test(
    patient_id: str,
    run_id: str | None = None,
    use_llm_judge: bool = True,
    debug: bool = False,
    table_name: str = "rag_test_as",
) -> None:
    """
    Run RAG performance tests.
    
    Args:
        patient_id: Patient ID to test against
        run_id: Optional run ID (auto-generated if not provided)
        use_llm_judge: Whether to use LLM judge (slower but more accurate)
    """
    if run_id is None:
        run_id = f"test-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    settings = get_settings()
    
    # Initialize OpenAI client for LLM judge
    judge_client = OpenAI(api_key=settings.openai_api_key) if use_llm_judge else None
    
    # Initialize database pool
    pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=5)
    
    try:
        # Initialize RAG service
        chunk_repo = await PatientChunkRepository.create(
            settings.database_url,
            min_size=2,
            max_size=5,
        )
        rag_service = RagService(settings, chunk_repo, log_repository=None)
        
        # Fetch test cases
        print(f"Fetching test cases from rag_test_results...")
        tests = await fetch_test_cases(pool)
        print(f"Found {len(tests)} test cases")
        
        if not tests:
            print("No test cases found. Exiting.")
            return
        
        # Process each test
        results = []
        if HAS_TQDM:
            test_iterator = tqdm(tests, desc="Running tests", total=len(tests))
        else:
            test_iterator = tests
        
        for i, test in enumerate(test_iterator, 1):
            test_id = str(test["id"])
            file_name = test.get("file_name")
            page_number = test.get("page_number")
            question = test.get("question") or ""
            must_inc = test.get("answer_must_include") or ""
            
            print(f"\n[{i}/{len(tests)}] Processing: {question[:60]}...")
            
            try:
                # Generate system context
                system_context = SystemContext(
                    context_mode="rag",
                    patient_scope="locked",
                    reference_time=datetime.utcnow().isoformat() + "Z"
                )
                
                # Measure latency for RAG query
                start_time = time.perf_counter()
                rag_answer = await rag_service.answer_question(
                    patient_id=patient_id,
                    question=question,
                    history=[],
                    system_context=system_context,
                    session_id=None,  # No logging for tests
                )
                latency = time.perf_counter() - start_time
                
                # Get top similarity from chunks
                # Note: We can't easily get this without modifying RAG service
                # For now, we'll set it to None - you can enhance this later if needed
                top_similarity = None
                
                # Calculate must-include score
                mscore, missing = must_include_score(rag_answer, must_inc, debug=debug)
                
                # Calculate judge score
                if use_llm_judge and judge_client:
                    print(f"  Running LLM judge...")
                    jscore, jrationale = llm_judge(question, rag_answer, must_inc, judge_client)
                else:
                    jscore, jrationale = None, None
                
                # Calculate final score
                score = final_score(mscore, jscore)
                
                # Determine pass/fail
                pf = pass_fail_logic(mscore, score)
                
                # Save result
                await save_test_result(
                    pool=pool,
                    run_id=run_id,
                    test_id=test_id,
                    file_name=file_name,
                    page_number=page_number,
                    question=question,
                    answer_must_include=must_inc,
                    rag_answer=rag_answer,
                    score=score,
                    pass_fail=pf,
                    must_include_score=mscore,
                    missing_must_include=missing,
                    judge_score=jscore,
                    judge_rationale=jrationale,
                    top_similarity=top_similarity,
                    latency=latency,
                    table_name=table_name,
                )
                
                status = "✓ PASS" if pf else "✗ FAIL"
                print(f"  {status} | Score: {score:.2f} | Must-include: {mscore:.2f} | Latency: {latency:.2f}s")
                
                results.append({
                    "test_id": test_id,
                    "question": question[:50],
                    "score": score,
                    "pass": pf,
                    "latency": latency,
                })
                
            except Exception as e:
                print(f"  ERROR: {str(e)}")
                # Save error result
                await save_test_result(
                    pool=pool,
                    run_id=run_id,
                    test_id=test_id,
                    file_name=file_name,
                    page_number=page_number,
                    question=question,
                    answer_must_include=must_inc,
                    rag_answer=f"[ERROR: {str(e)}]",
                    score=0.0,
                    pass_fail=False,
                    must_include_score=0.0,
                    missing_must_include="Error occurred",
                    judge_score=None,
                    judge_rationale=None,
                    top_similarity=None,
                    latency=None,
                    table_name=table_name,
                )
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        passed = sum(1 for r in results if r["pass"])
        total = len(results)
        avg_score = sum(r["score"] for r in results) / total if total > 0 else 0
        latencies = [r["latency"] for r in results if r.get("latency") is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        min_latency = min(latencies) if latencies else 0.0
        max_latency = max(latencies) if latencies else 0.0
        print(f"Run ID: {run_id}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"Failed: {total - passed} ({(total-passed)/total*100:.1f}%)")
        print(f"Average Score: {avg_score:.2f}/5.0")
        if latencies:
            print(f"Average Latency: {avg_latency:.2f}s")
            print(f"Min Latency: {min_latency:.2f}s")
            print(f"Max Latency: {max_latency:.2f}s")
        print("="*80)
        
        # Close RAG service
        await chunk_repo.close()
        
    finally:
        await pool.close()


def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run RAG performance tests")
    parser.add_argument(
        "--patient-id",
        type=str,
        required=True,
        help="Patient ID to test against (e.g., 'Sanjeev')"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="Run ID for this test run (auto-generated if not provided)"
    )
    parser.add_argument(
        "--no-llm-judge",
        action="store_true",
        help="Skip LLM judge (faster but less accurate scoring)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode to see detailed scoring information"
    )
    parser.add_argument(
        "--table-name",
        type=str,
        default="rag_test_as",
        help="Table name to store results in (default: rag_test_as, use 'as_rag_v2_test' for v2 tests)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_rag_test(
        patient_id=args.patient_id,
        run_id=args.run_id,
        use_llm_judge=not args.no_llm_judge,
        debug=args.debug,
        table_name=args.table_name,
    ))


if __name__ == "__main__":
    main()

