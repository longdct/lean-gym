import json
import re
from typing import Any, Dict, List, Optional, Tuple
import os
from pathlib import Path
import tempfile
from loguru import logger
import pexpect
import gymnasium as gym

from .status import *
from .utils import get_all_possible_lean_chars


class LeanEnvREPL(gym.Env):

    def __init__(
        self,
        theorem: str,
        header: Optional[str] = None,
        workdir: Optional[Path] = None,
        lake_path: Optional[Path] = None,
        timeout: int = 600,
    ):
        # Properties
        theorem = theorem.strip()
        if theorem.endswith("sorry"):
            theorem = theorem[:-5].strip()
        if theorem.endswith("by"):
            theorem = theorem[:-2].strip()
        if not theorem.endswith(":="):
            theorem += " := "
        self.theorem = theorem
        self.header = header
        self.timeout = timeout
        if lake_path is None:
            lake_path = Path.home() / ".elan/bin/lake"
        self.lake_path = lake_path.as_posix()

        self.origin_dir = Path.cwd()

        if workdir is None:
            os.chdir("/tmp")
        else:
            os.chdir(workdir)

        lean_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".lean", delete=False, dir=workdir
        )
        lean_file.write(self._get_lean_code())
        self.leanfile_path = lean_file.name
        lean_file.close()

        # Observation space is the text of proof state and error messages
        # Which is a set of unicode characters
        self.observation_space = gym.spaces.Text(
            max_length=10000, charset=get_all_possible_lean_chars()
        )

        # Same for action space
        self.action_space = gym.spaces.Text(
            max_length=10000, charset=get_all_possible_lean_chars()
        )

        # Misc
        self.proc = None
        self.completed = False
        self.final_result = None
        ## state_archive: sid -> state, for quickly access node in tree search
        self.state_archive: dict = {}
        self.current_state: dict = {}

    def _get_lean_code(self) -> str:
        lean_code = ""
        lean_code += self.header
        lean_code += "\n\n"
        lean_code += self.theorem
        lean_code += " by\n  lean_dojo_repl\n  sorry\n\n"
        return lean_code

    def reset(self, seed: int = None, options: Optional[dict] = None) -> str:
        super().reset(seed=seed)
        if options is None:
            self._init_process()
            self.state_archive = {}
            self.current_state = {}

        if (
            options is not None
            and "sid" in options
            and options["sid"] in self.state_archive
        ):
            sid = options["sid"]
            self.current_state = {
                "sid": sid,
                "state": self.state_archive[sid],
            }
        else:
            res = json.loads(self._read_next_line()[0])
            state = self._post_process(res["tacticState"])
            sid = res["sid"]
            self.current_state = {"sid": sid, "state": state}
            self.state_archive[sid] = state
        return self.current_state["state"], {"sid": sid}

    def step(self, action: str):

        if self.completed:
            return self.final_result

        sid = self.current_state["sid"]
        req = json.dumps({"sid": sid, "cmd": action}, ensure_ascii=False)

        try:
            res = self._submit_request(req)
        except (TimeoutError, CrashError):
            observation = self.current_state["state"]
            reward = -1
            done = True
            truncated = True

            self.completed = True
            self.final_result = (observation, reward, done, truncated, {})
            return observation, reward, done, truncated, {}

        if res["error"] is not None:
            observation = res["error"]
            reward = -1
            done = True
            truncated = False
        elif res["tacticState"] == "no goals":
            observation = self._post_process(res["tacticState"])
            reward = 1
            done = True
            truncated = False
        else:
            observation = self._post_process(res["tacticState"])
            reward = 0
            done = False
            truncated = False

            self.state_archive[res["sid"]] = observation
            self.current_state = {"sid": res["sid"], "state": observation}

        if done:
            self.completed = True
            self.final_result = (observation, reward, done, truncated, {})

        return observation, reward, done, truncated, {}

    def close(self):
        if self.proc is not None:
            self.proc.close()
        # Delete the temporary Lean file
        os.remove(self.leanfile_path)
        os.chdir(self.origin_dir)

    def _init_process(self) -> None:
        cmd = f"{self.lake_path} env lean {self.leanfile_path}"
        if self.proc is not None:
            self.proc.close()
        self.proc = pexpect.spawn(
            cmd, timeout=self.timeout, maxread=1, encoding="utf-8", echo=False
        )

    def _post_process(self, tactic_state: str) -> str:
        """Post-process the pretty-printed tactic state.

        Args:
            tactic_state (str): _description_

        Returns:
            str: _description_
        """
        m = re.match(r"\d+ goals\n", tactic_state)
        if m is not None:
            return tactic_state[m.end() :]
        else:
            return tactic_state

    def _submit_request(self, req: str) -> Dict[str, Any]:
        """Submit a request to Lean and get the response.

        Args:
            req (str): _description_

        Raises:
            CrashError: _description_

        Returns:
            Dict[str, Any]: _description_
        """
        self._check_alive()
        logger.debug(req)
        self.proc.sendline(req)
        try:
            res, msg = self._read_next_line()
        except EOFError:
            raise CrashError("Unexpected EOF")
        try:
            result: Dict[str, Any] = json.loads(res)
        except json.decoder.JSONDecodeError:
            raise CrashError(f"Invalid JSON: {res}")

        result["message"] = msg
        return result

    def _check_alive(self) -> None:
        if self.proc.isalive():
            return
        exit_code = self.proc.exitstatus
        assert exit_code is not None
        if exit_code == 137:
            raise CrashError("OOM")
        else:
            raise CrashError(f"Unexpected exit code: {exit_code}")

    def _read_next_line(self) -> Tuple[str, str]:
        """Read the next line from `self.proc`.

        Raises:
            EOFError: _description_
            TimeoutError: _description_

        Returns:
            str: _description_
        """
        _REPL_PROMPT = "REPL>"
        msg: List[str] = []
        while True:
            try:
                index = self.proc.expect(["\n", f"{_REPL_PROMPT}.*?\n"])
                if index == 0:
                    if self.proc.before == "":
                        raise EOFError
                    else:
                        msg.append(self.proc.before.strip())
                        continue
                self._check_alive()
                res = self.proc.match.string[len(_REPL_PROMPT) :].strip()
                return res, "\n".join(msg) + self.proc.before
            except pexpect.EOF:
                raise EOFError
            except pexpect.TIMEOUT:
                logger.debug(f"Tactic timed out")
                raise TimeoutError()
