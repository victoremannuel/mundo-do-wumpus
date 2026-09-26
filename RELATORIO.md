# RELATÓRIO DE IMPLEMENTAÇÃO  
## Agentes Lógicos — Mundo do Wumpus

## 1. Introdução

Neste trabalho desenvolvi uma implementação do **Mundo do Wumpus**, utilizando Python e conceitos de Inteligência Computacional para criar um agente capaz de explorar o ambiente de forma autônoma.

O principal objetivo foi fazer com que o agente conseguisse tomar decisões sem conhecer previamente a posição dos perigos ou dos demais elementos do mapa. Para isso, a solução foi estruturada para que o agente dependesse apenas das informações que poderia realmente perceber durante o jogo.

Dessa forma, o comportamento do agente segue basicamente o ciclo:

```text
PERCEBER
   ↓
MEMORIZAR
   ↓
INFERIR
   ↓
PLANEJAR
   ↓
DECIDIR
   ↓
AGIR
   ↓
ATUALIZAR O CONHECIMENTO
```

A inteligência utilizada no projeto é implementada inteiramente no próprio programa. Não utilizei GPT, APIs externas, modelos de linguagem ou outros serviços de Inteligência Artificial generativa para controlar o personagem durante uma partida.

---

## 2. Tecnologias utilizadas

O projeto foi desenvolvido principalmente com:

- **Python 3.11+**;
- **Rich**, para recursos de apresentação no terminal;
- **Textual**, para a interface gráfica baseada em terminal;
- **Pytest**, para testes automatizados;
- estruturas e algoritmos da biblioteca padrão do Python.

A escolha do Python facilitou a separação das responsabilidades do projeto e a implementação dos algoritmos de busca, inferência e tomada de decisão.

O programa funciona localmente e não necessita de conexão com a internet para executar o jogo.

---

## 3. Organização do projeto

Em vez de concentrar toda a implementação em um único arquivo, organizei o projeto em módulos separados.

A estrutura principal ficou dividida aproximadamente da seguinte forma:

```text
src/wumpus/

├── agent/
│   ├── memory.py
│   ├── knowledge.py
│   ├── inference.py
│   ├── planner.py
│   ├── risk.py
│   ├── strategy.py
│   ├── exit_policy.py
│   ├── simple_agent.py
│   └── human_agent.py
│
├── domain/
│   ├── coordinate.py
│   ├── enums.py
│   ├── models.py
│   ├── observation.py
│   └── perception.py
│
├── environment/
│   ├── world.py
│   ├── generator.py
│   ├── sensors.py
│   ├── actions.py
│   ├── arrows.py
│   ├── bats.py
│   └── scoring.py
│
├── game/
│   ├── config.py
│   ├── engine.py
│   ├── objective.py
│   └── scoring.py
│
├── ui/
│   └── componentes da interface
│
└── debug/
    └── renderização do mapa real
```

Essa divisão facilitou bastante a manutenção do projeto, principalmente porque mantém separadas as regras do ambiente, a inteligência do agente e a interface do usuário.

---

## 4. Representação do Mundo do Wumpus

O ambiente foi implementado como uma matriz de:

```text
6 × 6
```

O agente inicia na posição:

```text
[1,1]
```

e o mapa possui:

| Elemento | Quantidade |
|---|---:|
| Wumpus | 2 |
| Poços | 4 |
| Ouros | 3 |
| Morcegos | 2 |

As entidades são distribuídas aleatoriamente no início da partida e não podem ocupar a mesma sala.

Também implementei geração baseada em **seed**, permitindo reproduzir exatamente um determinado mapa.

Por exemplo:

```bash
python main.py --seed 42
```

Ao utilizar novamente a mesma configuração e a mesma seed, consigo reproduzir o cenário, o que foi muito importante para os testes e para investigar comportamentos específicos.

---

## 5. Geração de mapas

A geração do mapa não utiliza o gerador global de números aleatórios de forma indiscriminada. O projeto utiliza uma fonte de aleatoriedade controlada e reproduzível.

