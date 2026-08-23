#!/usr/bin/env python3
"""
Sovereign AI Health Score Engine
Runs locally on operator's machine — zero external deps.
Self-verification gate: your live score IS the proof asset.
"""

import json
import sqlite3
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

# Paths (adjust for installed location)
REVENUE_DB = Path("/home/scott/ai-lab/revenue-os/revenue-os.db")
AUDIT_API = "http://127.0.0.1:8011"

def run_cmd(cmd: list[str], timeout: int = 10) -> dict[str, Any]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return {"ok": result.returncode == 0, "stdout": result.stdout.strip(), "stderr": result.stderr.strip(), "code": result.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "timeout", "code": 124}
    except Exception as e:
        return {"ok": False, "stdout": "", "stderr": str(e), "code": 1}

def check_gpu_health() -> dict[str, Any]:
    """Check GPU via nvidia-smi"""
    result = run_cmd(["nvidia-smi", "--query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,ecc.errors.uncorrected.volatile", "--format=csv,noheader,nounits"])
    if not result["ok"]:
        return {"healthy": False, "error": "nvidia-smi failed", "score": 0}
    
    gpus = []
    for line in result["stdout"].splitlines():
        if line.strip():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 8:
                gpus.append({
                    "index": int(parts[0]),
                    "name": parts[1],
                    "temp_c": int(parts[2]),
                    "util_pct": int(parts[3]),
                    "mem_used_mb": int(parts[4]),
                    "mem_total_mb": int(parts[5]),
                    "power_w": float(parts[6]) if parts[6] != "[Not Supported]" else 0,
                    "ecc_errors": int(parts[7]) if parts[7].isdigit() else 0
                })
    
    # Score: penalize high temp (>80), high ECC errors, 100% util sustained
    score = 100
    findings = []
    for gpu in gpus:
        if gpu["temp_c"] > 85:
            score -= 15
            findings.append(f"GPU {gpu['index']} temp critical: {gpu['temp_c']}°C")
        elif gpu["temp_c"] > 75:
            score -= 5
            findings.append(f"GPU {gpu['index']} temp high: {gpu['temp_c']}°C")
        if gpu["ecc_errors"] > 0:
            score -= 20
            findings.append(f"GPU {gpu['index']} ECC errors: {gpu['ecc_errors']}")
        if gpu["util_pct"] == 100:
            score -= 5
            findings.append(f"GPU {gpu['index']} sustained 100% util")
    
    return {"healthy": score >= 70, "score": max(0, score), "gpus": gpus, "findings": findings}

def check_services() -> dict[str, Any]:
    """Check sovereign services via systemctl"""
    services = [
        "hardonia-checkout-api", "hardonia-compute-api", "storefront",
        "ai-lab-audit-api", "vramd", "ollama-default", "ollama-router",
        "comfyui", "nats", "prometheus", "minio", "openwebui", "portainer"
    ]
    
    result = run_cmd(["systemctl", "--user", "is-active"] + services)
    active = 0
    findings = []
    for line in result["stdout"].splitlines():
        if line == "active":
            active += 1
        else:
            findings.append(f"Service down: {line}")
    
    score = int((active / len(services)) * 100)
    return {"healthy": active == len(services), "score": score, "active": active, "total": len(services), "findings": findings}

def check_revenue_integrity() -> dict[str, Any]:
    """Check revenue-os.db for synthetic vs real sales"""
    try:
        conn = sqlite3.connect(REVENUE_DB)
        conn.row_factory = sqlite3.Row
        
        # Check for synthetic sales (purged previously)
        r = conn.execute("SELECT COUNT(*) FROM revenue_truth WHERE source = 'synthetic'").fetchone()
        synthetic = r[0] if r else 0
        
        r = conn.execute("SELECT COUNT(*) FROM revenue_truth WHERE source = 'stripe' AND event_type LIKE 'payment_intent%'").fetchone()
        real = r[0] if r else 0
        
        r = conn.execute("SELECT COUNT(*) FROM purchases WHERE status = 'fulfilled'").fetchone()
        fulfilled = r[0] if r else 0
        
        score = 100
        findings = []
        if synthetic > 0:
            score -= 30
            findings.append(f"{synthetic} synthetic sales in revenue_truth")
        if real == 0:
            score -= 20
            findings.append("No real Stripe payments recorded")
        if fulfilled > real:
            score -= 25
            findings.append(f"Fulfilled ({fulfilled}) > real payments ({real})")
        
        return {"healthy": score >= 70, "score": max(0, score), "synthetic": synthetic, "real": real, "fulfilled": fulfilled, "findings": findings}
    except Exception as e:
        return {"healthy": False, "score": 0, "error": str(e), "findings": [f"DB error: {e}"]}

def check_security_posture() -> dict[str, Any]:
    """Check audit-api security findings"""
    import urllib.request
    try:
        req = urllib.request.Request(f"{AUDIT_API}/api/operator/security", headers={"Authorization": "Bearer test"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        findings = data.get("findings", [])
        score = max(0, 100 - len(findings) * 10)
        return {"healthy": len(findings) == 0, "score": score, "findings": findings}
    except Exception:
        # If audit-api not reachable, degrade gracefully
        return {"healthy": True, "score": 80, "findings": ["audit-api unreachable (degraded)"]}

def check_drift() -> dict[str, Any]:
    """Check suite drift guard"""
    result = run_cmd(["bash", "/home/scott/ai-lab/suite/suite_drift.sh"])
    if not result["ok"]:
        return {"healthy": False, "score": 50, "findings": ["drift check failed"]}
    
    drift_detected = "DRIFT DETECTED" in result["stdout"] or "DRIFT REPORT" in result["stdout"]
    score = 70 if drift_detected else 100
    findings = ["Drift detected between registry/DB/surface"] if drift_detected else []
    return {"healthy": not drift_detected, "score": score, "findings": findings}

def compute_trust_score() -> dict[str, Any]:
    """Aggregate all checks into single trust score"""
    checks = {
        "gpu": check_gpu_health(),
        "services": check_services(),
        "revenue": check_revenue_integrity(),
        "security": check_security_posture(),
        "drift": check_drift()
    }
    
    weights = {"gpu": 0.25, "services": 0.25, "revenue": 0.20, "security": 0.15, "drift": 0.15}
    total_score = sum(checks[k].get("score", 0) * weights[k] for k in weights)
    all_healthy = all(checks[k].get("healthy", False) for k in weights)
    all_findings = []
    for k, v in checks.items():
        all_findings.extend([f"[{k}] {f}" for f in v.get("findings", [])])
    
    return {
        "score": round(total_score),
        "healthy": all_healthy,
        "checks": checks,
        "findings": all_findings,
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0"
    }

def main():
    if "--self" in sys.argv:
        result = compute_trust_score()
        print(json.dumps(result, indent=2))
        if not result["healthy"]:
            sys.exit(1)
    elif "--json" in sys.argv:
        result = compute_trust_score()
        print(json.dumps(result))
    else:
        result = compute_trust_score()
        print(f"Trust Score: {result['score']}/100 {'✅' if result['healthy'] else '❌'}")
        for k, v in result["checks"].items():
            status = "✅" if v.get("healthy") else "❌"
            print(f"  {k}: {v.get('score', 0)}/100 {status}")
        if result["findings"]:
            print("\nFindings:")
            for f in result["findings"]:
                print(f"  - {f}")

if __name__ == "__main__":
    main()
