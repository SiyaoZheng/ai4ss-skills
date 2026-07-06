from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillDistributionTests(unittest.TestCase):
    def test_goal_cli_skills_have_required_frontmatter(self) -> None:
        for skill_name in ("goal-cli-project-setup", "goal-cli-template-author"):
            path = ROOT / "skills" / skill_name / "SKILL.md"
            text = path.read_text(encoding="utf-8")

            self.assertTrue(text.startswith("---\n"), path)
            self.assertRegex(text, rf"\nname: {re.escape(skill_name)}\n")
            self.assertRegex(text, r"\ndescription: .+\n")
            self.assertRegex(text, r"\nversion: .+\n")

    def test_llms_txt_points_agents_to_current_skill_entrypoints(self) -> None:
        text = (ROOT / "llms.txt").read_text(encoding="utf-8")

        self.assertIn("skills/goal-cli-project-setup/SKILL.md", text)
        self.assertIn("skills/goal-cli-template-author/SKILL.md", text)
        self.assertIn("THE THING is the finished result", text)

    def test_readme_and_skill_docs_link_the_distribution_files(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        docs = (ROOT / "docs" / "skills.md").read_text(encoding="utf-8")

        for text in (readme, docs):
            self.assertIn("goal-cli-project-setup", text)
            self.assertIn("goal-cli-template-author", text)
            self.assertIn("llms.txt", text)

    def test_agent_docs_use_current_heartbeat_budget_examples(self) -> None:
        paths = (
            ROOT / "llms.txt",
            ROOT / "skills" / "goal-cli-project-setup" / "SKILL.md",
            ROOT / "docs" / "skills.md",
        )

        for path in paths:
            text = path.read_text(encoding="utf-8")
            self.assertIn("goal-cli run --max-minutes 600", text, path)
            self.assertIn("goal-cli heartbeat install --every-minutes 30 --max-minutes 600", text, path)
            self.assertNotIn("goal-cli run --max-minutes 30", text, path)
            self.assertNotIn("goal-cli heartbeat install --every-minutes 30 --max-minutes 30", text, path)


if __name__ == "__main__":
    unittest.main()
