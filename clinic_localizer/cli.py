from __future__ import annotations

import argparse
import json
from typing import Sequence

from clinic_localizer.validation_service import Application, run, verify


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog='clinic_localizer', description='东盟医疗人工智能本地化验证注册库')
    commands = root.add_subparsers(dest="command", required=True)
    execute = commands.add_parser("run")
    execute.add_argument("--fixture", required=True)
    execute.add_argument("--database", required=True)
    execute.add_argument("--output", required=True)
    check = commands.add_parser("verify")
    check.add_argument("--database", required=True)
    check.add_argument("--output", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--database", required=True)
    strata = commands.add_parser("strata", help="compare evidence reliability by population group")
    strata.add_argument("--database", required=True)
    strata.add_argument("--purpose", default=None)
    history = commands.add_parser("scope-history", help="show why each scope range was retained, narrowed or deferred")
    history.add_argument("--database", required=True)
    history.add_argument("--scope", required=True)
    review = commands.add_parser("review-scope", help="review a scope's supported range without issuing it")
    review.add_argument("--database", required=True)
    review.add_argument("--scope", required=True)
    review.add_argument("--review-id", required=True)
    review.add_argument("--trigger", default="manual")
    issue = commands.add_parser("issue-scope", help="issue a scope only for its supported range")
    issue.add_argument("--database", required=True)
    issue.add_argument("--scope", required=True)
    issue.add_argument("--issue-id", required=True)
    issue.add_argument("--review-id", required=True)
    recheck = commands.add_parser("recheck-scopes", help="re-evaluate scopes after resubmission or correction")
    recheck.add_argument("--database", required=True)
    recheck.add_argument("--trigger", required=True)
    recheck.add_argument("--review-prefix", required=True)
    recheck.add_argument("--cohort", action="append", default=None,
                         help="limit to scopes linking this cohort (repeatable)")
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "run":
        result = run(args.fixture, args.database, args.output)
    elif args.command == "verify":
        result = verify(args.database, args.output)
    else:
        application = Application(args.database)
        if args.command == "strata":
            result = application.stratified_review(args.purpose)
        elif args.command == "scope-history":
            result = application.scope_history(args.scope)
        elif args.command == "review-scope":
            result = application.repository.review_scope(args.review_id, args.scope, args.trigger)
        elif args.command == "issue-scope":
            result = application.repository.issue_scope_checked(args.issue_id, args.scope, args.review_id)
        elif args.command == "recheck-scopes":
            result = application.repository.recheck_all_scopes(args.trigger, args.review_prefix,
                                                               args.cohort)
        else:
            result = application.inspect()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
