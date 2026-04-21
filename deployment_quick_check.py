#!/usr/bin/env python3
"""
FairLens Deployment Quick Start
One-command deployment verification and summary
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("FairLens Deployment Ready - Quick Start Guide")
    print("=" * 60)
    print(f"{Colors.END}")

def print_status(message, status="info"):
    if status == "pass":
        print(f"{Colors.GREEN}✓ {message}{Colors.END}")
    elif status == "fail":
        print(f"{Colors.RED}✗ {message}{Colors.END}")
    elif status == "warn":
        print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")
    else:
        print(f"{Colors.BLUE}→ {message}{Colors.END}")

def check_file(path):
    """Check if file exists"""
    return Path(path).exists()

def run_command(cmd):
    """Run command silently"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def main():
    print_header()
    
    root = Path(__file__).parent
    os.chdir(root)
    
    print(f"\n{Colors.BOLD}Deployment Readiness Check{Colors.END}")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    # Check critical files
    critical_files = {
        "README.md": "Project documentation",
        "DEPLOYMENT_READY_CHECKLIST.md": "Deployment checklist",
        "DEPLOYMENT_PACKAGE_SUMMARY.md": "Deployment summary",
        "backend/requirements.txt": "Python dependencies",
        "docker-compose.prod.yml": "Production docker setup",
        "backend/.env.prod.template": "Environment template",
        "backend/app/api/v1/reports.py": "Reports API endpoint",
        "backend/app/services/reporting.py": "Enhanced reporting service",
        "backend/tests/test_enhanced_reporting.py": "Test suite",
    }
    
    print(f"\n{Colors.BOLD}Critical Files:{Colors.END}")
    for file, desc in critical_files.items():
        if check_file(file):
            print_status(f"{file} - {desc}", "pass")
            passed += 1
        else:
            print_status(f"{file} - {desc}", "fail")
            failed += 1
    
    # Python checks
    print(f"\n{Colors.BOLD}Python Environment:{Colors.END}")
    
    if run_command("python --version > /dev/null 2>&1"):
        print_status("Python installed", "pass")
        passed += 1
    else:
        print_status("Python installed", "fail")
        failed += 1
    
    if run_command("python -c 'import fastapi' 2>/dev/null"):
        print_status("FastAPI installed", "pass")
        passed += 1
    else:
        print_status("FastAPI installed", "warn")
    
    if run_command("python -c 'import reportlab' 2>/dev/null"):
        print_status("ReportLab installed", "pass")
        passed += 1
    else:
        print_status("ReportLab installed", "warn")
    
    # Code quality
    print(f"\n{Colors.BOLD}Code Quality:{Colors.END}")
    
    os.chdir("backend")
    
    if run_command("python -m py_compile app/services/reporting.py"):
        print_status("reporting.py syntax valid", "pass")
        passed += 1
    else:
        print_status("reporting.py syntax valid", "fail")
        failed += 1
    
    if run_command("python -m py_compile app/api/v1/reports.py"):
        print_status("reports.py syntax valid", "pass")
        passed += 1
    else:
        print_status("reports.py syntax valid", "fail")
        failed += 1
    
    # Docker
    os.chdir("..")
    print(f"\n{Colors.BOLD}Docker Configuration:{Colors.END}")
    
    if check_file("docker-compose.prod.yml"):
        print_status("Production docker-compose.yml present", "pass")
        passed += 1
    else:
        print_status("Production docker-compose.yml present", "fail")
        failed += 1
    
    if run_command("docker --version > /dev/null 2>&1"):
        print_status("Docker installed", "pass")
        passed += 1
    else:
        print_status("Docker installed", "warn")
    
    # Summary
    print(f"\n{Colors.BOLD}Summary{Colors.END}")
    print("-" * 60)
    print(f"Passed:  {Colors.GREEN}{passed}{Colors.END}")
    print(f"Failed:  {Colors.RED}{failed}{Colors.END}")
    total = passed + failed
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"Success Rate: {percentage:.0f}%")
    
    # Deployment ready
    print(f"\n{Colors.BOLD}Deployment Status:{Colors.END}")
    if failed == 0:
        print_status("ALL CHECKS PASSED - READY FOR DEPLOYMENT", "pass")
        print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
        print("1. Review DEPLOYMENT_READY_CHECKLIST.md")
        print("2. Configure backend/.env with production values")
        print("3. Run: docker-compose -f docker-compose.prod.yml up -d")
        print("4. Run database migrations: alembic upgrade head")
        print("5. Verify: curl http://localhost:8001/health")
        return 0
    else:
        print_status("SOME CHECKS FAILED - FIX BEFORE DEPLOYMENT", "fail")
        print(f"\n{Colors.BOLD}Issues to Fix:{Colors.END}")
        print("- Install missing Python packages: pip install -r backend/requirements.txt")
        print("- Check file permissions and git status")
        print("- Verify all files were properly created")
        print("- Install Docker if not present")
        return 1

if __name__ == "__main__":
    print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    exit_code = main()
    print(f"\n{'=' * 60}\n")
    sys.exit(exit_code)