Além de distribuir os elementos aleatoriamente, o gerador verifica as restrições estruturais do mapa.

Entre as validações realizadas estão:

- dimensões corretas;
- quantidade correta de Wumpus;
- quantidade correta de poços;
- quantidade correta de ouros;
- quantidade correta de morcegos;
- ausência de sobreposição de entidades;
- proteção da região inicial;
- proteção da saída;
- existência de caminho fisicamente possível para cumprir o objetivo configurado.

Essa última verificação é feita internamente pelo gerador. Essa informação, porém, **não é fornecida ao agente**.

O agente continua precisando descobrir sozinho como navegar pelo mapa.

---

## 6. Entrada e saída da caverna

Durante a evolução do projeto, optei por separar a posição inicial da posição final.

O agente continua surgindo em:

```text
[1,1]
```

mas a saída operacional utilizada na versão atual fica no canto oposto:

```text
[6,6]
```

Essa alteração evita que o agente possa encerrar uma partida imediatamente após iniciá-la e torna a exploração mais significativa.

Para sair efetivamente da caverna, não basta chegar à posição de saída. É necessário executar a ação:

```text
CLIMB
```

quando as condições do objetivo atual estiverem satisfeitas.

---

## 7. Ações do agente

As principais ações implementadas são:

```text
MOVE_FORWARD
TURN_RIGHT
GRAB
SHOOT
CLIMB
```

Para realizar uma rotação equivalente a 90 graus para a esquerda, o agente pode executar três rotações para a direita.

Além disso, cada ação produz efeitos no ambiente e na pontuação.

Os principais valores utilizados são:

| Evento | Pontuação |
|---|---:|
| Ação normal | -1 |
| Atirar flecha | -10 |
| Pegar ouro | +1000 |
| Cair em poço | -1000 |
| Ser devorado pelo Wumpus | -1000 |

As regras de pontuação são centralizadas para evitar que diferentes partes do código atribuam valores diferentes ao mesmo evento.

---

## 8. Sistema de percepções

O agente não conhece o mapa verdadeiro.

Para descobrir o que existe ao redor, ele utiliza os sensores previstos no problema.

Implementei as seguintes percepções:

### Fedor

É percebido quando existe um Wumpus vivo em uma sala ortogonalmente adjacente.

### Brisa

É percebida quando existe um poço em uma sala adjacente.

### Som de morcego

É percebido quando existe um morcego em uma sala adjacente.

### Brilho

É percebido quando o agente está na mesma sala de uma pedra de ouro.

### Impacto

É gerado quando o agente tenta atravessar uma das paredes externas do labirinto.

### Grito

É percebido após a morte de um Wumpus.

As diagonais não são consideradas para fedor, brisa ou som de morcego.

---

## 9. Separação entre ambiente e agente

Uma das partes que considerei mais importantes na implementação foi impedir que o agente tivesse acesso ao mapa real.

O ambiente conhece informações como:

```text
posição dos Wumpus
posição dos poços
posição dos morcegos
posição dos ouros
```

O agente, por outro lado, não recebe essas estruturas.

A comunicação ocorre aproximadamente desta maneira:

```text
        MUNDO REAL
            │
            │ gera
            ▼
       OBSERVAÇÃO
            │
            ▼
      AGENTE LÓGICO
            │
            │ escolhe
            ▼
           AÇÃO
            │
            ▼
        AMBIENTE
```

O agente recebe somente um objeto de observação contendo informações permitidas, como:

- posição atual;
- direção;
- sensores;
- pontuação;
- quantidade de ouro coletada;
- estado da partida.

Isso impede que a solução seja apenas um algoritmo consultando diretamente onde estão os obstáculos.

---

## 10. Memória do agente

Para permitir que decisões futuras considerem acontecimentos anteriores, implementei uma memória para o agente.

Ela mantém informações como:

