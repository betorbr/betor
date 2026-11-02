#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path

PYPROJECT_PATH = Path("pyproject.toml")
APP_PATH = Path("betor/api/app.py")


def run_cmd(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_current_version() -> str:
    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def get_commits_since_last_release() -> tuple[str | None, list[str]]:
    try:
        # Find last commit with message starting with "release:"
        git_log_release = run_cmd(["git", "log", "--grep=^release:", "--format=%H %s", "-n", "1"])
        if not git_log_release:
            return None, run_cmd(["git", "log", "--format=%s"]).splitlines()
        
        parts = git_log_release.split(" ", 1)
        last_hash = parts[0]
        
        # Get commits from last release to HEAD
        commits_output = run_cmd(["git", "log", f"{last_hash}..HEAD", "--format=%s"])
        commits = [c for c in commits_output.splitlines() if c.strip()]
        return last_hash, commits
    except subprocess.CalledProcessError:
        commits_output = run_cmd(["git", "log", "--format=%s"])
        return None, [c for c in commits_output.splitlines() if c.strip()]


def determine_bump_level(commits: list[str]) -> str:
    # Check for breaking changes or major hints
    for commit in commits:
        if "BREAKING CHANGE" in commit or "major:" in commit.lower():
            return "major"
    
    # Check for features (minor)
    for commit in commits:
        if commit.startswith("feat:") or "feat:" in commit:
            return "minor"
    
    # Default to patch for fixes, refactors, tests, docs, etc.
    return "patch"


def parse_version(version_str: str) -> tuple[int, int, int, int | None]:
    # Matches x.x.x or x.x.x-rcY or x.x.xrcY
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-?rc(\d+))?$", version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    major, minor, patch, rc = match.groups()
    return int(major), int(minor), int(patch), int(rc) if rc is not None else None


def bump_version_base(major: int, minor: int, patch: int, level: str) -> tuple[int, int, int]:
    if level == "major":
        return major + 1, 0, 0
    elif level == "minor":
        return major, minor + 1, 0
    elif level == "patch":
        return major, minor, patch + 1
    else:
        raise ValueError(f"Unknown bump level: {level}")


def update_files(new_pyproject_version: str, new_app_version: str):
    # Update pyproject.toml
    pyproject_content = PYPROJECT_PATH.read_text(encoding="utf-8")
    new_pyproject_content = re.sub(
        r'^(version\s*=\s*)"[^"]+"',
        f'\\1"{new_pyproject_version}"',
        pyproject_content,
        flags=re.MULTILINE
    )
    PYPROJECT_PATH.write_text(new_pyproject_content, encoding="utf-8")

    # Update betor/api/app.py
    app_content = APP_PATH.read_text(encoding="utf-8")
    new_app_content = re.sub(
        r'(version\s*=\s*)"[^"]+"',
        f'\\1"{new_app_version}"',
        app_content
    )
    APP_PATH.write_text(new_app_content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Automated version bump tool for BeTor")
    parser.add_argument("--rc", action="store_true", help="Create or increment a release candidate")
    parser.add_argument("--promote", action="store_true", help="Promote current release candidate to stable release")
    parser.add_argument("--level", choices=["patch", "minor", "major"], help="Force bump level")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without modifying files or git")
    args = parser.parse_args()

    current_version_str = get_current_version()
    major, minor, patch, current_rc = parse_version(current_version_str)

    last_hash, commits = get_commits_since_last_release()
    print(f"Versão atual: {current_version_str}")
    print(f"Último commit de release hash: {last_hash}")
    print(f"Total de commits desde a última release: {len(commits)}")

    bump_level = args.level or determine_bump_level(commits)
    print(f"Nível de bump determinado: {bump_level}")

    # Determine new version
    if args.promote:
        if current_rc is None:
            print("Erro: A versão atual não é um release candidate para ser promovida.", file=sys.stderr)
            sys.exit(1)
        # Promote: keep major.minor.patch without rc
        new_base = (major, minor, patch)
        new_rc = None
    elif args.rc:
        if current_rc is not None:
            # Already an RC, increment RC number
            new_base = (major, minor, patch)
            new_rc = current_rc + 1
        else:
            # Stable version, bump base and start rc0
            new_base = bump_version_base(major, minor, patch, bump_level)
            new_rc = 0
    else:
        # Normal release or transition from RC
        if current_rc is not None:
            # Promote RC to stable release
            new_base = (major, minor, patch)
            new_rc = None
        else:
            # Stable version bump
            new_base = bump_version_base(major, minor, patch, bump_level)
            new_rc = None

    # Construct version strings
    base_str = f"{new_base[0]}.{new_base[1]}.{new_base[2]}"
    if new_rc is not None:
        full_version = f"{base_str}-rc{new_rc}"
    else:
        full_version = base_str

    # FastAPI app version should never have rc suffix
    app_version = base_str

    print(f"Nova versão pyproject / commit / tag: {full_version}")
    print(f"Nova versão app FastAPI: {app_version}")

    if args.dry_run:
        print("[Dry-run] Nenhuma alteração foi aplicada.")
        return

    # Update files
    update_files(full_version, app_version)
    print("Arquivos atualizados com sucesso.")

    # Git operations
    run_cmd(["git", "add", str(PYPROJECT_PATH), str(APP_PATH)])
    
    # Check if poetry.lock changed or needs commit (optional, but poetry version modifies pyproject.toml)
    try:
        run_cmd(["git", "add", "poetry.lock"])
    except subprocess.CalledProcessError:
        pass

    commit_msg = f"release: {full_version}"
    tag_name = f"v{full_version}"

    run_cmd(["git", "commit", "-m", commit_msg])
    run_cmd(["git", "tag", tag_name])

    print(f"Commit criado: '{commit_msg}'")
    print(f"Tag criada: '{tag_name}'")
    print("Bump version concluído com sucesso!")


if __name__ == "__main__":
    main()
