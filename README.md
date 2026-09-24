# Mundo do Wumpus

Implementação acadêmica, offline e incremental de um Mundo do Wumpus 6 × 6.
O objetivo do projeto é construir um agente lógico autônomo que decide somente
a partir das percepções disponibilizadas pelo ambiente, sem acesso ao mapa
real.

## Estado atual

O repositório contém o scaffold inicial. As regras do domínio e a inteligência
do agente serão adicionadas nas fases seguintes do plano de implementação.

## Requisitos

- Python 3.11 ou mais recente

## Preparação e testes

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
pytest -q
```

A documentação completa de arquitetura, regras, execução e limitações será
entregue na fase final dedicada ao README.
