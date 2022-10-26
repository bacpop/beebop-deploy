import io
import pytest
import string

from contextlib import redirect_stdout
from unittest import mock

from src import beebop_cli
from src import beebop_deploy


def test_cli_parse():
    assert beebop_cli.parse(["start"]) == \
        ("config", None, "start", {"pull_images": False}, {})
    assert beebop_cli.parse(["start", "--pull"]) == \
        ("config", None, "start", {"pull_images": True}, {})
    assert beebop_cli.parse(["start", "prod"]) == \
        ("config", "prod", "start", {"pull_images": False}, {})
    assert beebop_cli.parse(["stop"]) == \
        ("config", None, "stop", {"kill": False, "remove_network": False,
                                  "remove_volumes": False}, {})
    assert beebop_cli.parse(["stop", "--kill", "--network"]) == \
        ("config", None, "stop", {"kill": True, "remove_network": True,
                                  "remove_volumes": False}, {})

    assert beebop_cli.parse(["destroy"]) == \
        ("config", None, "stop", {"kill": True, "remove_network": True,
                                  "remove_volumes": True}, {})

    assert beebop_cli.parse(["status"]) == ("config", None, "status", {}, {})
    assert beebop_cli.parse(["upgrade"]) == ("config", None, "upgrade", {}, {})


def test_args_passed_to_start():
    with mock.patch('src.beebop_cli.beebop_start') as f:
        beebop_cli.main(["start", "prod"])

    assert f.called
    assert f.call_args[0][1] == {"pull_images": False}

    with mock.patch('src.beebop_cli.beebop_start') as f:
        beebop_cli.main(["start", "prod", "--pull"])

    assert f.called
    assert f.call_args[0][1] == {"pull_images": True}
