import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "knowledge_tool.py"


class KnowledgeToolCliTests(unittest.TestCase):
    def run_cli(self, *args: str, config_path: Path | None = None) -> dict:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        if config_path:
            env["KNOWLEDGE_TOOL_CONFIG"] = str(config_path)
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
        )
        return json.loads(result.stdout)

    def test_compacts_legacy_history_and_calculates_roadmap_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "learning"
            topic = root / "compose"
            topic.mkdir(parents=True)
            state = {
                "topic": "Compose",
                "slug": "compose",
                "mode": "topic",
                "learning_root": str(root),
                "learning_dir": str(topic),
                "current_step": "state_placement",
                "next_step": "Practice state ownership",
                "created_at": "2026-08-01T00:00:00+00:00",
                "updated_at": "2026-08-02T00:00:00+00:00",
                "mastery": [
                    {
                        "recorded_at": "2026-08-01T00:00:00+00:00",
                        "stage": "state_placement",
                        "score": 7,
                        "weak_concepts": ["ownership"],
                        "next_task": "retry",
                    },
                    {
                        "recorded_at": "2026-08-02T00:00:00+00:00",
                        "stage": "state_placement_apply",
                        "score": 9,
                        "weak_concepts": [],
                        "next_task": "advance",
                    },
                ],
            }
            (topic / "learning_state.json").write_text(
                json.dumps(state), encoding="utf-8"
            )
            (topic / "assessment.md").write_text("legacy log", encoding="utf-8")
            roadmap = {
                "goal": "Compose basics",
                "modules": [
                    {
                        "id": "state",
                        "title": "State",
                        "weight": 100,
                        "concepts": [
                            {
                                "id": "ownership",
                                "title": "State ownership",
                                "stage_patterns": ["state_placement"],
                            }
                        ],
                    }
                ],
            }
            roadmap_path = Path(temp) / "roadmap.json"
            roadmap_path.write_text(json.dumps(roadmap), encoding="utf-8")

            self.run_cli(
                "plan",
                "--slug",
                "compose",
                "--file",
                str(roadmap_path),
                "--root",
                str(root),
            )
            payload = self.run_cli(
                "compact", "--slug", "compose", "--root", str(root)
            )

            compact_state = json.loads(
                (topic / "learning_state.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("mastery", compact_state)
            self.assertEqual(
                len((topic / "assessment-history.jsonl").read_text(encoding="utf-8").splitlines()),
                2,
            )
            self.assertEqual(payload["resume_snapshot"]["course_coverage_percent"], 100)
            self.assertGreaterEqual(
                payload["resume_snapshot"]["learned_material_mastery_percent"], 80
            )
            self.assertTrue((topic / "assessment-archive.md").exists())

    def test_assess_records_concept_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "learning"
            self.run_cli(
                "init",
                "--topic",
                "Compose",
                "--slug",
                "compose",
                "--root",
                str(root),
            )
            payload = self.run_cli(
                "assess",
                "--slug",
                "compose",
                "--stage",
                "state_apply",
                "--score",
                "8",
                "--concept",
                "state-ownership",
                "--evidence",
                "code",
                "--next-task",
                "Next lesson",
                "--root",
                str(root),
            )
            self.assertEqual(payload["resume_snapshot"]["assessment_count"], 1)
            self.assertEqual(payload["resume_snapshot"]["applied_evidence_count"], 1)
            history = json.loads(
                (root / "compose" / "assessment-history.jsonl")
                .read_text(encoding="utf-8")
                .strip()
            )
            self.assertEqual(history["concepts"], ["state-ownership"])
            self.assertEqual(history["evidence"], "code")

    def test_checkpoint_advances_without_assessment(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "learning"
            self.run_cli(
                "init",
                "--topic",
                "Compose",
                "--slug",
                "compose",
                "--root",
                str(root),
            )
            payload = self.run_cli(
                "checkpoint",
                "--slug",
                "compose",
                "--step",
                "lesson_complete",
                "--next-task",
                "Write a code example",
                "--note",
                "The explanation was delivered without a quiz.",
                "--root",
                str(root),
            )
            self.assertEqual(payload["resume_snapshot"]["assessment_count"], 0)
            self.assertEqual(payload["resume_snapshot"]["current_step"], "lesson_complete")
            state = json.loads(
                (root / "compose" / "learning_state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(state["next_step"], "Write a code example")
            self.assertFalse((root / "compose" / "assessment-history.jsonl").exists())

    def test_new_topic_requires_storage_confirmation_without_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config_path = Path(temp) / "config.json"
            payload = self.run_cli(
                "init",
                "--topic",
                "Compose",
                config_path=config_path,
            )
            self.assertEqual(payload["status"], "needs_storage_confirmation")
            self.assertFalse(config_path.exists())

    def test_configured_root_is_used_across_working_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            config_path = temp_path / "config.json"
            root = temp_path / "global-learning"
            self.run_cli(
                "config",
                "--set-learning-root",
                str(root),
                config_path=config_path,
            )
            confirmation = self.run_cli(
                "init",
                "--topic",
                "Compose",
                "--slug",
                "compose",
                config_path=config_path,
            )
            initialized = self.run_cli(
                "init",
                "--topic",
                "Compose",
                "--slug",
                "compose",
                "--confirmed-root",
                config_path=config_path,
            )
            resumed = self.run_cli(
                "continue",
                "--query",
                "Compose",
                config_path=config_path,
            )
            self.assertEqual(
                confirmation["status"], "needs_new_topic_root_confirmation"
            )
            self.assertEqual(initialized["status"], "initialized")
            self.assertEqual(resumed["status"], "resume_match")
            self.assertTrue(Path(resumed["learning_dir"]).samefile(root / "compose"))

    def test_migrate_topic_preserves_source_and_sets_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            config_path = temp_path / "config.json"
            source_root = temp_path / "old-learning"
            target_root = temp_path / "new-learning"
            self.run_cli(
                "init",
                "--topic",
                "Compose",
                "--slug",
                "compose",
                "--root",
                str(source_root),
                config_path=config_path,
            )
            payload = self.run_cli(
                "migrate-topic",
                "--slug",
                "compose",
                "--source-root",
                str(source_root),
                "--target-root",
                str(target_root),
                "--set-default",
                config_path=config_path,
            )
            self.assertEqual(payload["status"], "topic_migrated")
            self.assertTrue((source_root / "compose" / "learning_state.json").exists())
            migrated_state = json.loads(
                (target_root / "compose" / "learning_state.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(migrated_state["learning_root"], str(target_root.resolve()))
            config = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(config["default_learning_root"], str(target_root.resolve()))


if __name__ == "__main__":
    unittest.main()
