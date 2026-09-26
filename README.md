# Mundo do Wumpus — agente lógico autônomo

Implementação acadêmica, offline e determinística do Mundo do Wumpus em Python 3.11+. O agente explora uma caverna 6 × 6 sem conhecer o mapa real: decide apenas com observações, memória e conhecimento inferido. O projeto não usa LLMs, APIs externas nem serviços pagos. Toda partida recebe uma seed inteira concreta; mesma seed, configuração e objetivo reproduzem o mesmo mapa.

## Objetivo acadêmico

O projeto combina um **agente baseado em conhecimento**, um **agente orientado a utilidade** e **planejamento de caminhos** por BFS. O ambiente é parcialmente observável, sequencial, essencialmente estático entre ações, discreto e de regras conhecidas, mas de mapa inicial desconhecido. A geração e os teletransportes usam RNG injetável; uma `--seed` fixa torna a execução reproduzível.

## Regras do jogo

- A caverna tem 6 × 6 salas, de `[1,1]` a `[6,6]`. O agente começa em `[1,1]`, virado para norte; a saída estrutural, sempre vazia, é `[6,6]`.
- A zona inicial (`[1,1]`, `[1,2]`, `[2,1]`) e a saída são livres de entidades. Cada mapa tem 2 Wumpus, 4 poços, 3 ouros e 2 morcegos, sem sobreposição; os vizinhos da saída continuam aleatórios.
- Ouro vale `+1000`; ações comuns custam `-1`; disparar custa `-10`; morrer aplica `-1000` além do custo de entrar na sala.
- A saída é automática: ao entrar em `[6,6]`, a partida termina quando o objetivo estiver satisfeito. `CLIMB` pode existir por compatibilidade e ainda custa uma ação, mas não é condição de vitória.
- **ESCAPAR O MAIS RÁPIDO POSSÍVEL** chega à saída com prioridade, usando apenas rotas seguras conhecidas, inferência e risco aceitável; ouro pode ser ignorado pelo agente autônomo. **COLETAR TODOS OS OUROS ANTES DE ESCAPAR** exige todos os ouros configurados e bloqueia a saída enquanto houver ouro pendente.
- A geração escolhe somente mapas estruturalmente vencíveis, sem entregar essa solução ao agente: em **ESCAPAR RÁPIDO** há caminho ortogonal seguro entre início e saída; em **COLETAR TODOS OS OUROS**, início, todos os ouros e saída pertencem ao mesmo componente de salas sem poço, Wumpus vivo ou morcego. Isso prova que uma solução física existe, não que o agente necessariamente a encontrará.
- Morcegos teleportam o agente para sala aleatória e podem formar cadeia; a orientação é preservada. A flecha segue em linha reta até parede ou primeiro Wumpus vivo.

Sensores: **fedor** (Wumpus adjacente), **brisa** (poço adjacente), **som de morcego**, **brilho**, **impacto** e **grito**.

## Arquitetura e fronteira antitrapaça

```text
MapGenerator -> World -> AgentObservation -> SimpleAgent
                    |                         |
                    +-> ActionResult <--------+
```

`World` guarda mapa, entidades, pontuação e regras. `SimpleAgent` não recebe `World`, grade ou posições de entidades: sua única entrada é `AgentObservation` (posição, direção, percepções, pontuação, ouro e estado ativo). O `GameEngine` executa `observar -> renderizar -> decidir -> executar -> processar resultado`.

O mapa real só aparece no caminho explícito `World -> DebugRenderer -> interface`; nunca chega ao agente. Testes de fronteira verificam que o pacote do agente não importa tipos do ambiente ou do mapa oculto.

## Como o agente raciocina

1. A memória registra observação e resultado da ação.
2. A base de conhecimento marca salas visitadas, seguras, desconhecidas, possíveis perigos, perigos confirmados e conhecimento negativo.
3. Ausência de sinal elimina o perigo correspondente nas adjacências; sinais positivos adicionam candidatos. Um perigo só é confirmado quando uma observação tem um único candidato possível.
4. A estratégia escolhe uma meta pública: em escape rápido, prioriza rota segura e fronteira com melhor custo conhecido mais distância até `[6,6]`; em coletar todos, pega brilho, explora até obter todos os ouros e então navega para `[6,6]`. Ambas preservam caça racional, risco aceitável e espera fail-closed.
5. O planejador BFS cria rota apenas por salas conhecidas como seguras.

Como há múltiplos perigos de cada tipo, a interseção de dois sinais positivos não confirma um perigo por si só: perigos distintos podem explicar cada sinal. A implementação privilegia inferências sólidas, ainda que incompletas.

## PEAS

