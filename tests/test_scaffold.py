from importlib import import_module
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_required_scaffold_exists() -> None:
    required_paths = (
        PROJECT_ROOT / "pyproject.toml",
        PROJECT_ROOT / "requirements.txt",
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "src",
        PROJECT_ROOT / "tests",
    )

    assert all(path.exists() for path in required_paths)


def test_package_is_importable() -> None:
    package = import_module("wumpus")

    assert package.__version__ == "0.1.0"
