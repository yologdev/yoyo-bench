import json
import os
import shlex
from pathlib import Path, PurePosixPath
from typing import Any

from harbor.agents.installed.base import (
    BaseInstalledAgent,
    CliFlag,
    EnvVar,
    with_prompt_template,
)
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext
from harbor.models.trajectories import (
    Agent,
    FinalMetrics,
    Metrics,
    Observation,
    ObservationResult,
    Step,
    ToolCall,
    Trajectory,
)
from harbor.models.trial.paths import EnvironmentPaths


class Yoyo(BaseInstalledAgent):
    """
    Harbor agent adapter for yoyo — a self-evolving coding agent.

    Installs the yoyo binary, loads bench-specific skills and prompt,
    then runs yoyo in single-prompt mode against the benchmark task.
    """

    SUPPORTS_ATIF: bool = False

    _OUTPUT_FILENAME = "yoyo-output.txt"

    CLI_FLAGS = [
        CliFlag(
            "max_turns",
            cli="--max-turns",
            type="int",
            default=100,
            env_fallback="YOYO_MAX_TURNS",
        ),
        CliFlag(
            "provider",
            cli="--provider",
            type="str",
            default="anthropic",
            env_fallback="YOYO_PROVIDER",
        ),
        CliFlag(
            "fallback",
            cli="--fallback",
            type="str",
            env_fallback="YOYO_FALLBACK_PROVIDER",
        ),
        CliFlag(
            "thinking",
            cli="--thinking",
            type="str",
            default="high",
            env_fallback="YOYO_THINKING",
        ),
    ]

    ENV_VARS = []

    @staticmethod
    def name() -> str:
        return "yoyo"

    def get_version_command(self) -> str | None:
        return "yoyo --version"

    def parse_version(self, stdout: str) -> str:
        import re

        text = stdout.strip()
        match = re.search(r"(\d+\.\d+\.\d+)", text)
        if match:
            return match.group(1)
        return text

    async def install(self, environment: BaseEnvironment) -> None:
        # Install system dependencies (as root)
        await self.exec_as_root(
            environment,
            command=(
                "if command -v apk &> /dev/null; then"
                "  apk add --no-cache curl bash git;"
                " elif command -v apt-get &> /dev/null; then"
                "  apt-get update && apt-get install -y curl git;"
                " elif command -v yum &> /dev/null; then"
                "  yum install -y curl git;"
                " else"
                '  echo "Warning: No known package manager found" >&2;'
                " fi"
            ),
            env={"DEBIAN_FRONTEND": "noninteractive"},
        )

        # Upload pre-built yoyo binary into the container
        local_binary = Path(__file__).parent.parent / "bin" / "yoyo"
        remote_binary = "/usr/local/bin/yoyo"
        await environment.upload_file(local_binary, remote_binary)
        await self.exec_as_root(
            environment,
            command=f"chmod +x {remote_binary}",
        )

    @with_prompt_template
    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        escaped_instruction = shlex.quote(instruction)

        env = {}

        # API key — support Anthropic and other providers
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if anthropic_key:
            env["ANTHROPIC_API_KEY"] = anthropic_key

        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if openai_key:
            env["OPENAI_API_KEY"] = openai_key

        # Model override
        if self.model_name:
            provider_model = self.model_name
            if "/" in provider_model:
                # Harbor passes "provider/model" format
                parts = provider_model.split("/", 1)
                env["_YOYO_PROVIDER_HINT"] = parts[0]
            env["YOYO_MODEL"] = provider_model.split("/")[-1]

        # Merge declarative env vars
        env.update(self._resolved_env_vars)
        env = {k: v for k, v in env.items() if v}

        # Build CLI flags
        cli_flags = self.build_cli_flags()
        extra_flags = (cli_flags + " ") if cli_flags else ""

        # Model flag
        model_flag = ""
        if "YOYO_MODEL" in env:
            model_flag = f"--model {env.pop('YOYO_MODEL')} "

        # Provider hint from model string
        provider_hint = env.pop("_YOYO_PROVIDER_HINT", "")
        if provider_hint and "--provider" not in extra_flags:
            extra_flags = f"--provider {provider_hint} {extra_flags}"

        # Upload skills if they exist locally
        skills_dir = Path(__file__).parent.parent / "skills"
        if skills_dir.is_dir():
            for skill_path in skills_dir.rglob("SKILL.md"):
                relative = skill_path.relative_to(skills_dir)
                remote_path = f"/tmp/yoyo-skills/{relative}"
                content = skill_path.read_text()
                escaped_content = shlex.quote(content)
                await self.exec_as_agent(
                    environment,
                    command=f"mkdir -p $(dirname {remote_path}) && echo {escaped_content} > {remote_path}",
                    env=env,
                )

        skills_flag = ""
        if skills_dir.is_dir():
            skills_flag = "--skills /tmp/yoyo-skills "

        # Upload system prompt if it exists
        prompt_file = Path(__file__).parent.parent / "prompts" / "system_prompt.md"
        prompt_flag = ""
        if prompt_file.is_file():
            content = prompt_file.read_text()
            escaped_content = shlex.quote(content)
            await self.exec_as_agent(
                environment,
                command=f"echo {escaped_content} > /tmp/yoyo-system-prompt.md",
                env=env,
            )
            prompt_flag = "--system-file /tmp/yoyo-system-prompt.md "

        output_path = f"/logs/agent/{self._OUTPUT_FILENAME}"

        # Run yoyo in piped mode
        await self.exec_as_agent(
            environment,
            command=(
                f"yoyo --yes -p {escaped_instruction} "
                f"{extra_flags}{model_flag}{skills_flag}{prompt_flag}"
                f"2>&1 | tee {output_path}"
            ),
            env=env,
        )

    def populate_context_post_run(self, context: AgentContext) -> None:
        """Parse yoyo output and populate the agent context for scoring."""
        output_file = self.logs_dir / "agent" / self._OUTPUT_FILENAME
        if not output_file.exists():
            self.logger.warning("No yoyo output file found")
            return

        output = output_file.read_text()

        # Build a simple trajectory from the output
        steps = [
            Step(
                step_id=0,
                source="user",
                message="Task instruction provided via stdin",
            ),
            Step(
                step_id=1,
                source="agent",
                message=output,
            ),
        ]

        trajectory = Trajectory(
            agent=Agent(
                name="yoyo",
                version=self.version(),
            ),
            steps=steps,
            metrics=FinalMetrics(
                metrics=Metrics(
                    input_tokens=0,
                    output_tokens=0,
                    total_cost_usd=0.0,
                ),
            ),
        )

        context.trajectory = trajectory
        context.submission = output