- posições visitadas;
- posição atual;
- orientação;
- percepções anteriores;
- ações executadas;
- caminhos utilizados;
- ouro coletado;
- alterações relevantes de conhecimento.

Essa memória permite que o agente não trate cada turno de forma isolada.

O conhecimento adquirido durante uma sala continua disponível nos próximos movimentos.

---

## 11. Base de conhecimento

Além da memória, implementei uma base de conhecimento que representa o que o agente conseguiu deduzir sobre o ambiente.

Entre as informações mantidas estão:

```text
salas visitadas
salas seguras
salas desconhecidas
possíveis poços
possíveis Wumpus
possíveis morcegos
poços confirmados
Wumpus confirmados
morcegos confirmados
```

Também mantenho conhecimento negativo.

Por exemplo:

```text
esta sala NÃO possui poço
esta sala NÃO possui Wumpus
esta sala NÃO possui morcego
```

Esse conhecimento negativo é muito importante para descobrir salas seguras.

---

## 12. Inferência lógica

O agente utiliza as percepções para fazer inferências sobre salas vizinhas.

Um exemplo simples ocorre quando o agente visita uma sala e não sente brisa.

Nesse caso:

```text
sem brisa
    ↓
nenhum vizinho possui poço
```

Da mesma forma:

```text
sem fedor
    ↓
nenhum vizinho possui Wumpus vivo
```

e:

```text
sem som de morcego
    ↓
nenhum vizinho possui morcego
```

Quando existe uma percepção positiva, as posições vizinhas passam a ser tratadas como candidatas ao perigo correspondente.

Depois, novas observações podem eliminar candidatos.

Exemplo:

```text
Sala A possui brisa

Possíveis poços:
B ou C

Depois descubro que:
B não possui poço

Logo:
C é o poço
```

O mecanismo de inferência atual é propositalmente conservador.

Como existem vários Wumpus, vários poços e vários morcegos no mapa, o programa evita confirmar um perigo somente porque conjuntos de possibilidades se sobrepõem. A confirmação precisa possuir evidência suficiente.

---

## 13. Planejamento de caminhos

Depois de identificar salas seguras, o agente precisa encontrar uma sequência de movimentos até seu objetivo.

Para isso implementei planejamento utilizando **BFS — Breadth-First Search**.

O BFS busca um caminho entre duas posições utilizando apenas as células que o agente considera transitáveis.

Exemplo:

```text
posição atual
     ↓
salas seguras conhecidas
     ↓
BFS
     ↓
caminho até o objetivo
```

Depois, o caminho formado por coordenadas é convertido em ações como:

```text
TURN_RIGHT
MOVE_FORWARD
MOVE_FORWARD
...
```

Dessa maneira, o planejamento de rota fica separado das ações físicas do personagem.

---

## 14. Avaliação de risco

Nem sempre o agente consegue provar que existe uma sala completamente segura para continuar explorando.

Por esse motivo também implementei um mecanismo de avaliação de risco.

O sistema considera diferentes evidências de:

- poço;
- Wumpus;
- morcego;
- conhecimento negativo;
- perigo confirmado.

A estratégia sempre prefere uma posição comprovadamente segura.

Somente quando não existe alternativa segura conhecida o agente pode avaliar uma opção de menor risco.

Essa etapa permite que o programa continue jogando mesmo em situações de incerteza, em vez de simplesmente ficar parado.

---

## 15. Estratégia de decisão

O agente possui uma estratégia que combina:

```text
MEMÓRIA
+
BASE DE CONHECIMENTO
+
INFERÊNCIA
+
PLANEJAMENTO
+
RISCO
+
OBJETIVO
```

Um exemplo de prioridade é o ouro.

Quando o agente percebe brilho na posição onde está:

```text
GRAB
```

tem prioridade sobre continuar uma rota já calculada.

Depois disso, o agente pode recalcular sua decisão.

A estratégia também consegue:

