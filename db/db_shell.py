#!/usr/bin/env python3
import os
import sys
from db_helper import query_database
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "financial_data.db")


def meta_command(cmd: str) -> bool:
    parts = cmd.strip().split()
    if parts[0] == ".exit" or parts[0] == ".quit":
        print("Bye")
        return True
    elif parts[0] == ".tables":
        info = query_database(db_path=DB_PATH)
        print(", ".join(info["tables"]))
    elif parts[0] == ".summary":
        info = query_database(db_path=DB_PATH)
        print(f"Tables: {', '.join(info['tables'])}")
        print(f"Companies: {info['company_count']}, Metrics: {info['metrics_count']}")
        for sym, c in info["companies"].items():
            print(f"  {sym:6} {c['name']:30} years: {', '.join(c['years'])}")
    elif parts[0] == ".help":
        print(".exit / .quit  Exit")
        print(".tables        List tables")
        print(".summary       Show DB summary")
        print(".help          This message")
        print("Any other input is run as SQL against the DB")
    else:
        print(f"Unknown meta command: {parts[0]}")
    return False


def main():
    if not os.path.exists(DB_PATH):
        print(f"DB not found: {DB_PATH}")
        sys.exit(1)

    print(f"Connected to: {DB_PATH}")
    print("Type .help for help, .exit to quit")
    print()

    buf = ""
    while True:
        prompt = "   " if buf else "db> "
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line and buf:
            continue

        stripped = line.strip()

        if stripped.startswith("."):
            if buf:
                print("(flushing previous buffer)")
                buf = ""
            if meta_command(stripped):
                break
            continue

        if stripped == "":
            continue

        buf += " " + stripped if buf else stripped

        if not stripped.endswith(";"):
            continue

        sql = buf.rstrip(";").strip()
        buf = ""

        if not sql:
            continue

        try:
            results = query_database(query=sql, db_path=DB_PATH)
            if isinstance(results, list):
                if not results:
                    print("(no rows)")
                else:
                    keys = list(results[0].keys())
                    col_widths = {k: max(len(str(k)), max((len(str(r[k])) for r in results), default=0)) for k in keys}
                    header = " | ".join(k.ljust(col_widths[k]) for k in keys)
                    sep = "-+-".join("-" * col_widths[k] for k in keys)
                    print(header)
                    print(sep)
                    for r in results:
                        print(" | ".join(str(r[k]).ljust(col_widths[k]) for k in keys))
                    print(f"({len(results)} rows)")
            else:
                print(results)
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
