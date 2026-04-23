from __future__ import annotations

from pathlib import Path

from core.settings import Settings


DEFAULT_GUIDANCE_FILENAMES: tuple[str, ...] = (
    "meta-prompt-checklist-for-llm.md",
    "meta-prompt-harness-generator-v1.1.md",
    "prompt-engineering-guide.md",
    "thinking-framework-v2.md",
)
RESEARCH_RUNTIME_GUIDANCE_FILENAMES: tuple[str, ...] = (
    "research_runtime_guidance_v29lite.md",
)
ENGINEERING_DIR_NAMES: tuple[str, ...] = (
    "engineering",
    "\uc5d4\uc9c0\ub2c8\uc5b4\ub9c1",
)


def _read_prompt_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig", errors="ignore").strip()


def _ordered_guidance_paths(root: Path) -> list[Path]:
    return [path for name in DEFAULT_GUIDANCE_FILENAMES if (path := root / name).is_file()]


def _ordered_research_guidance_paths(root: Path) -> list[Path]:
    return [path for name in RESEARCH_RUNTIME_GUIDANCE_FILENAMES if (path := root / name).is_file()]


def _iter_candidate_guidance_roots(settings: Settings) -> list[Path]:
    roots: list[Path] = []
    configured_path = settings.default_guidance_prompt_path
    if configured_path is not None:
        roots.append(Path(configured_path))

    for base in (settings.workspace_root, settings.workspace_root.parent):
        for directory_name in ENGINEERING_DIR_NAMES:
            roots.append(base / directory_name)

    unique_roots: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        try:
            normalized = root.resolve(strict=False)
        except OSError:
            normalized = root
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_roots.append(root)
    return unique_roots


def _discover_default_guidance_paths(settings: Settings) -> list[Path]:
    best_match: list[Path] = []
    for root in _iter_candidate_guidance_roots(settings):
        if root.is_file():
            return [root]
        if not root.is_dir():
            continue
        paths = _ordered_guidance_paths(root)
        if len(paths) > len(best_match):
            best_match = paths
        if len(paths) == len(DEFAULT_GUIDANCE_FILENAMES):
            return paths
    return best_match


def _discover_research_guidance_paths(settings: Settings) -> list[Path]:
    if settings.pipeline_mode != "research":
        return []

    roots = [
        settings.workspace_root / "docs",
        settings.workspace_root.parent / "docs",
    ]
    paths: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        paths.extend(_ordered_research_guidance_paths(root))
    return paths


def _compose_guidance_documents(paths: list[Path]) -> str:
    if not paths:
        return ""
    sections: list[str] = [
        "Repository default guidance bundle.",
        "Treat these documents as shared standing instructions for planning, execution, and review.",
    ]
    for path in paths:
        content = _read_prompt_text(path)
        if not content:
            continue
        sections.extend(["", f"## {path.name}", content])
    return "\n".join(sections).strip()


def load_guidance_prompt(settings: Settings) -> str:
    path = settings.default_guidance_prompt_path
    if path is not None:
        prompt_path = Path(path)
        if prompt_path.exists() and prompt_path.is_file():
            return _read_prompt_text(prompt_path)

    paths = _discover_default_guidance_paths(settings)
    for research_path in _discover_research_guidance_paths(settings):
        if research_path not in paths:
            paths.append(research_path)
    return _compose_guidance_documents(paths)


def compose_system_prompt(base_prompt: str, guidance_prompt: str, *, section_name: str) -> str:
    if not guidance_prompt:
        return base_prompt
    return (
        f"{base_prompt}\n\n"
        "Repository prompt composition note.\n"
        "Use repository-local tools for deterministic lookups and canonical source identifiers.\n"
        "Use built-in web tools for current or external verification when available.\n"
        "Treat the following guidance bundle as standing instruction unless it conflicts with the explicit task.\n"
        f"Focus most on the parts relevant to: {section_name}.\n\n"
        f"{guidance_prompt}"
    )
