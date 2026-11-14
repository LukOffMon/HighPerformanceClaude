"""Shared project detection for repo_brief.py and checks.py.

Standard library only (Python 3.8+). Never executes project code; only reads files.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

IGNORED_DIRS = {
    ".git", "node_modules", ".venv", "venv", "env", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "dist", "build", "out", ".next", ".nuxt",
    ".svelte-kit", ".turbo", ".cache", "coverage", "target", "vendor", ".idea",
    ".vscode", ".gradle", "Pods", ".expo", ".parcel-cache", ".tox", "site-packages",
}

LANG_BY_EXT = {
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".py": "Python", ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin",
    ".kts": "Kotlin", ".swift": "Swift", ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
    ".c": "C", ".h": "C/C++ header", ".cpp": "C++", ".cc": "C++", ".hpp": "C++",
    ".dart": "Dart", ".lua": "Lua", ".luau": "Luau", ".ex": "Elixir", ".exs": "Elixir",
    ".scala": "Scala", ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell",
    ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro", ".html": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".sql": "SQL", ".prisma": "Prisma",
    ".tf": "Terraform", ".sol": "Solidity", ".r": "R", ".jl": "Julia", ".zig": "Zig",
    ".md": "Markdown", ".mdx": "MDX", ".ipynb": "Notebook",
}

BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip", ".gz", ".tar",
    ".woff", ".woff2", ".ttf", ".otf", ".mp3", ".mp4", ".mov", ".wav", ".so", ".dylib",
    ".dll", ".exe", ".bin", ".lockb", ".jar", ".class", ".pyc", ".wasm", ".sqlite", ".db",
}

GENERATED_HINTS = ("lock", ".min.", "generated", "__snapshots__", ".snap", "bundle")


def run(cmd: List[str], cwd: Path, timeout: int = 10) -> Optional[str]:
    """Run a read-only helper command (git) and return stdout, or None on failure."""
    try:
        res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return None
    return res.stdout if res.returncode == 0 else None


def is_git_repo(root: Path) -> bool:
    return run(["git", "rev-parse", "--is-inside-work-tree"], root) is not None


def list_files(root: Path, limit: int = 50000) -> List[Path]:
    """Tracked + untracked-but-not-ignored files when in git, else a filtered walk."""
    files: List[Path] = []
    if is_git_repo(root):
        out = run(["git", "ls-files", "-co", "--exclude-standard"], root, timeout=30)
        if out is not None:
            for line in out.splitlines():
                if not line:
                    continue
                parts = Path(line).parts
                if any(p in IGNORED_DIRS for p in parts[:-1]):
                    continue
                files.append(Path(line))
                if len(files) >= limit:
                    break
            return files
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]
        for name in filenames:
            files.append(Path(dirpath, name).relative_to(root))
            if len(files) >= limit:
                return files
    return files


def read_text(path: Path, max_bytes: int = 400_000) -> Optional[str]:
    try:
        if path.stat().st_size > max_bytes:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def load_json(path: Path) -> Optional[dict]:
    text = read_text(path)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


# ---------------------------------------------------------------- JS / TS

def js_package_manager(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return "bun"
    if (root / "yarn.lock").exists():
        return "yarn"
    pkg = load_json(root / "package.json") or {}
    pm = str(pkg.get("packageManager", ""))
    for name in ("pnpm", "yarn", "bun"):
        if pm.startswith(name):
            return name
    return "npm"


def js_run(pm: str, script: str) -> str:
    if pm == "npm":
        return f"npm run {script} --silent"
    if pm == "bun":
        return f"bun run {script}"
    return f"{pm} {script}"


def js_exec(pm: str) -> str:
    return {"pnpm": "pnpm exec", "yarn": "yarn", "bun": "bunx"}.get(pm, "npx --no-install")


JS_FRAMEWORKS = [
    ("next", "Next.js"), ("nuxt", "Nuxt"), ("@remix-run/react", "Remix"), ("astro", "Astro"),
    ("@sveltejs/kit", "SvelteKit"), ("svelte", "Svelte"), ("vue", "Vue"), ("react-native", "React Native"),
    ("expo", "Expo"), ("react", "React"), ("solid-js", "Solid"), ("@angular/core", "Angular"),
    ("vite", "Vite"), ("electron", "Electron"), ("express", "Express"), ("fastify", "Fastify"),
    ("hono", "Hono"), ("@nestjs/core", "NestJS"), ("prisma", "Prisma"), ("@prisma/client", "Prisma"),
    ("drizzle-orm", "Drizzle"), ("mongoose", "Mongoose"), ("tailwindcss", "Tailwind"),
    ("@supabase/supabase-js", "Supabase"), ("firebase", "Firebase"), ("stripe", "Stripe"),
    ("zod", "Zod"), ("@tanstack/react-query", "TanStack Query"), ("redux", "Redux"),
    ("zustand", "Zustand"), ("three", "Three.js"), ("phaser", "Phaser"), ("typescript", "TypeScript"),
    ("vitest", "Vitest"), ("jest", "Jest"), ("@playwright/test", "Playwright"), ("cypress", "Cypress"),
    ("eslint", "ESLint"), ("@biomejs/biome", "Biome"), ("prettier", "Prettier"), ("turbo", "Turborepo"),
]


def js_stack(pkg: dict) -> List[str]:
    deps: Dict[str, str] = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        section = pkg.get(key)
        if isinstance(section, dict):
            deps.update({str(k): str(v) for k, v in section.items()})
    seen: List[str] = []
    for dep, label in JS_FRAMEWORKS:
        if dep in deps and label not in seen:
            version = deps[dep].lstrip("^~>=<")
            seen.append(f"{label} {version}" if version and version[0].isdigit() else label)
    return seen


# ---------------------------------------------------------------- Python

def py_runner(root: Path) -> str:
    if (root / "uv.lock").exists() and shutil.which("uv"):
        return "uv run "
    if (root / "poetry.lock").exists() and shutil.which("poetry"):
        return "poetry run "
    if (root / "Pipfile.lock").exists() and shutil.which("pipenv"):
        return "pipenv run "
    return ""


def py_config_text(root: Path) -> str:
    chunks = []
    for name in ("pyproject.toml", "setup.cfg", "tox.ini", "requirements.txt",
                 "requirements-dev.txt", "requirements/dev.txt", "Pipfile"):
        text = read_text(root / name)
        if text:
            chunks.append(text)
    return "\n".join(chunks)


PY_LIBS = [
    ("django", "Django"), ("fastapi", "FastAPI"), ("flask", "Flask"), ("starlette", "Starlette"),
    ("sqlalchemy", "SQLAlchemy"), ("pydantic", "Pydantic"), ("celery", "Celery"),
    ("pandas", "pandas"), ("numpy", "NumPy"), ("polars", "Polars"), ("torch", "PyTorch"),
    ("tensorflow", "TensorFlow"), ("scikit-learn", "scikit-learn"), ("anthropic", "Anthropic SDK"),
    ("openai", "OpenAI SDK"), ("langchain", "LangChain"), ("streamlit", "Streamlit"),
    ("typer", "Typer"), ("click", "Click"), ("httpx", "httpx"), ("requests", "requests"),
    ("playwright", "Playwright"), ("pytest", "pytest"), ("ruff", "Ruff"), ("mypy", "mypy"),
    ("pyright", "Pyright"), ("black", "Black"),
]


def py_stack(text: str) -> List[str]:
    low = text.lower()
    out = []
    for dep, label in PY_LIBS:
        if re.search(rf"(^|[\s\"'\[,]){re.escape(dep)}([\s\"'=<>~!\[,;]|$)", low, re.M):
            out.append(label)
    return out


# ---------------------------------------------------------------- Make / just

def make_targets(root: Path) -> List[str]:
    text = read_text(root / "Makefile") or read_text(root / "makefile") or ""
    targets = re.findall(r"^([A-Za-z0-9][A-Za-z0-9_.-]*):(?!=)", text, re.M)
    return sorted({t for t in targets if not t.startswith(".")})


def just_recipes(root: Path) -> List[str]:
    text = read_text(root / "justfile") or read_text(root / "Justfile") or ""
    return sorted(set(re.findall(r"^([A-Za-z0-9][A-Za-z0-9_-]*)\s*(?:[^:=\n]*)?:(?!=)", text, re.M)))


# ---------------------------------------------------------------- checks

Check = Tuple[str, str, str]  # (category, command, source)

CATEGORY_ORDER = ["typecheck", "lint", "test", "build"]

SCRIPT_PATTERNS = {
    "typecheck": [r"^typecheck$", r"^type-check$", r"^check-types$", r"^types$", r"^tsc$", r"^check$"],
    "lint": [r"^lint$", r"^eslint$", r"^biome$", r"^lint:check$"],
    "test": [r"^test$", r"^test:unit$", r"^unit$", r"^vitest$", r"^jest$"],
    "build": [r"^build$"],
}


def _pick_script(names: List[str], category: str) -> Optional[str]:
    for pattern in SCRIPT_PATTERNS[category]:
        for name in names:
            if re.match(pattern, name):
                return name
    return None


def detect_checks(root: Path) -> List[Check]:
    """Return ordered verification commands for the project rooted at `root`."""
    found: Dict[str, Check] = {}

    def add(cat: str, cmd: str, src: str) -> None:
        if cat not in found:
            found[cat] = (cat, cmd, src)

    # 1. Explicit task runners first: they encode the project's intent.
    targets = make_targets(root)
    for cat, names in (("typecheck", ["typecheck", "type-check", "types"]), ("lint", ["lint"]),
                       ("test", ["test", "tests"]), ("build", ["build"])):
        for name in names:
            if name in targets and shutil.which("make"):
                add(cat, f"make {name}", "Makefile")
                break
    recipes = just_recipes(root)
    for cat, names in (("typecheck", ["typecheck"]), ("lint", ["lint"]), ("test", ["test"]), ("build", ["build"])):
        for name in names:
            if name in recipes and shutil.which("just"):
                add(cat, f"just {name}", "justfile")
                break

    # 2. package.json scripts.
    pkg = load_json(root / "package.json")
    if pkg is not None:
        pm = js_package_manager(root)
        scripts = pkg.get("scripts") if isinstance(pkg.get("scripts"), dict) else {}
        names = list(scripts.keys())
        for cat in CATEGORY_ORDER:
            name = _pick_script(names, cat)
            if not name:
                continue
            body = str(scripts[name])
            if cat == "test" and "no test specified" in body:
                continue
            if re.search(r"--watch\b|\bwatch\b", body) and cat in ("test", "typecheck"):
                continue  # watch mode would hang a non-interactive session
            # checks.py runs with CI=1, which makes vitest/jest run once instead of watching.
            add(cat, js_run(pm, name), f"package.json:{name}")
        if "typecheck" not in found and (root / "tsconfig.json").exists():
            add("typecheck", f"{js_exec(pm)} tsc --noEmit --pretty false", "tsconfig.json")

    # 3. Python.
    py_text = py_config_text(root)
    has_py = bool(py_text) or any((root / n).exists() for n in ("setup.py", "manage.py"))
    if has_py:
        runner = py_runner(root)
        low = py_text.lower()
        if "[tool.mypy]" in low or (root / "mypy.ini").exists():
            add("typecheck", f"{runner}mypy .", "mypy config")
        elif "[tool.pyright]" in low or (root / "pyrightconfig.json").exists():
            add("typecheck", f"{runner}pyright", "pyright config")
        if "[tool.ruff" in low or (root / "ruff.toml").exists() or (root / ".ruff.toml").exists():
            add("lint", f"{runner}ruff check . --output-format concise", "ruff config")
        elif "flake8" in low or (root / ".flake8").exists():
            add("lint", f"{runner}flake8", "flake8 config")
        if (root / "manage.py").exists() and "pytest" not in low:
            add("test", f"{runner}python manage.py test", "manage.py")
        elif ("pytest" in low or (root / "tests").is_dir() or (root / "test").is_dir()
              or (root / "pytest.ini").exists() or (root / "conftest.py").exists()):
            add("test", f"{runner}python -m pytest -q -x --tb=short", "pytest")

    # 4. Go / Rust / others.
    if (root / "go.mod").exists():
        add("typecheck", "go vet ./...", "go.mod")
        add("test", "go test ./...", "go.mod")
        add("build", "go build ./...", "go.mod")
    if (root / "Cargo.toml").exists():
        add("typecheck", "cargo check -q", "Cargo.toml")
        add("lint", "cargo clippy -q -- -D warnings", "Cargo.toml")
        add("test", "cargo test -q", "Cargo.toml")
    if (root / "gradlew").exists():
        add("test", "./gradlew test -q", "gradlew")
        add("build", "./gradlew build -x test -q", "gradlew")
    elif (root / "pom.xml").exists():
        add("test", "mvn -q test", "pom.xml")
    if any(root.glob("*.sln")) or any(root.glob("*.csproj")):
        add("build", "dotnet build --nologo -v q", ".NET")
        add("test", "dotnet test --nologo -v q", ".NET")
    if (root / "Gemfile").exists():
        gem = read_text(root / "Gemfile") or ""
        if "rubocop" in gem:
            add("lint", "bundle exec rubocop", "Gemfile")
        if "rspec" in gem:
            add("test", "bundle exec rspec", "Gemfile")
        elif (root / "bin" / "rails").exists():
            add("test", "bin/rails test", "Gemfile")
    if (root / "composer.json").exists():
        if (root / "vendor" / "bin" / "phpstan").exists():
            add("typecheck", "vendor/bin/phpstan analyse --no-progress", "composer.json")
        if (root / "vendor" / "bin" / "pest").exists():
            add("test", "vendor/bin/pest", "composer.json")
        elif (root / "vendor" / "bin" / "phpunit").exists():
            add("test", "vendor/bin/phpunit", "composer.json")
    if (root / "Package.swift").exists():
        add("build", "swift build", "Package.swift")
        add("test", "swift test", "Package.swift")
    if (root / "pubspec.yaml").exists():
        add("lint", "dart analyze", "pubspec.yaml")
        add("test", "flutter test" if "flutter" in (read_text(root / "pubspec.yaml") or "") else "dart test",
            "pubspec.yaml")

    return [found[c] for c in CATEGORY_ORDER if c in found]
