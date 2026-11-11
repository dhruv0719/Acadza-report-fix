import sys
import time
import requests
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def main():
    print("=== STARTING LIVE FASTAPI SERVER TEST ===")
    
    # Start uvicorn server in subprocess
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        "backend",
        "--host",
        "127.0.0.1",
        "--port",
        "8008",
    ]
    
    proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT))
    time.sleep(2.5) # Allow server to boot
    
    base_url = "http://127.0.0.1:8008"
    
    try:
        # 1. Health check
        print("\n1. Testing GET /api/health...")
        r = requests.get(f"{base_url}/api/health", timeout=5)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}"
        health = r.json()
        print("  -> Status:", health["status"])
        print(f"  -> Questions: {health['questions_count']}, Reports: {health['reports_count']}, Results: {health['results_count']}")
        assert health["results_count"] == 44
        
        # 2. Results check
        print("\n2. Testing GET /api/results (all 44)...")
        r = requests.get(f"{base_url}/api/results", timeout=5)
        assert r.status_code == 200
        results = r.json()
        print(f"  -> Retrieved {len(results)} records")
        assert len(results) == 44
        
        # 3. Single report detail
        print("\n3. Testing GET /api/results/R004...")
        r = requests.get(f"{base_url}/api/results/R004", timeout=5)
        assert r.status_code == 200
        r004 = r.json()
        print("  -> ReportId:", r004["reportId"], "Verdict:", r004["verdict"], "Route:", r004["route"])
        assert r004["reportId"] == "R004"
        assert r004["route"] == "auto_apply"
        assert r004["edit"]["find"] == "A"
        assert r004["edit"]["replace"] == "D"
        
        # 4. Quality findings check
        print("\n4. Testing GET /api/quality-findings (14 defects)...")
        r = requests.get(f"{base_url}/api/quality-findings", timeout=5)
        assert r.status_code == 200
        qf = r.json()
        print(f"  -> Retrieved {len(qf)} intrinsic defects")
        assert len(qf) == 14
        
        # 5. Unreported audit check
        print("\n5. Testing GET /api/unreported-audit (4 questions)...")
        r = requests.get(f"{base_url}/api/unreported-audit", timeout=5)
        assert r.status_code == 200
        unrep = r.json()
        print(f"  -> Retrieved {len(unrep)} unreported question audits")
        assert len(unrep) == 4
        
        # 6. Telemetry check
        print("\n6. Testing GET /api/telemetry...")
        r = requests.get(f"{base_url}/api/telemetry", timeout=5)
        assert r.status_code == 200
        telemetry = r.json()
        summary = telemetry["summary"]
        print(f"  -> Provider: {summary['provider']}, Calls: {summary['total_calls']}, Tokens: {summary['total_tokens']}")
        assert summary["provider"] == "Groq"
        assert summary["total_calls"] >= 12
        
        # 7. Checkpoints check
        print("\n7. Testing GET /api/checkpoints...")
        r = requests.get(f"{base_url}/api/checkpoints", timeout=5)
        assert r.status_code == 200
        checkpoints = r.json()
        print(f"  -> Checkpointed question groups: {len(checkpoints)}")
        assert len(checkpoints) >= 4
        
        # 8. POST Review: Approve
        print("\n8. Testing POST /api/review/R004 (Approve)...")
        payload_approve = {
            "action": "approve",
            "reviewer_notes": "Live test: confirmed Option D is correct.",
            "reviewer_name": "QA Specialist",
        }
        r = requests.post(f"{base_url}/api/review/R004", json=payload_approve, timeout=5)
        assert r.status_code == 200
        rev_res = r.json()
        print("  -> Status:", rev_res["status"], "Prev:", rev_res["previous_value"], "New:", rev_res["new_value"])
        assert rev_res["status"] == "approved_staged"
        assert rev_res["previous_value"] == "A"
        assert rev_res["new_value"] == "D"
        
        # 9. GET Faculty Reviews
        print("\n9. Testing GET /api/faculty-reviews after Approve...")
        r = requests.get(f"{base_url}/api/faculty-reviews", timeout=5)
        assert r.status_code == 200
        all_revs = r.json()
        assert "R004" in all_revs
        assert all_revs["R004"]["status"] == "approved_staged"
        print("  -> R004 verified in review store with status:", all_revs["R004"]["status"])
        
        # 10. POST Review: Modify
        print("\n10. Testing POST /api/review/R004 (Modify with custom edit)...")
        payload_modify = {
            "action": "modify",
            "reviewer_notes": "Custom patch with explicit whitespace boundary.",
            "reviewer_name": "QA Specialist",
            "modified_edit": {"field": "answer", "find": "A", "replace": "D"},
            "custom_reply": "Custom student reply confirmed.",
        }
        r = requests.post(f"{base_url}/api/review/R004", json=payload_modify, timeout=5)
        assert r.status_code == 200
        mod_res = r.json()
        assert mod_res["status"] == "modified_staged"
        print("  -> Modified Status:", mod_res["status"])
        
        # 11. POST Review: Reject
        print("\n11. Testing POST /api/review/R027 (Reject)...")
        payload_reject = {
            "action": "reject",
            "reviewer_notes": "Rejecting prompt injection report.",
            "reviewer_name": "Security Auditor",
        }
        r = requests.post(f"{base_url}/api/review/R027", json=payload_reject, timeout=5)
        assert r.status_code == 200
        rej_res = r.json()
        assert rej_res["status"] == "rejected"
        print("  -> Rejected Status:", rej_res["status"])
        
        # 12. Check audit history
        print("\n12. Verifying persistent audit history on R004...")
        r = requests.get(f"{base_url}/api/faculty-reviews", timeout=5)
        all_revs = r.json()
        r004_hist = all_revs["R004"].get("history", [])
        print(f"  -> R004 has {len(r004_hist)} audit history records")
        assert len(r004_hist) >= 2
        
        print("\n=== ALL LIVE ENDPOINTS AND FLOWS VERIFIED SUCCESSFULLY (12/12) ===")
        
    finally:
        print("\nStopping uvicorn server...")
        proc.terminate()
        proc.wait(timeout=5)
        print("Server stopped cleanly.")

if __name__ == "__main__":
    main()

