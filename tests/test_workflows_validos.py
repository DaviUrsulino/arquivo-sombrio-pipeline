from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")


def test_todos_os_workflows_sao_yaml_valido():
    # 06/11: um run: de várias linhas sem "|" quebrou a produtora em silêncio (só falha no GitHub, não aqui)
    for arquivo in (Path(__file__).resolve().parents[1] / ".github" / "workflows").glob("*.yml"):
        yaml.safe_load(arquivo.read_text(encoding="utf-8"))
