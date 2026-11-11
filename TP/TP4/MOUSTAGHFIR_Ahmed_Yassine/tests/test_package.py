"""Ces deux tests échouent tant que le package n'est pas installé."""

from importlib.metadata import entry_points, version


def test_installed_version_is_0_2_0():
    assert version("maintai") == "0.2.0"


def test_console_script_is_registered():
    scripts = {
        point.name: point.value for point in entry_points(group="console_scripts")
    }
    assert scripts["maintai-predict"] == "maintai.cli:main"