- explorar novas salas;
- retornar por caminhos conhecidos;
- escolher alternativas de menor risco;
- caçar um Wumpus quando existe evidência suficiente;
- abandonar um objetivo temporariamente quando ocorre nova informação;
- replanejar após teleporte;
- detectar situações de repetição;
- decidir quando seguir para a saída.

---

## 16. Objetivos de jogo

Além do comportamento originalmente previsto, implementei dois objetivos selecionáveis.

### Escapar o mais rápido possível

Nesse modo o agente tenta alcançar a saída priorizando rotas seguras ou aceitáveis.

Ele não procura ouro propositalmente.

Entretanto, caso passe por uma sala contendo ouro durante a própria rota, coleta esse ouro antes de continuar.

### Coletar todos os ouros antes de escapar

Nesse modo o agente continua explorando até coletar todos os ouros configurados.

Somente depois disso a saída pode concluir a partida.

Essa configuração permitiu observar estratégias diferentes utilizando o mesmo motor do jogo.

---

## 17. Flechas e Wumpus

As flechas são disparadas em linha reta na direção em que o agente está olhando.

O disparo continua até:

```text
atingir um Wumpus vivo
```

ou:

```text
atingir a parede
```

Caso exista mais de um Wumpus na mesma direção, apenas o primeiro é atingido.

Depois que um Wumpus morre:

- ele deixa de oferecer risco;
- deixa de gerar fedor;
- sua morte gera o grito;
- o conhecimento do agente pode ser atualizado.

A estratégia não dispara simplesmente porque percebe fedor.

A intenção é utilizar a flecha somente quando existir evidência lógica suficiente ou vantagem estratégica.

---

## 18. Morcegos

Os morcegos adicionam uma parte não determinística à execução.

Ao entrar em uma sala com morcego:

1. o agente chega à sala;
2. o morcego é ativado;
3. o agente é teleportado;
4. o destino é escolhido aleatoriamente;
5. a orientação do agente é mantida;
6. o destino é resolvido imediatamente.

O agente pode ser levado para:

- sala vazia;
- ouro;
- outro morcego;
- poço;
- Wumpus;
- outra posição válida do mapa.

Também implementei tratamento para cadeias como:

```text
MORCEGO
   ↓
MORCEGO
   ↓
MORCEGO
   ↓
...
```

com proteções para impedir loops técnicos infinitos.

---

## 19. Detecção de ciclos

Durante os testes percebi que um agente autônomo também precisa lidar com situações onde suas próprias decisões podem formar ciclos.

Por isso foram adicionados mecanismos de detecção de estagnação.

O agente consegue identificar situações como:

```text
mesma posição
+
mesma orientação
+
mesma intenção
+
nenhum conhecimento novo
```

repetidas várias vezes.

Quando isso ocorre, a rota atual pode ser invalidada e uma nova alternativa é calculada.

Existe ainda um limite técnico de turnos para impedir que qualquer erro de estratégia gere uma execução infinita.

---

## 20. Interface

Inicialmente o jogo possuía uma visualização sequencial utilizando Rich.

Posteriormente desenvolvi uma interface persistente em terminal utilizando **Textual**.

A interface atual apresenta uma aparência inspirada em jogos retrô e evita imprimir uma nova tela completa a cada turno.

Ela apresenta informações como:

- mapa conhecido pelo agente;
- posição;
- orientação;
- objetivo;
- pontuação;
- quantidade de ouro;
- turno;
- sensores;
- decisão tomada;
- legenda;
- seed da partida.

Também existem controles para:

- pausar;
- avançar uma ação;
- alterar a velocidade;
- ativar depuração;
- reiniciar a partida;
- encerrar o jogo.

---

## 21. Modo autônomo e modo jogador

A interface permite selecionar dois tipos de execução.

### Agente autônomo

Nesse modo todas as decisões são tomadas pelo agente lógico implementado no projeto.

### Jogador

Também implementei um modo manual, permitindo controlar o personagem diretamente.

Mesmo nesse modo, as ações continuam passando pelo mesmo motor do jogo.

Isso evita duplicação de regras.

