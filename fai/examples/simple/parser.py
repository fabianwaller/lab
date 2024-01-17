#! /usr/bin/env python
import os

from lab.parser import Parser
import re


def add_patterns():
    parser.add_pattern("node", r"node: (.+)\n", type=str, file="driver.log", required=True)
    parser.add_pattern("exit_code", r"exit code: (.+)\n", type=int, file="driver.log")
    parser.add_pattern("start_msg", r"(Running dummy executable)", type=str)
    parser.add_pattern("success_msg", r"(Done)", type=str)


def set_derived_flags(content, props):
    if props["exit_code"] == 0 and "start_msg" in props and "success_msg" in props:
        props["error"] = "none"
    else:
        props["error"] = "unclassified_error"
        props.add_unexplained_error(f"Exit code {props['exit_code']}.")


if __name__ == "__main__":
    parser = Parser()
    add_patterns()
    parser.add_function(set_derived_flags)
    parser.parse()
