from pathlib import Path

from core.prompting import (
    ENGINEERING_DIR_NAMES,
    RESEARCH_RUNTIME_GUIDANCE_FILENAMES,
    compose_system_prompt,
    load_guidance_prompt,
)
from core.settings import Settings


def test_load_guidance_prompt_reads_configured_file(tmp_path: Path) -> None:
    prompt_path = tmp_path / "guidance.md"
    prompt_path.write_text("# Guidance\nAlways test.\n", encoding="utf-8")
    settings = Settings(
        workspace_root=tmp_path,
        pipeline_db_path="outputs/test.db",
        anthropic_api_key="test-anthropic",
        openai_api_key="test-openai",
        default_guidance_prompt_path=prompt_path,
    )

    loaded = load_guidance_prompt(settings)

    assert "# Guidance" in loaded
    assert "Always test." in loaded


def test_compose_system_prompt_appends_guidance() -> None:
    combined = compose_system_prompt("Base prompt", "Shared guidance", section_name="testing")

    assert "Base prompt" in combined
    assert "Shared guidance" in combined
    assert "testing" in combined
    assert "repository-local tools" in combined
    assert "built-in web tools" in combined


def test_load_guidance_prompt_auto_discovers_engineering_bundle(tmp_path: Path) -> None:
    workspace = tmp_path / "Self_Working_pipeline"
    engineering = tmp_path / ENGINEERING_DIR_NAMES[-1]
    workspace.mkdir()
    engineering.mkdir()
    (engineering / "meta-prompt-checklist-for-llm.md").write_text("Checklist guidance", encoding="utf-8")
    (engineering / "meta-prompt-harness-generator-v1.1.md").write_text("Harness guidance", encoding="utf-8")
    (engineering / "prompt-engineering-guide.md").write_text("Prompt guide", encoding="utf-8")
    (engineering / "thinking-framework-v2.md").write_text("Thinking guide", encoding="utf-8")

    settings = Settings(
        workspace_root=workspace,
        pipeline_db_path="outputs/test.db",
        anthropic_api_key="test-anthropic",
        openai_api_key="test-openai",
    )

    loaded = load_guidance_prompt(settings)

    assert "Repository default guidance bundle." in loaded
    assert "meta-prompt-checklist-for-llm.md" in loaded
    assert "Checklist guidance" in loaded
    assert "Thinking guide" in loaded


def test_load_guidance_prompt_reads_bundle_from_configured_directory(tmp_path: Path) -> None:
    prompt_dir = tmp_path / "prompt-bundle"
    prompt_dir.mkdir()
    (prompt_dir / "meta-prompt-checklist-for-llm.md").write_text("Checklist guidance", encoding="utf-8")
    (prompt_dir / "prompt-engineering-guide.md").write_text("Prompt guide", encoding="utf-8")
    settings = Settings(
        workspace_root=tmp_path,
        pipeline_db_path="outputs/test.db",
        anthropic_api_key="test-anthropic",
        openai_api_key="test-openai",
        default_guidance_prompt_path=prompt_dir,
    )

    loaded = load_guidance_prompt(settings)

    assert "Repository default guidance bundle." in loaded
    assert "Checklist guidance" in loaded
    assert "Prompt guide" in loaded


def test_load_guidance_prompt_appends_research_runtime_guidance_in_research_mode(tmp_path: Path) -> None:
    workspace = tmp_path / "Self_Working_pipeline"
    docs = workspace / "docs"
    workspace.mkdir()
    docs.mkdir()
    (docs / RESEARCH_RUNTIME_GUIDANCE_FILENAMES[0]).write_text(
        "MC1-1 runtime guidance",
        encoding="utf-8",
    )
    settings = Settings(
        workspace_root=workspace,
        pipeline_db_path="outputs/test.db",
        anthropic_api_key="test-anthropic",
        openai_api_key="test-openai",
        pipeline_mode="research",
    )

    loaded = load_guidance_prompt(settings)

    assert "Repository default guidance bundle." in loaded
    assert RESEARCH_RUNTIME_GUIDANCE_FILENAMES[0] in loaded
    assert "MC1-1 runtime guidance" in loaded