Ou seja:

```text
AGENTE AUTÔNOMO ─┐
                 ├──> GAME ENGINE ───> WORLD
JOGADOR ─────────┘
```

Pontuação, flechas, mortes, sensores, morcegos e demais regras continuam sendo processados pelo mesmo ambiente.

---

## 22. Modo de depuração

Foi criado também um modo voltado à demonstração e à análise do funcionamento do agente.

Exemplo:

```bash
python main.py --seed 42 --debug
```

Nesse modo é possível visualizar:

```text
MAPA CONHECIDO PELO AGENTE

e

MAPA REAL
```

ao mesmo tempo.

Porém, o mapa real é encaminhado exclusivamente para a interface de depuração.

Ele não é fornecido ao agente.

Dessa forma consigo demonstrar visualmente se as inferências do agente estão corretas sem quebrar a principal restrição do trabalho.

---

## 23. Execução do projeto

Depois de instalar as dependências:

```bash
python -m pip install -r requirements.txt
```

o jogo pode ser iniciado normalmente com:

```bash
python main.py
```

Para executar uma partida reproduzível:

```bash
python main.py --seed 42
```

Modo de depuração:

```bash
python main.py --seed 42 --debug
```

Também mantive a interface de console anterior:

```bash
python main.py --seed 42 --no-delay --legacy-console
```

Isso é útil principalmente para testes, registros e execução automatizada.

---

## 24. Processo de implementação

O desenvolvimento foi realizado de forma incremental.

Dividi a implementação em 21 fases principais:

```text
1. Scaffold
2. Domínio
3. Gerador
4. Ambiente
5. Flechas
6. Morcegos
7. Engine
8. Memory
9. Knowledge Base
10. Inference Engine
11. Planner
12. Strategy
13. Wumpus Hunting
14. Risk Engine
15. Política de saída
16. Interface
17. Debug
18. CLI
19. Testes de integração
20. Testes E2E
21. README final
```

Minha intenção foi evitar implementar todo o projeto de uma vez.

O fluxo utilizado em cada etapa foi aproximadamente:

```text
IMPLEMENTAR
     ↓
TESTAR
     ↓
CORRIGIR
     ↓
VALIDAR
     ↓
REGISTRAR CHECKPOINT
     ↓
CONTINUAR
```

Isso também facilitou localizar regressões quando novas funcionalidades foram adicionadas.

---

## 25. Testes automatizados

Os testes tiveram bastante importância durante o desenvolvimento.

Foram criados testes para diferentes níveis da aplicação.

### Testes de domínio

Validam:

- coordenadas;
- direções;
- estruturas de dados;
- configurações.

### Testes do ambiente

Validam:

- movimentos;
- paredes;
- sensores;
- pontuação;
- ouro;
- morte;
- saída.

### Testes de geração

Validam:

- número de entidades;
- posições protegidas;
- ausência de sobreposição;
- determinismo por seed;
- conectividade necessária.

### Testes das flechas

Validam:

- direção;
- alcance;
- morte do primeiro Wumpus encontrado;
- custo correto do disparo.

### Testes dos morcegos

Validam:

- teleporte;
- cadeias de teleporte;
- preservação da orientação;
- destinos perigosos.

### Testes da inteligência

Validam:

- memória;
- conhecimento negativo;
- inferência;
- perigos possíveis;
- perigos confirmados;
- identificação de salas seguras;
- planejamento BFS;
- avaliação de risco;
- estratégia;
- política de saída.

### Testes antitrapaça

Também existem verificações específicas para garantir que o agente não obtenha referência ao mapa real.

### Testes de integração e E2E

As últimas fases executam o agente real junto ao ambiente real.

Foram utilizadas diversas seeds fixas e execuções em lote para verificar:

- término das partidas;
- determinismo;
- ausência de exceções;
- ausência de loops infinitos;
- consistência das decisões.

Na manutenção mais recente registrada no repositório, a suíte completa chegou a:

