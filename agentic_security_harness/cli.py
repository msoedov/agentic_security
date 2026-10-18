"""Fire commands. stdout is a machine-readable protocol; diagnostics go to stderr."""

from dataclasses import asdict
import contextlib
import json
import sys

from agentic_security_harness.deciders import Decision
from agentic_security_harness.loop import Harness, replay
from agentic_security_harness.runlog import ROOT, RunLog


def output(data):
    print(json.dumps(data, ensure_ascii=True, allow_nan=False), flush=True)


class CLI:
    def run(self, spec, policy="default", decider="rules", seed=0, budget_usd=None):
        stream = sys.stdout
        emit = lambda event: print(json.dumps(event), file=stream, flush=True)
        with contextlib.redirect_stdout(sys.stderr):
            harness = Harness.create(spec, policy, decider, seed, budget_usd, emit)
            with harness.log.lock():
                code = harness.run()
        raise SystemExit(code)

    def step(self, run):
        with RunLog(run).lock() as log, contextlib.redirect_stdout(sys.stderr):
            harness = Harness(log)
            pending = harness.step()
        if pending is None:
            raise SystemExit(3)
        output(pending)

    def decide(self, run, action, reason=""):
        with RunLog(run).lock() as log:
            harness = Harness(log)
            if harness.state.finished:
                raise ValueError("Run is finished")
            harness.decide(Decision(str(action), str(reason)))
        output({"ok": True, "run_id": log.path.name, "action": action})

    def replay(self, run):
        with RunLog(run).lock() as log:
            code = replay(log, output)
        raise SystemExit(code)

    def report(self, run, o=None):
        from agentic_security_harness.report import write_report

        with RunLog(run).lock() as log:
            report = write_report(log, o)
        output(asdict(report))

    def ls(self):
        if ROOT.exists():
            for path in sorted(ROOT.iterdir()):
                if path.is_dir():
                    with RunLog(path).lock() as log:
                        harness = Harness(log)
                        output(
                            {
                                "run_id": path.name,
                                "path": str(path),
                                "status": harness.state.finished or "pending",
                                "attempts": len(harness.state.attempts),
                                "cost_usd": harness.state.cost,
                            }
                        )


def main():
    import fire

    try:
        fire.Fire(CLI())
    except (Exception, KeyboardInterrupt) as exc:
        print(f"agesec: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
