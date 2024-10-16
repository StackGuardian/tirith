import pytest
import subprocess
import os


def run_cmd(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()

    return process.returncode


def test_end_to_end():
    policy_file_name = (
        f"{os.path.dirname(os.path.abspath(__file__))}/fixtures/apigateway_state_logging_enabled.tirith.json"
    )
    input_file_name = f"{os.path.dirname(os.path.abspath(__file__))}/fixtures/plan.json"
    command = f"tirith -policy-path {policy_file_name} -input-path {input_file_name}"
    returncode = run_cmd(command)

    assert returncode == 1