```text
429 testes aprovados
```

sem falhas na verificação registrada naquele checkpoint.

Também foram realizados testes de estresse com centenas de mapas e partidas para detectar problemas que dificilmente apareceriam utilizando apenas uma única execução.

---

## 26. Evoluções realizadas após a implementação principal

Depois das 21 fases iniciais, continuei melhorando alguns pontos do jogo.

Entre essas melhorias estão:

- interface persistente em Textual;
- visual retrô;
- modo manual;
- tela inicial de configuração;
- objetivos de jogo selecionáveis;
- saída transferida para `[6,6]`;
- proteção da área inicial;
- geração de mapas fisicamente solucionáveis;
- melhoria da detecção de loops;
- reinício reproduzível das partidas;
- melhoria do comportamento de coleta de ouro;
- correções na estratégia e no planejamento.

Essas alterações foram feitas sem permitir que o agente utilizasse informações escondidas do mapa.

---

## 27. Limitações atuais

Apesar de o núcleo do jogo e as 21 fases de implementação estarem verificados, ainda existem alguns pontos complementares registrados na documentação técnica como trabalho adicional.

Principalmente:

- detalhamento maior das estatísticas finais;
- métricas adicionais de exploração;
- refinamentos de apresentação;
- situações onde o agente pode escolher uma estratégia conservadora e não conseguir finalizar dentro do limite técnico de turnos.

Também é importante destacar que o objetivo do projeto não é garantir que o agente vença todas as partidas.

Um agente pode morrer mesmo tomando decisões coerentes, pois existem situações nas quais é necessário assumir algum risco.

O objetivo principal é garantir que ele tome decisões utilizando somente aquilo que conseguiu perceber e inferir.

---

## 28. Resultado obtido

Ao final do desenvolvimento consegui implementar um jogo completo do Mundo do Wumpus no qual o agente:

- não conhece inicialmente o mapa;
- recebe somente percepções válidas;
- mantém memória das salas visitadas;
- constrói conhecimento progressivamente;
- utiliza conhecimento negativo;
- realiza inferências;
- identifica salas seguras;
- identifica possíveis perigos;
- confirma perigos quando possui evidências;
- calcula caminhos utilizando BFS;
- avalia riscos;
- utiliza flechas;
- coleta ouro;
- reage a morcegos;
- replaneja após mudanças inesperadas;
- detecta ciclos;
- procura a saída;
- toma decisões autonomamente.

A interface permite acompanhar visualmente todo esse processo, incluindo as percepções e a justificativa funcional das decisões tomadas.

---

## 29. Conclusão

A implementação do Mundo do Wumpus permitiu aplicar na prática vários conceitos estudados em Inteligência Computacional.

O ponto que considerei mais importante no projeto foi não resolver o problema simplesmente consultando o mapa.

O ambiente sabe onde estão os elementos, mas o agente não.

Ele precisa construir gradualmente sua própria representação do mundo.

Assim, a tomada de decisão ocorre aproximadamente desta forma:

```text
PERCEPÇÃO
    ↓
MEMÓRIA
    ↓
BASE DE CONHECIMENTO
    ↓
INFERÊNCIA
    ↓
AVALIAÇÃO DE RISCO
    ↓
PLANEJAMENTO
    ↓
AÇÃO
```

Na minha avaliação, essa separação foi o que realmente transformou o programa de um simples jogo baseado em regras em um **agente lógico autônomo**.

Além de cumprir a mecânica principal do Mundo do Wumpus, o projeto ficou estruturado de forma que consigo reproduzir partidas, testar individualmente os componentes, visualizar o raciocínio do agente e comparar o conhecimento que ele construiu com o mapa verdadeiro através do modo de depuração.

O resultado final demonstra, de forma prática, como um agente pode perceber um ambiente parcialmente observável, acumular conhecimento, realizar inferências e utilizar essas informações para planejar suas próximas ações sem depender de Inteligência Artificial generativa ou de informações privilegiadas do ambiente.
