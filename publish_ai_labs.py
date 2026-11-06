"""Publica el contenido de ./output en el repo hermano ../ai-labs: rama + commit + push + PR."""
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
AI_LABS_DIR = Path(os.environ.get("AI_LABS_DIR", BASE_DIR.parent / "ai-labs")).resolve()
BASE_BRANCH = os.environ.get("AI_LABS_BASE_BRANCH", "main")

PR_BODY = """## Cambio

Artefactos generados por el flujo CrewAI para: {title}.
Incluye specs, backend-quarkus, frontend-angular y checkpoint del flujo (copiados desde `crewai/output`).

## Comprobación

Pendiente: los artefactos son salida de agentes aprobada paso a paso (HITL) en CrewAI; no se han ejecutado builds ni tests sobre esta rama.

## Revisión humana

Pendiente de revisión por la persona revisora. La salida de un agente no sustituye esta revisión.
"""


def _run(args: list[str], cwd: Path, check: bool = True) -> str:
    res = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if check and res.returncode != 0:
        raise RuntimeError(f"{' '.join(args)}\n{res.stderr.strip() or res.stdout.strip()}")
    return res.stdout.strip()


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:40].strip("-") or "feature"


def _copy_output(dest: Path) -> int:
    count = 0
    for src in OUTPUT_DIR.rglob("*"):
        if src.is_dir() or "__pycache__" in src.parts:
            continue
        target = dest / src.relative_to(OUTPUT_DIR)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        count += 1
    return count


def publish(feature_title: str) -> str | None:
    """Devuelve la URL del PR o None si no había cambios. Lanza RuntimeError ante fallos."""
    if not (AI_LABS_DIR / ".git").exists():
        raise RuntimeError(f"No existe un repo git en {AI_LABS_DIR}")
    if not OUTPUT_DIR.exists():
        raise RuntimeError("No existe la carpeta output/")

    if _run(["git", "status", "--porcelain", "--untracked-files=no"], AI_LABS_DIR):
        raise RuntimeError("ai-labs tiene cambios sin commitear; confírmalos o guárdalos antes de publicar.")

    original = _run(["git", "branch", "--show-current"], AI_LABS_DIR)
    branch = f"feature/crewai-output-{_slug(feature_title)}"
    if _run(["git", "branch", "--list", branch], AI_LABS_DIR):
        branch += time.strftime("-%Y%m%d%H%M%S")

    _run(["git", "fetch", "origin", BASE_BRANCH], AI_LABS_DIR)
    _run(["git", "checkout", "-b", branch, f"origin/{BASE_BRANCH}"], AI_LABS_DIR)
    try:
        n = _copy_output(AI_LABS_DIR)
        print(f"  · {n} archivos copiados a {AI_LABS_DIR}")
        _run(["git", "add", "-A", "--", "."], AI_LABS_DIR)
        if not _run(["git", "status", "--porcelain"], AI_LABS_DIR):
            print("  · Sin cambios respecto a origin/%s; no se crea PR." % BASE_BRANCH)
            return None
        _run(["git", "commit", "-m",
              f"feat: artefactos generados por CrewAI para {feature_title}\n\n"
              "Incluye backend-quarkus, frontend-angular, specs y checkpoint del flujo.\n\n"
              "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"], AI_LABS_DIR)
        _run(["git", "push", "-u", "origin", branch], AI_LABS_DIR)
        return _run(["gh", "pr", "create", "--base", BASE_BRANCH, "--head", branch,
                     "--title", f"feat: artefactos generados por CrewAI para {feature_title}",
                     "--body", PR_BODY.format(title=feature_title)], AI_LABS_DIR)
    finally:
        if original:
            _run(["git", "checkout", original], AI_LABS_DIR, check=False)
