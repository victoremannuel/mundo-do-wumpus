from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_final_readme_covers_the_plan_required_topics() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    required_topics = (
        "Objetivo acadêmico", "Regras do jogo", "Arquitetura",
        "Como o agente raciocina", "Instalação e testes", "Execução",
        "debug", "Exemplos de resultado", "Limitações conhecidas", "PEAS",
    )
    assert all(topic.casefold() in readme.casefold() for topic in required_topics)


def test_final_readme_documents_reproducible_execution_and_test_commands() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "python main.py --seed 42" in readme
    assert "python -m pytest -q" in readme
    assert "python -m compileall -q src main.py" in readme
