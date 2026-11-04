"""Complete expanded contract coverage with bounded retries and an execution journal."""

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from asktrace import contract_batches, contracts


def main():
    root = Path.cwd()
    parent = root / "runs/pncp-74d68096-1e27-451d-b423-f8cded554d54/manifest.json"
    folder = root / "runs" / ("contracts-completion-" + str(uuid4()))
    folder.mkdir()
    journal = {
        "started_at": datetime.now(UTC).isoformat(),
        "parent": parent.relative_to(root).as_posix(),
        "status": "running",
        "interval_seconds": 1,
        "max_consecutive_failed_batches": 3,
        "reports": [],
    }

    def checkpoint():
        temporary = folder / "progress.tmp"
        temporary.write_text(
            json.dumps(journal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
        )
        temporary.replace(folder / "progress.json")

    checkpoint()
    failures = 0
    try:
        while True:

            def collector(root, parent, limit, offset):
                print(f"Starting batch offset={offset} selected={limit}", flush=True)
                started = time.monotonic()
                done = 0

                def transport(url):
                    nonlocal done
                    result = contracts.fetch(url)
                    done += 1
                    if done % 25 == 0:
                        print(
                            f"Batch offset={offset}: {done} pages observed; "
                            f"elapsed={round(time.monotonic() - started)}s",
                            flush=True,
                        )
                    return result

                path = contracts.collect(
                    root, parent, limit, transport=transport, interval=1, offset=offset
                )
                manifest = json.loads(path.read_bytes())
                print(
                    f"Batch offset={offset}: {manifest['status']}; quality={manifest['quality']}",
                    flush=True,
                )
                return path

            report = contract_batches.resume(root, parent, max_batches=20, collector=collector)
            data = json.loads(report.read_bytes())
            journal["reports"].append(
                {
                    "path": report.relative_to(root).as_posix(),
                    "status": data["status"],
                    "covered": data["covered_distinct_purchases"],
                    "remaining": data["remaining_eligible"],
                    "contracts": data["distinct_contracts"],
                }
            )
            checkpoint()
            print("Consolidated:", journal["reports"][-1], flush=True)
            if data["remaining_eligible"] == 0:
                journal["status"] = "complete"
                break
            if data["status"] == "needs_review":
                failures += 1
                if failures >= 3:
                    journal["status"] = "incomplete_after_bounded_failures"
                    break
                print("Waiting 30 seconds before a bounded retry of the pending batch.", flush=True)
                time.sleep(30)
            else:
                failures = 0
    except BaseException as error:
        journal["status"] = "interrupted_or_failed"
        journal["error_type"] = type(error).__name__
        raise
    finally:
        journal["finished_at"] = datetime.now(UTC).isoformat()
        checkpoint()
        print("Completion journal:", folder.relative_to(root), flush=True)


if __name__ == "__main__":
    main()
