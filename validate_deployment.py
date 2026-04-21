#!/usr/bin/env python3
"""
FairLens Deployment Validation Script
Comprehensive validation of all deployment components
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Tuple, List

class DeploymentValidator:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"

    def check(self, name: str, condition: bool, error_msg: str = "") -> bool:
        """Log check result"""
        if condition:
            print(f"✓ {name}")
            self.passed += 1
        else:
            print(f"✗ {name}")
            if error_msg:
                print(f"  Error: {error_msg}")
            self.failed += 1
        return condition

    def warn(self, name: str):
        """Log warning"""
        print(f"⚠ {name}")
        self.warnings += 1

    def run_command(self, cmd: str, cwd: Path = None) -> Tuple[int, str]:
        """Run shell command and return exit code and output"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return 1, "Command timed out"
        except Exception as e:
            return 1, str(e)

    def validate_python_env(self):
        """Validate Python environment and dependencies"""
        print("\n1. Python Environment")
        print("-" * 40)

        # Check Python version
        code, output = self.run_command("python --version")
        self.check("Python installed", code == 0, output)

        # Check required packages
        packages = [
            ("fastapi", "FastAPI"),
            ("sqlalchemy", "SQLAlchemy"),
            ("psycopg2", "psycopg2"),
            ("celery", "Celery"),
            ("reportlab", "ReportLab"),
            ("pydantic", "Pydantic"),
            ("uvicorn", "Uvicorn"),
        ]

        os.chdir(self.backend_dir)
        for pkg, name in packages:
            code, _ = self.run_command(f"python -c 'import {pkg}'")
            self.check(f"{name} installed", code == 0)

    def validate_code_quality(self):
        """Validate code quality and syntax"""
        print("\n2. Code Quality")
        print("-" * 40)

        os.chdir(self.backend_dir)
        
        files_to_check = [
            "app/services/reporting.py",
            "app/api/v1/reports.py",
            "app/api/v1/router.py",
            "app/api/v1/llm_bias.py",
            "app/main.py",
        ]

        for file in files_to_check:
            code, output = self.run_command(f"python -m py_compile {file}")
            self.check(f"{file} syntax valid", code == 0, output)

        # Check imports
        imports = [
            ("app.services.reporting", "ComplianceReportGenerator"),
            ("app.api.v1", "reports"),
            ("app.api.v1", "llm_bias"),
            ("app.db.models", "LLMBiasAnalysis"),
        ]

        for module, name in imports:
            code, output = self.run_command(f"python -c 'from {module} import {name}'")
            self.check(f"Import {module}.{name}", code == 0, output)

    def validate_database(self):
        """Validate database configuration"""
        print("\n3. Database Configuration")
        print("-" * 40)

        os.chdir(self.backend_dir)
        
        # Check alembic configuration
        self.check("alembic.ini exists", (self.backend_dir / "alembic.ini").exists())
        self.check("Alembic versions dir exists", (self.backend_dir / "alembic/versions").exists())
        
        # Check migrations
        migrations = ["0001_initial.py", "0002_llm_bias.py"]
        for migration in migrations:
            path = self.backend_dir / f"alembic/versions/{migration}"
            self.check(f"Migration {migration} exists", path.exists())

    def validate_api_endpoints(self):
        """Validate API endpoint configuration"""
        print("\n4. API Endpoints")
        print("-" * 40)

        os.chdir(self.backend_dir)
        
        endpoints = [
            ("app/api/v1/audits.py", "Audits"),
            ("app/api/v1/auth.py", "Auth"),
            ("app/api/v1/llm_bias.py", "LLM Bias"),
            ("app/api/v1/reports.py", "Reports"),
            ("app/api/v1/users.py", "Users"),
        ]

        for file, name in endpoints:
            path = self.backend_dir / file
            self.check(f"{name} endpoint exists", path.exists())

        # Check router configuration
        router_path = self.backend_dir / "app/api/v1/router.py"
        with open(router_path, 'r') as f:
            router_content = f.read()
            self.check("Reports router imported", "from app.api.v1 import reports" in router_content)
            self.check("Reports router registered", "include_router(reports.router" in router_content)

    def validate_docker(self):
        """Validate Docker configuration"""
        print("\n5. Docker Configuration")
        print("-" * 40)

        files = [
            ("docker-compose.yml", "Main"),
            ("docker-compose.prod.yml", "Production"),
            ("backend/Dockerfile", "Backend"),
            ("frontend/Dockerfile", "Frontend"),
        ]

        for file, name in files:
            path = self.root_dir / file
            self.check(f"{name} docker file exists", path.exists())

        # Validate docker-compose syntax
        code, output = self.run_command("docker-compose -f docker-compose.yml config > /dev/null 2>&1")
        if code == 0:
            self.check("docker-compose.yml syntax valid", True)
        else:
            self.check("docker-compose.yml syntax valid", False, output)

    def validate_environment(self):
        """Validate environment configuration"""
        print("\n6. Environment Configuration")
        print("-" * 40)

        env_files = [
            ("backend/.env", "Production"),
            ("backend/.env.example", "Example"),
            ("backend/.env.prod.example", "Production Example"),
        ]

        for file, name in env_files:
            path = self.root_dir / file
            if path.exists():
                self.check(f"{name} env file exists", True)
            else:
                self.warn(f"{name} env file missing (create from .env.example)")

    def validate_documentation(self):
        """Validate documentation files"""
        print("\n7. Documentation")
        print("-" * 40)

        docs = [
            "README.md",
            "API_DOCUMENTATION.md",
            "DEPLOYMENT_GUIDE.md",
            "ENHANCED_REPORT_GENERATION.md",
            "REPORT_DEPLOYMENT_GUIDE.md",
            "PHASE2_VERIFICATION_CHECKLIST.md",
            "PHASE2_COMPLETION_REPORT.md",
        ]

        for doc in docs:
            path = self.root_dir / doc
            self.check(f"{doc} exists", path.exists())

    def validate_dependencies(self):
        """Validate dependencies"""
        print("\n8. Dependencies")
        print("-" * 40)

        req_file = self.backend_dir / "requirements.txt"
        self.check("requirements.txt exists", req_file.exists())

        if req_file.exists():
            with open(req_file, 'r') as f:
                req_content = f.read()
                
            deps = {
                "fastapi": "FastAPI",
                "sqlalchemy": "SQLAlchemy",
                "psycopg2": "psycopg2",
                "celery": "Celery",
                "reportlab": "ReportLab",
                "pydantic": "Pydantic",
            }

            for pkg, name in deps.items():
                self.check(f"{name} in requirements", pkg in req_content)

    def validate_frontend(self):
        """Validate frontend configuration"""
        print("\n9. Frontend Configuration")
        print("-" * 40)

        files = [
            "package.json",
            "vite.config.ts",
            "tsconfig.json",
        ]

        for file in files:
            path = self.frontend_dir / file
            self.check(f"Frontend {file} exists", path.exists())

        # Check src directory
        self.check("Frontend src directory exists", (self.frontend_dir / "src").exists())

    def validate_tests(self):
        """Validate test configuration"""
        print("\n10. Testing")
        print("-" * 40)

        tests_dir = self.backend_dir / "tests"
        self.check("Tests directory exists", tests_dir.exists())
        
        test_files = [
            "test_enhanced_reporting.py",
        ]

        for test_file in test_files:
            path = tests_dir / test_file
            self.check(f"Test file {test_file} exists", path.exists())

    def validate_directories(self):
        """Validate required directories"""
        print("\n11. Directory Structure")
        print("-" * 40)

        dirs = [
            ("backend/app", "Backend app"),
            ("backend/tests", "Backend tests"),
            ("frontend/src", "Frontend src"),
            ("frontend/public", "Frontend public"),
        ]

        for dir_path, name in dirs:
            path = self.root_dir / dir_path
            self.check(f"{name} directory exists", path.exists())

    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 40)
        print("Validation Summary")
        print("=" * 40)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Passed:  {self.passed}")
        print(f"Failed:  {self.failed}")
        print(f"Warnings: {self.warnings}")
        print(f"Success Rate: {pass_rate:.1f}%")
        print()

        if self.failed == 0:
            print("✓ ALL VALIDATIONS PASSED - READY FOR DEPLOYMENT")
            return 0
        else:
            print(f"✗ {self.failed} VALIDATION(S) FAILED - FIX BEFORE DEPLOYMENT")
            return 1

    def run_all(self):
        """Run all validations"""
        print("=" * 40)
        print("FairLens Deployment Validator")
        print("=" * 40)

        try:
            self.validate_python_env()
            self.validate_code_quality()
            self.validate_database()
            self.validate_api_endpoints()
            self.validate_docker()
            self.validate_environment()
            self.validate_documentation()
            self.validate_dependencies()
            self.validate_frontend()
            self.validate_tests()
            self.validate_directories()
        except Exception as e:
            print(f"\n✗ Validation error: {e}")
            return 1

        return self.print_summary()


def main():
    """Main entry point"""
    validator = DeploymentValidator()
    exit_code = validator.run_all()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
