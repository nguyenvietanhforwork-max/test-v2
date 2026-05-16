"""Versioned prompt registry. Each prompt has a (name, version, template)."""

from dataclasses import dataclass
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent
ACTIVE = {
    "classification": "v1",
    "summarization": "v1",
    "wiki_enrichment": "v1",
    "report_generation": "v1",
}


@dataclass
class Prompt:
    name: str
    version: str
    template: str

    def format(self, **kwargs) -> str:
        return self.template.format(**kwargs)


def get_prompt(name: str) -> Prompt:
    version = ACTIVE[name]
    path = PROMPTS_DIR / name / f"{version}.md"
    return Prompt(name=name, version=version, template=path.read_text(encoding="utf-8"))
