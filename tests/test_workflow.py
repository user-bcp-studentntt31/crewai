"""Exercise the pipeline without calling Copilot or GitHub."""

import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import main as app
from crew.workflow import ROLES, STEPS, DATA_ROLES, build_tasks, workflow_steps, include_data


FEATURE = {
    "title": "Transfer funds",
    "description": "Transfer funds between accounts",
    "acceptance_criteria": ["Reject a transfer with insufficient funds"],
}


class WorkflowTests(unittest.TestCase):
    def test_each_role_builds_its_own_task(self):
        tasks = build_tasks(FEATURE)
        self.assertEqual(
            list(tasks),
            ["architect", "ai-engineer", "testing", "security", "chapter"],
        )
        for role in ROLES:
            self.assertIs(tasks[role.KEY].agent, role.agent)
            self.assertIn("Transfer funds", tasks[role.KEY].description)
            self.assertIn(FEATURE["description"], tasks[role.KEY].description)
            for criterion in FEATURE["acceptance_criteria"]:
                self.assertIn(criterion, tasks[role.KEY].description)
            self.assertTrue(Path(role.__file__).is_file())

    def test_pipeline_saves_all_roles_and_resumes(self):
        self.check_pipeline(False)

    def test_data_pipeline_saves_sql_passes_context_and_resumes(self):
        self.check_pipeline(True)

    def test_invalid_activation_is_rejected(self):
        with patch.dict("os.environ", {"CREWAI_INCLUDE_DATA": "maybe"}):
            with self.assertRaises(ValueError):
                include_data()

    def test_integrated_role_keeps_upstream_implementation_guidance(self):
        tasks = build_tasks(FEATURE)
        instructions = tasks["ai-engineer"].description
        for expected in ("Quarkus", "Angular", "parametriza", "autorización",
                         "carga", "navegación por teclado", "no inventes ejecuciones"):
            self.assertIn(expected, instructions)
        self.assertIn("AI Engineer", tasks["chapter"].description)
        self.assertNotIn("Backend, Frontend", tasks["chapter"].description)

    def test_data_retry_rejection_and_resume_keep_human_gate(self):
        self.check_pipeline(True, interrupt_data=True)

    def test_ai_engineer_retry_rejection_and_resume_keep_human_gate(self):
        self.check_pipeline(False, interrupt_engineer=True)

    def check_pipeline(self, with_data, interrupt_data=False, interrupt_engineer=False):
        roles = DATA_ROLES if with_data else ROLES
        steps = workflow_steps(with_data)
        calls = []

        def run(agent, task):
            key = next(role.KEY for role in roles if role.agent is agent)
            calls.append((key, task.description))
            if key == "data":
                return "Approved data contract.\n```sql\n-- migration.sql\nCREATE TABLE accounts (id INTEGER PRIMARY KEY);\n```"
            if key == "ai-engineer":
                return ("Integrated implementation.\n"
                        "```java\n// BalanceService.java\npackage pe.bcp.login.service;\npublic class BalanceService {}\n```\n"
                        "```typescript\n// balance.service.ts\nexport class BalanceService {}\n```\n"
                        "```html\n<!-- balance.component.html -->\n<p>Balance</p>\n```\n"
                        "```css\n/* balance.component.css */\np { color: black; }\n```")
            if key == "testing":
                return "Coverage report. NO EJECUTADO.\n```java\n// BalanceTest.java\npackage pe.bcp.login;\npublic class BalanceTest {}\n```"
            return f"Approved output from {key}. No model was called."

        with tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict("os.environ", {"CREWAI_INCLUDE_DATA": str(with_data).lower()}))
            output = Path(tmp)
            stack.enter_context(patch.object(app, "OUTPUT_DIR", output))
            stack.enter_context(
                patch.object(app, "CHECKPOINT_FILE", output / ".checkpoint.json")
            )
            stack.enter_context(patch.object(app, "proj_tools", return_value=[]))
            stack.enter_context(
                patch.object(
                    app,
                    "list_projects",
                    return_value=[{"id": "P1", "title": "Team backlog"}],
                )
            )
            stack.enter_context(
                patch.object(
                    app,
                    "list_project_items",
                    return_value=[{"title": FEATURE["title"]}],
                )
            )
            stack.enter_context(
                patch.object(app, "get_feature_from_item", return_value=FEATURE)
            )
            stack.enter_context(patch.object(app, "run_step", side_effect=run))
            data_decisions = iter([("r", "Add a uniqueness constraint"), ("n", "")])
            engineer_decisions = iter([("r", "Fix the API contract"), ("n", "")])
            def approve(label, result):
                if interrupt_data and label == "Datos y persistencia":
                    decision = next(data_decisions, ("s", ""))
                    if decision[0] != "s":
                        self.assertFalse((output / "specs/data_spec.md").exists())
                        self.assertFalse((output / "db/migration.sql").exists())
                    return decision
                if interrupt_engineer and label == "AI Engineer":
                    decision = next(engineer_decisions, ("s", ""))
                    if decision[0] != "s":
                        self.assertFalse((output / "specs" / "ai_engineer_spec.md").exists())
                        self.assertFalse((output / "backend-quarkus" / "src" / "main" / "java" / "pe" / "bcp" / "login" / "service" / "BalanceService.java").exists())
                        self.assertFalse((output / "frontend-angular" / "src" / "app" / "auth" / "balance.service.ts").exists())
                    return decision
                return "s", ""
            stack.enter_context(patch.object(app, "hitl_approve", side_effect=approve))
            stack.enter_context(patch("builtins.input", return_value="1"))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            if interrupt_data or interrupt_engineer:
                with self.assertRaises(SystemExit):
                    app.main()
                rejected = json.loads((output / ".checkpoint.json").read_text())
                if interrupt_data:
                    self.assertEqual(rejected["steps"]["data"]["status"], "rejected")
                    self.assertNotIn("ai-engineer", rejected["steps"])
                    self.assertIn("Add a uniqueness constraint", calls[2][1])
                else:
                    self.assertEqual(rejected["steps"]["ai-engineer"]["status"], "rejected")
                    self.assertNotIn("testing", rejected["steps"])
                    self.assertIn("Fix the API contract", calls[2][1])
            app.main()

            expected = [role.KEY for role in roles]
            if interrupt_data:
                expected[1:2] = ["data", "data", "data"]
            if interrupt_engineer:
                expected[1:2] = ["ai-engineer", "ai-engineer", "ai-engineer"]
            self.assertEqual([key for key, _ in calls], expected)
            for key, _, _, spec, _ in steps:
                self.assertTrue((output / "specs" / spec).is_file(), key)
            self.assertTrue(
                (
                    output
                    / "backend-quarkus/src/test/java/pe/bcp/login/BalanceTest.java"
                ).is_file()
            )
            self.assertTrue((output / "backend-quarkus/src/main/java/pe/bcp/login/service/BalanceService.java").is_file())
            self.assertTrue((output / "frontend-angular/src/app/auth/balance.service.ts").is_file())
            self.assertTrue((output / "frontend-angular/src/app/auth/balance.component.html").is_file())
            self.assertTrue((output / "frontend-angular/src/app/auth/balance.component.css").is_file())
            testing_prompt = next(prompt for key, prompt in calls if key == "testing")
            self.assertIn("BalanceService.java", testing_prompt)
            self.assertIn("balance.service.ts", testing_prompt)
            chapter_prompt = calls[-1][1]
            self.assertIn("Integrated implementation", chapter_prompt)
            self.assertIn("BalanceService.java", chapter_prompt)
            self.assertIn("balance.service.ts", chapter_prompt)
            self.assertIn("Coverage report", chapter_prompt)
            self.assertIn("Approved output from security", chapter_prompt)
            checkpoint = json.loads((output / ".checkpoint.json").read_text())
            self.assertEqual(len(checkpoint["steps"]), len(roles))
            self.assertEqual(checkpoint["workflow_version"], app.WORKFLOW_VERSION)
            if with_data:
                self.assertEqual(list(dict.fromkeys(key for key, _ in calls))[:3], ["architect", "data", "ai-engineer"])
                engineer_prompt = next(prompt for key, prompt in calls if key == "ai-engineer")
                self.assertIn("Approved data contract", engineer_prompt)
                self.assertIn("No regeneres sus archivos SQL", engineer_prompt)
                self.assertIn("Approved data contract", chapter_prompt)
                self.assertTrue((output / "db/migration.sql").is_file())
            self.assertTrue(
                all(
                    step["status"] == "approved"
                    for step in checkpoint["steps"].values()
                )
            )

            generated_java = output / "backend-quarkus/src/main/java/pe/bcp/login/service/BalanceService.java"
            generated_ts = output / "frontend-angular/src/app/auth/balance.service.ts"
            generated_java.unlink()
            generated_ts.unlink()
            app.main()
            self.assertEqual(
                len(calls), len(expected), "Approved steps must not call the model again"
            )
            self.assertTrue(generated_java.is_file())
            self.assertTrue(generated_ts.is_file())
            before = (output / ".checkpoint.json").read_text()
            with patch.dict("os.environ", {"CREWAI_INCLUDE_DATA": str(not with_data).lower()}):
                with self.assertRaises(SystemExit) as stopped:
                    app.main()
                self.assertEqual(stopped.exception.code, 1)
            self.assertEqual((output / ".checkpoint.json").read_text(), before)

    def test_legacy_checkpoint_is_rejected_without_overwriting(self):
        for steps in (
            {"architect": {"status": "approved", "output": "Old architecture"}},
            {"backend": {"status": "approved", "output": "Old backend"},
             "frontend": {"status": "approved", "output": "Old frontend"},
             "testing": {"status": "approved", "output": "Old tests"}},
        ):
            with self.subTest(steps=steps), tempfile.TemporaryDirectory() as tmp, contextlib.ExitStack() as stack:
                output = Path(tmp)
                checkpoint = output / ".checkpoint.json"
                checkpoint.write_text(json.dumps({"feature_title": FEATURE["title"], "steps": steps}))
                before = checkpoint.read_text()
                stack.enter_context(patch.dict("os.environ", {"CREWAI_INCLUDE_DATA": "false"}))
                stack.enter_context(patch.object(app, "OUTPUT_DIR", output))
                stack.enter_context(patch.object(app, "CHECKPOINT_FILE", checkpoint))
                stack.enter_context(patch.object(app, "proj_tools", return_value=[]))
                stack.enter_context(patch.object(app, "list_projects", return_value=[{"id": "P1", "title": "Backlog"}]))
                stack.enter_context(patch.object(app, "list_project_items", return_value=[{"title": FEATURE["title"]}]))
                stack.enter_context(patch.object(app, "get_feature_from_item", return_value=FEATURE))
                runner = stack.enter_context(patch.object(app, "run_step"))
                stack.enter_context(patch("builtins.input", return_value="1"))
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                with self.assertRaises(SystemExit) as stopped:
                    app.main()
                self.assertEqual(stopped.exception.code, 1)
                runner.assert_not_called()
                self.assertEqual(checkpoint.read_text(), before)
                self.assertFalse((output / "backend-quarkus").exists())


if __name__ == "__main__":
    unittest.main()