| Elemento | Descrição |
| --- | --- |
| Performance | `+1000` ouro, `-1000` morte, `-1` ações normais, `-10` flecha |
| Environment | Labirinto 6 × 6, Wumpus, poços, morcegos, ouro e paredes |
| Actuators | Avançar, virar à direita/esquerda, pegar e atirar (a saída é automática) |
| Sensors | Fedor, brisa, som de morcego, brilho, impacto e grito |

## Instalação e testes

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m compileall -q src main.py
```

As dependências de execução são Rich e Textual; pytest é usado nos testes. Ruff não está configurado neste repositório.

## Execução

```bash
# Interface retro persistente (padrão)
python main.py

# Execução determinística e modo professor
python main.py --seed 42
python main.py --seed 42 --debug

# Iniciar pausado na interface legada e controlar cadência
python main.py --step --legacy-console
python main.py --delay 0.5
python main.py --no-delay

# Renderer de console sequencial, útil para automação e logs
python main.py --seed 42 --no-delay --legacy-console
```

A interface padrão começa por uma configuração explícita de **modo** (agente autônomo ou jogador) e **objetivo**; o botão iniciar permanece desabilitado até que ambos sejam escolhidos, e `R` volta à configuração preservando modo, objetivo, seed e contagens. A mesma tela ajusta as contagens de Wumpus, poços, ouros e morcegos; em `6 × 6` restam 32 salas disponíveis para entidades, porque a zona inicial e a saída são protegidas. Em jogo, a tela fixa mostra objetivo, saída, mapa conhecido, posição/direção, sensores, pontuação, ouro, turno, decisão e legenda, além da seed concreta — inclusive quando ela foi escolhida automaticamente. `[1,1]` (INÍCIO) e `[6,6]` (SAÍDA) são marcadores pixel-art públicos desde o primeiro quadro, inclusive sob o agente. No modo jogador, os controles são mover, virar, pegar e atirar; não há comando de subir. Ao alcançar a saída sem todos os ouros, o modo de coleta mostra feedback de saída bloqueada e a partida continua. Pausa, passo único, velocidade, depuração e saída controlam apenas apresentação e cadência; não escolhem ações. Abaixo de 118 × 54, ela mostra um aviso e se recompõe ao redimensionar. No `--debug`, os mapas conhecido e real são separados; só o primeiro é usado nas decisões.

## Exemplos de resultado

Uma execução termina como `ESCAPED`, `DEAD` ou `TURN_LIMIT`. O limite técnico é 2000 turnos e evita execução infinita; não representa vitória. O resultado inclui status, pontuação, ouro coletado, Wumpus abatidos, turnos e salas visitadas.

A matriz E2E executa e repete as seeds `1`, `2`, `3`, `10`, `20`, `42`, `100`, `123`, `999` e `2026`, exigindo o mesmo resultado completo em cada repetição.

## Cobertura de testes

O conjunto automatizado cobre domínio, geração determinística e invariantes do mapa; sensores, movimentos, pontuação, flecha e morcegos; memória, conhecimento, inferência, BFS, estratégia, risco e saída; fronteira agente/ambiente e debug; CLI, TUI, integração e partidas E2E reproduzíveis.

```bash
python -m pytest tests/e2e/test_seeded_games.py -q
```

## Limitações conhecidas

- Mapas podem continuar difíceis, arriscados e levar o agente a morrer ou atingir o limite; a garantia é somente de uma solução física sem poço, Wumpus ou morcego, que o agente não conhece.
- Sem passo seguro ou risco aceitável, o agente pode girar deterministicamente até o limite. Detecção explícita de ciclos e lista temporária de objetivos ainda são trabalho futuro.
- A morte de Wumpus é atribuída conservadoramente: apenas quando o agente consegue prová-la com seu próprio conhecimento.
- A tela final exibe modo, objetivo, status, pontuação, ouro, Wumpus, turnos, salas visitadas, seed, início e saída, mas ainda não detalha motivo, tiros e taxa de exploração.
- Em **coletar todos os ouros**, sem rota segura conhecida até a saída o agente aguarda de forma determinística em vez de arriscar; a exploração por risco só atua enquanto ainda falta ouro.
- O painel de raciocínio mostra a decisão do turno anterior junto da nova observação, por causa da ordem de renderização do motor.

## Estrutura principal

```text
src/wumpus/domain/       DTOs, coordenadas e enums
src/wumpus/environment/  mapa, regras, sensores, flechas e morcegos
src/wumpus/game/         configuração, pontuação e GameEngine
src/wumpus/agent/        memória, conhecimento, inferência, BFS e estratégia
src/wumpus/ui/           console e interface retro Textual
src/wumpus/debug/        adaptadores explícitos para mapa real
tests/                   testes unitários, integração e E2E
```
