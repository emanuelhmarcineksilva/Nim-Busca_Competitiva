# TDE2 — Busca Competitiva: Nim de Duas Pilhas

Implementação didática em Python do Nim de Duas Pilhas e de agentes baseados em Minimax e Alfa-Beta. O projeto inclui regras, agentes, o motor experimental, os resultados reais do protocolo e uma interface desktop Tkinter com cinco telas: Partida, Algoritmos, Experimentos, Resultados e Guia do Trabalho.

## Apresentação do projeto

O jogo usa duas pilhas de pedras. Em cada turno, o jogador retira uma ou mais pedras de uma única pilha; quem retirar a última pedra vence. MAX e MIN representam os papéis na busca, não jogadores fixos na interface. Todos os valores de utilidade e busca são reportados do ponto de vista de MAX.

## Estrutura dos arquivos

```text
TD2/
├── jogo.py
├── agentes.py
├── experimentos.py
├── interface.py
├── DUVIDAS_E_EXPLICACOES.md
├── telas/
│   ├── algoritmos.py
│   ├── comum.py
│   ├── experimentos.py
│   ├── guia.py
│   ├── partida.py
│   └── resultados.py
├── resultados/
│   ├── final/
│   │   ├── jogadas.csv
│   │   ├── partidas.csv
│   │   └── resumo.csv
│   └── piloto/
│       ├── jogadas.csv
│       ├── partidas.csv
│       └── resumo.csv
├── testes/
│   ├── test_jogo.py
│   ├── test_minimax.py
│   ├── test_alfa_beta.py
│   ├── test_avaliacao.py
│   ├── test_alfa_beta_limitado.py
│   ├── test_agentes.py
│   ├── test_experimentos.py
│   ├── test_protocolo_experimentos.py
│   ├── test_tela_partida.py
│   ├── test_tela_algoritmos.py
│   ├── test_tela_resultados.py
│   ├── test_tela_experimentos.py
│   └── test_rolagem_interface.py
├── README.md
└── OQueFaltanoProjeto.md
```

- [`jogo.py`](./jogo.py) contém as regras e os tipos `Estado`, `Jogada`, `Jogador` e `Pilha`.
- [`agentes.py`](./agentes.py) contém `minimax()`, `alfa_beta()`, `ordenar_acoes()`, `avaliacao_heuristica()`, `alfa_beta_limitado()` e os agentes para partidas.
- [`experimentos.py`](./experimentos.py) executa partidas individuais, define os 16 confrontos do protocolo, calcula resumos e exporta três CSVs. A interface de experimentos reutiliza esse motor para confrontos personalizados e para executar o protocolo sem alterar seus parâmetros.
- [`interface.py`](./interface.py) inicia a janela Tkinter e controla a navegação; [`telas/`](./telas/) contém as páginas.
- [`DUVIDAS_E_EXPLICACOES.md`](./DUVIDAS_E_EXPLICACOES.md) explica os conceitos e as dúvidas práticas do projeto em linguagem didática.
- [`resultados/final/`](./resultados/final/) contém os CSVs das 19.520 partidas do protocolo completo.
- [`resultados/piloto/`](./resultados/piloto/) contém os CSVs do piloto pequeno, não os resultados finais do protocolo.
- [`testes/`](./testes/) valida regras, algoritmos, agentes, partidas, protocolo, exportação, as telas e a rolagem da interface.
- [`OQueFaltanoProjeto.md`](./OQueFaltanoProjeto.md) registra pendências e requisitos ainda necessários para a entrega.

O motor de experimentos foi executado e validado com 19.520 partidas. A tela Partida reutiliza `jogo.py` e `agentes.py`; Algoritmos apresenta conceitos e executa as funções reais de busca; Experimentos configura partidas personalizadas ou solicita confirmação antes do protocolo completo, acompanha progresso e grava cada execução em uma pasta isolada; Resultados lê os CSVs finais; Guia organiza o conteúdo em seções e consulta os resultados existentes. A execução pela interface não altera `resultados/final/`. O código usa a biblioteca padrão do Python, incluindo Tkinter/ttk; os testes usam `unittest`.

Para abrir a interface:

```bash
python3 interface.py
```

A tela Partida aceita de 0 a 8 peças por pilha (não permite iniciar com ambas vazias), jogador inicial MAX/MIN e os agentes Humano, Aleatório, Minimax completo, Alpha-Beta completo, Alpha-Beta limitado e Agente principal. Os agentes automáticos avançam uma jogada por clique; a busca ocorre em uma thread separada para manter a janela responsiva. As jogadas, estados, nós de busca e sementes aleatórias aparecem no histórico. Essa tela usa as regras de `jogo.py` e as funções de `agentes.py`; não duplica os algoritmos.

### Algoritmos

A aba **Algoritmos** organiza sete assuntos: Minimax, Alpha-Beta, poda, ordenação, busca limitada, heurística e XOR. Na demonstração, o estado inicial é configurável (até quatro peças por pilha e oito no total); Minimax, Alpha-Beta e Alfa-Beta limitado chamam as implementações de `agentes.py` em uma thread, sem bloquear a janela. A página mostra valor, jogada e nós visitados, compara os nós completos dos dois algoritmos e calcula a heurística real do estado. A árvore é deliberadamente reduzida à raiz e a seus sucessores imediatos, cujos valores são calculados com Minimax. O código de busca não expõe o rastreamento dos cortes por ramo; por isso a interface mostra a quantidade total de nós evitados, mas não marca nós podados individuais como se tivesse essa informação. A área de ordenação exibe a sequência legal antes e depois de aplicar `ordenar_acoes()`. A calculadora XOR é didática e não substitui uma busca ou garante vitória contra qualquer adversário.

### Resultados

A aba **Resultados** carrega `resultados/final/{partidas,jogadas,resumo}.csv`, sem alterar ou regenerar os arquivos. Apresenta contagens gerais, vitórias acumuladas por configuração (identificadas como agregação entre contextos), estatísticas do confronto selecionado, gráficos Canvas, navegação paginada pelas partidas e histórico das jogadas. `N/A` permanece não aplicável; as médias de profundidade e ordenação são ponderadas pelo número de decisões com busca. Os CSVs não incluem confronto experimental entre Minimax completo e Alfa-Beta completo, portanto a comparação entre esses dois algoritmos está disponível na demonstração interativa, não como resultado agregado do protocolo. A própria aba registra as limitações sobre posições simétricas, amostra e interpretação dos resultados.

### Experimentos e Guia do Trabalho

A aba **Experimentos** tem dois modos. O modo personalizado permite escolher os agentes de MAX e MIN, parâmetros aplicáveis, posições, repetições, semente e jogador inicial; valida os valores antes de iniciar. O modo protocolo mantém as configurações aprovadas e pede confirmação antes de iniciar 19.520 partidas. O progresso é atualizado sem bloquear a janela, e o cancelamento ocorre entre partidas. Cada execução concluída é armazenada em uma pasta única dentro de `resultados/execucoes/`; não sobrescreve `resultados/final/`. Uma execução cancelada ou com falha não publica CSVs parciais. O resultado da execução mostra o resumo e permite exportar cópias dos três CSVs.

A aba **Guia do trabalho** oferece navegação por seções, com formalização, exemplos, complexidade, metodologia, limitações e resultados lidos dos CSVs finais. O guia não substitui nem preenche o template acadêmico. Para revisar perguntas conceituais e exemplos em texto, consulte [`DUVIDAS_E_EXPLICACOES.md`](./DUVIDAS_E_EXPLICACOES.md).

Todas as páginas usam uma área externa rolável. Textos e tabelas que possuem rolagem própria mantêm seu comportamento para evitar conflito com a rolagem da página.

## Regras e formalização do jogo

Um estado é a tripla:

\[
s = (a, b, j)
\]

em que \(a,b \in \mathbb{N}_0\) são as quantidades de pedras nas pilhas A e B, e \(j \in \{\text{MAX},\text{MIN}\}\) identifica quem joga em seguida. O estado inicial provisório é \(s_0=(8,8,\text{MAX})\); as quantidades serão configuráveis.

### Jogador

\[
\operatorname{JOGADOR}(a,b,j)=j
\]

### Ações legais

Para um estado não terminal:

\[
\operatorname{AÇÕES}(a,b,j)
= \{(A,k)\mid 1\leq k\leq a\}
\cup
\{(B,k)\mid 1\leq k\leq b\}
\]

Uma ação `(A, k)` retira `k` pedras somente da pilha A; `(B, k)` faz o mesmo na pilha B. Se a pilha estiver vazia, não há ações para ela. Em um estado terminal, o conjunto de ações é vazio.

Por exemplo, em `(3, 2, MAX)`, as ações legais são `(A, 1)`, `(A, 2)`, `(A, 3)`, `(B, 1)` e `(B, 2)`.

### Transição

\(\operatorname{RESULTADO}(s,\alpha)\) subtrai a quantidade indicada somente da pilha escolhida e alterna o jogador. A transição produz um novo estado, sem modificar o original. A ação precisa pertencer a \(\operatorname{AÇÕES}(s)\).

Exemplo:

\[
\operatorname{RESULTADO}((3,2,\text{MAX}),(A,2))=(1,2,\text{MIN})
\]

### Estado terminal

\[
\operatorname{TESTE\text{-}TERMINAL}(a,b,j)
\iff a=0 \land b=0
\]

O jogador que acabou de retirar a última pedra vence. Portanto, no estado terminal, `j` é o jogador que não tem uma jogada disponível e perdeu.

### Utilidade

No terminal, a utilidade é sempre vista da perspectiva de MAX:

\[
\operatorname{UTILIDADE}(s,\text{MAX}) =
\begin{cases}
+1 & \text{se } j=\text{MIN}\\
-1 & \text{se } j=\text{MAX}
\end{cases}
\]

Assim, `(0, 0, MIN)` vale `+1` (MAX retirou a última pedra) e `(0, 0, MAX)` vale `-1` (MIN retirou a última pedra). Como não há empate, os valores dos dois jogadores são opostos, caracterizando soma zero.

Na implementação, `utilidade(estado)` recebe apenas o estado: a perspectiva é fixa em MAX para evitar que um agente peça acidentalmente a avaliação pelo ponto de vista oposto.

## Propriedades do jogo

- **Dois jogadores:** MAX e MIN alternam turnos.
- **Soma zero:** a vitória de um jogador é a derrota do outro.
- **Informação perfeita:** ambos observam as duas pilhas e todas as jogadas anteriores.
- **Determinístico:** uma ação legal sempre produz o mesmo estado seguinte.
- **Horizonte finito:** cada jogada remove ao menos uma pedra; com \(a+b\) pedras, a partida termina em no máximo \(a+b\) jogadas.

### Regras implementadas

Em `jogo.py`, `Estado` e `Jogada` são dataclasses imutáveis. `Jogador` e `Pilha` são enums, evitando valores soltos no código. As quantidades das pilhas precisam ser inteiros não negativos; uma jogada precisa retirar uma quantidade inteira positiva.

- `criar_estado_inicial(a, b, jogador)` permite configurar as pilhas; por padrão cria `(8, 8, MAX)`.
- `jogador(estado)` devolve quem joga a seguir.
- `acoes(estado)` gera as retiradas legais em ordem: pilha A, depois B, e quantidade crescente em cada pilha.
- `resultado(estado, jogada)` valida a jogada, altera apenas a pilha selecionada e devolve um novo estado com o turno alternado. Não modifica o estado original.
- `teste_terminal(estado)` é verdadeiro quando as duas pilhas estão vazias.
- `utilidade(estado)` só aceita estado terminal e devolve `+1` se MAX venceu ou `-1` se MAX perdeu.

Os testes em `testes/test_jogo.py` cobrem estado inicial, ações legais, transições, alternância, terminalidade, utilidade e entradas inválidas. Para executar a suíte completa com Python 3:

```bash
python3 -m unittest discover -s testes -p 'test_*.py' -v
```

Validação das regras: **13 testes executados e aprovados**.

## Funcionamento dos algoritmos

### Minimax puro

`minimax(estado)` em `agentes.py` não usa poda, heurística, limite de profundidade ou memoização. Ele usa as funções de regra de `jogo.py`, mantendo as regras em um único módulo.

Em cada chamada, o algoritmo primeiro verifica se o estado é terminal. Se for, devolve a utilidade de MAX, nenhuma jogada e um nó visitado. Caso contrário, percorre todas as ações legais e chama Minimax em cada estado sucessor. MAX mantém o maior valor; MIN mantém o menor. A função retorna `(valor, melhor_jogada, nós_visitados)`. Se várias ações tiverem o mesmo valor, fica a primeira na ordem de `acoes()`.

O contador soma uma unidade por chamada recursiva, incluindo raiz e terminais. Uma posição alcançada por caminhos diferentes é contada novamente: não há tabela de transposição.

Execute todos os testes com:

```bash
python3 -m unittest discover -s testes -p 'test_*.py' -v
```

### Alfa-Beta

`alfa_beta(estado, alpha, beta, ordenar=False)` também busca até os estados terminais e retorna `(valor, melhor_jogada, nós_visitados)`. A janela padrão é \((-\infty,+\infty)\), então a busca completa na raiz retorna o valor minimax exato.

`alpha` é o melhor valor que MAX já consegue garantir no caminho atual; `beta` é o melhor valor que MIN já consegue garantir. MAX aumenta `alpha`; MIN diminui `beta`. Quando `alpha >= beta`, não é necessário explorar os sucessores restantes daquele nó. Cada chamada efetivamente visitada conta como nó; descendentes ignorados pela poda não são contados.

#### Ordenação de jogadas

Com `ordenar=False`, Alfa-Beta percorre a mesma sequência de ações de `acoes()`: A e depois B, quantidades crescentes. Com `ordenar=True`, `ordenar_acoes(estado)` coloca primeiro as ações cujo sucessor deixa as pilhas iguais (XOR zero). Essa posição é perdedora para quem joga a seguir no Nim de duas pilhas, então a ordenação tenta priorizar um sucessor favorável ao jogador atual. A ordenação muda o custo e pode mudar qual jogada empatada é retornada, mas não o valor minimax completo.

Medição registrada nos 32 estados com pilhas entre 0 e 3, considerando ambos os jogadores: Minimax visitou **1.128 nós**, Alfa-Beta natural **822**, e Alfa-Beta ordenado **504**. A ordem ordenada reduziu nós em 20 estados, empatou em 12 e não aumentou em nenhum. Isso é uma amostra pequena, não uma garantia de redução em outros estados.

Os testes em `testes/test_alfa_beta.py` comparam valores em profundidade completa nos 32 estados e verificam a contagem de nós.

### Avaliação heurística

`avaliacao_heuristica(estado)` estima uma posição **não terminal** e sempre retorna valor do ponto de vista de MAX:

- **Oportunidade imediata:** se exatamente uma pilha está vazia, o jogador da vez pode retirar todas as pedras restantes e vencer imediatamente. A característica vale `+1` para aquele jogador, recebe peso **0,8**, e não descreve uma vantagem independente do turno.
- **Paridade:** total ímpar recebe `+1` e total par `-1`, com peso **0,2**. É uma aproximação fraca baseada no modelo simplificado de retirar uma pedra por turno; as regras reais permitem retirar qualquer quantidade.

Os sinais são combinados e depois convertidos para a perspectiva de MAX. Assim, um sinal positivo favorece MAX, e um negativo favorece MIN, independentemente do jogador da vez. Os pesos dão maior influência à possibilidade concreta de vitória imediata; a paridade é secundária por ser apenas aproximada. A combinação fica no intervalo `[-1, +1]`.

Em estado terminal a função devolve `utilidade(estado)` diretamente; a heurística não altera resultados reais. Nos 30 estados não terminais com pilhas entre 0 e 3, seu sinal concordou com o Minimax completo em **26 casos (86,7%)**. O resultado descreve apenas esse conjunto. Os testes em `testes/test_avaliacao.py` validam sinais, perspectiva, limites e utilidade terminal.

### Alfa-Beta com limite de profundidade

`alfa_beta_limitado(estado, profundidade_maxima, alpha, beta, ordenar)` é separada da busca completa. A raiz começa na profundidade zero. Em cada chamada:

1. Verifica terminalidade e, se terminal, retorna a utilidade exata.
2. Se não terminal e atingiu o limite, retorna a heurística.
3. Caso contrário, expande jogadas e aplica Alfa-Beta.

O limite é o número de jogadas descidas desde a raiz. `profundidade_maxima=0` avalia diretamente uma raiz não terminal e retorna `None` como jogada; para escolher uma ação, use limite pelo menos 1. A função rejeita limites negativos, não inteiros e booleanos. `minimax()` e `alfa_beta()` continuam disponíveis como referências completas, sem corte heurístico. Os testes estão em `testes/test_alfa_beta_limitado.py`.

Em 30 posições não terminais pequenas comparadas ao resultado de Minimax completo, a concordância do sinal foi 26/30 (86,7%) na profundidade 0, 28/30 (93,3%) na profundidade 1 e 30/30 (100%) a partir da profundidade 2. Os nós visitados somados nessas posições foram 30, 126, 298, 522 e 692 para as profundidades 0 a 4. Esses resultados são específicos da amostra e não provam melhoria em outras instâncias.

## Agentes para partidas

Os três agentes estão em `agentes.py`; nenhum deles reimplementa as regras ou a busca existente.

### Agente aleatório

`agente_aleatorio(estado, seed=None)` escolhe uniformemente uma ação da lista `acoes(estado)` usando um `random.Random` local. A mesma semente e o mesmo estado reproduzem a mesma jogada. Retorna apenas `Jogada`; em estado terminal, retorna `None`. Ele não faz busca: não se deve atribuir a ele um número artificial de nós. Nos experimentos, seu custo de busca deve ser registrado como não aplicável (por exemplo, campo vazio/`None`), e não como zero nós explorados.

**Observação para os experimentos:** cada chamada cria um novo gerador. Para uma partida reproduzível, controle a sequência aleatória ao longo da partida; não reinicialize o agente com a mesma semente em todos os turnos, pois isso repetiria a escolha para estados equivalentes.

### Agente de busca de referência

`agente_busca_limitada(estado, profundidade=1, ordenar=False)` chama `alfa_beta_limitado()` com a heurística já existente. É a configuração mais rasa de referência: explora pelo menos uma jogada, sem ordenação por padrão. Pode receber outra profundidade e ativar ordenação. Retorna `(jogada, valor_estimado, nós_visitados)`; em terminal retorna `(None, utilidade_exata, 1)`. A busca limitada aceita profundidade zero, mas em raiz não terminal essa avaliação não escolhe jogada; por isso o wrapper do agente gera `ValueError` nesse caso.

### Agente principal

`agente_principal(estado, profundidade=3)` também delega a `alfa_beta_limitado()`, mas sempre ativa ordenação. A profundidade padrão **3 é uma proposta provisória**, não uma configuração aprovada: oferece uma busca mais profunda que a referência de profundidade 1, mantendo uma configuração pequena para iniciar os experimentos. Ainda não foi medida em partidas nem comparada em desempenho; os experimentos devem verificar se o custo e a qualidade justificam esse padrão. A profundidade pode ser sobrescrita ao chamar a função. Seu retorno e tratamento de terminais são iguais aos do agente de referência.

### Demonstração dos agentes

Execute na raiz do projeto, em `python3`, colando o bloco:

```python
from agentes import agente_aleatorio, agente_busca_limitada, agente_principal
from jogo import Estado, Jogador

estado = Estado(1, 2, Jogador.MAX)
print("aleatório:", agente_aleatorio(estado, seed=7))
print("busca de referência:", agente_busca_limitada(estado))
print("principal, profundidade 3:", agente_principal(estado, profundidade=3))
terminal = Estado(0, 0, Jogador.MIN)
print("aleatório terminal:", agente_aleatorio(terminal, seed=7))
print("busca terminal:", agente_busca_limitada(terminal, profundidade=1))
print("principal terminal:", agente_principal(terminal, profundidade=3))
```

Saída real:

```text
aleatório: Jogada(pilha=<Pilha.B: 'B'>, quantidade=1)
busca de referência: (Jogada(pilha=<Pilha.B: 'B'>, quantidade=1), 0.2, 4)
principal, profundidade 3: (Jogada(pilha=<Pilha.B: 'B'>, quantidade=1), 1, 10)
aleatório terminal: None
busca terminal: (None, 1, 1)
principal terminal: (None, 1, 1)
```

O exemplo mostra tanto a profundidade explicitamente configurada quanto o padrão provisório do agente principal. Os nós dos agentes de busca seguem a convenção do `alfa_beta_limitado()`: contam chamadas visitadas, incluindo raiz e terminais; folhas heurísticas também são chamadas e contam como nós.

## Execução de uma partida

`executar_partida()` em `experimentos.py` recebe os agentes de MAX e MIN, as quantidades iniciais das pilhas, quem começa e uma semente opcional. O retorno é um dicionário com estados inicial e final, vencedor, número de jogadas, configurações dos agentes e histórico. Cada registro do histórico inclui agente, jogador, estados anterior e posterior, ação, nós visitados e semente usada.

Para o agente aleatório, o motor mantém um gerador por partida e deriva uma semente para cada turno aleatório. A semente inicial fica no resultado; ao fornecer a mesma semente e configurações, a partida pode ser reproduzida. Se nenhuma for informada, o motor gera uma e também a registra. `nos_visitados` é `None` para o agente aleatório, pois ele não realiza busca.

Exemplo:

```python
from agentes import agente_aleatorio, agente_busca_limitada
from experimentos import executar_partida
from jogo import Jogador

partida = executar_partida(
    agente_max=agente_aleatorio,
    agente_min=agente_busca_limitada,
    pilha_a=2,
    pilha_b=1,
    jogador_inicial=Jogador.MAX,
    seed=2026,
)
print(partida["vencedor"])
print(partida["historico"])
```

Uma partida iniciada já em estado terminal não registra jogadas e retorna `vencedor=None`, pois nenhuma jogada foi feita para determinar um vencedor.

## Protocolo experimental e arquivos CSV

`configurar_confrontos()` monta os 16 confrontos aprovados: cinco contra o agente aleatório (dez repetições por combinação), seis comparando profundidades, quatro comparando ordenação e um confronto controlado. `gerar_posicoes_iniciais()` mantém as 80 posições ordenadas de `(0,0)` a `(8,8)`, excluindo apenas `(0,0)`. As quatro combinações de atribuição de agente a MAX/MIN e de jogador inicial são aplicadas a cada posição. Posições como `(2,5)` e `(5,2)` são simétricas neste jogo; são mantidas para seguir o protocolo, mas essa repetição estrutural deve ser considerada na interpretação.

`validar_protocolo_completo()` verifica a quantidade esperada de confrontos e partidas. O protocolo executado contém 3.200 partidas por cada um dos cinco confrontos aleatorizados (16.000 no grupo), 320 por cada um dos seis confrontos de profundidade (1.920), 320 por cada um dos quatro confrontos de ordenação (1.280) e 320 no confronto controlado: **19.520 partidas no total**. Os registros reais estão em [`resultados/final/`](./resultados/final/).

A estratégia ótima conhecida para o Nim de duas pilhas relaciona as quantidades de pedras por XOR: quando o XOR é zero, a posição é perdedora para quem joga sob jogo perfeito; caso contrário, existe uma jogada para chegar a XOR zero. Isso é conhecimento conhecido sobre o jogo, não uma descoberta inédita do projeto. Vitórias contra o agente aleatório, por si sós, também não demonstram superioridade geral. A heurística mantém os pesos já definidos; nenhum peso, profundidade ou outro parâmetro deve ser ajustado após observar os confrontos finais. Qualquer calibração teria de ocorrer antes da avaliação final e com esforço comparável entre configurações.

Para executar um piloto limitado com um confronto aleatorizado e um determinístico:

```python
from experimentos import configurar_confrontos, executar_experimentos

confrontos = configurar_confrontos()
piloto = executar_experimentos(
    confrontos=[confrontos[0], confrontos[5]],
    posicoes=[(0, 1), (1, 0)],
    repeticoes_aleatorias=2,
    diretorio_resultados="resultados/piloto",
)
print(len(piloto["partidas"]))
print(piloto["caminhos_csv"])
```

O piloto acima executa 24 partidas: 16 aleatorizadas e 8 determinísticas. Para confrontos aleatorizados, a semente da partida é `2026 + ((indice_posicao * 4 + indice_combinacao) * 10 + indice_repeticao)`. A semente não depende do confronto, então as combinações correspondentes reutilizam a mesma semente nos diferentes confrontos aleatorizados. Cada turno aleatório deriva e registra uma nova semente a partir do gerador persistente daquela partida.

Os CSVs são:

- `jogadas.csv`: uma linha por jogada, com estado anterior/posterior, agente, jogador, ação, nós e sementes.
- `partidas.csv`: uma linha por partida, com configuração, posição inicial, papéis, índices, vencedor e número de jogadas.
- `resumo.csv`: uma linha por agente em cada confronto. A taxa de vitória é `vitórias / partidas × 100`; os nós médios e máximos consideram apenas decisões que fizeram busca.

Nos CSVs, `N/A` significa que a métrica não se aplica, como os nós para o agente aleatório; nunca significa zero. Empates permanecem representados, embora as regras atuais do Nim não permitam empate. Executar novamente na mesma pasta substitui os CSVs nela.

## Exemplos de execução e demonstração

Execute os exemplos a partir da raiz do projeto, colando cada bloco no interpretador Python iniciado com `python3`. As saídas abaixo foram conferidas executando as chamadas no código atual.

### Regras: ações, transição, terminalidade e utilidade

Entrada: `(1, 2, MAX)`, jogada `(B, 2)`. A jogada retira duas pedras de B e alterna para MIN. O estado terminal `(0, 0, MIN)` indica que MAX retirou a última pedra, então a utilidade de MAX é `+1`.

```python
from jogo import Estado, Jogada, Jogador, Pilha, acoes, resultado
from jogo import teste_terminal, utilidade

estado = Estado(1, 2, Jogador.MAX)
print([(j.pilha.value, j.quantidade) for j in acoes(estado)])
print(resultado(estado, Jogada(Pilha.B, 2)))
terminal = Estado(0, 0, Jogador.MIN)
print(teste_terminal(terminal), utilidade(terminal))
```

Saída real:

```text
[('A', 1), ('B', 1), ('B', 2)]
Estado(pilha_a=1, pilha_b=0, jogador_atual=<Jogador.MIN: 'MIN'>)
True 1
```

### Minimax: MAX, MIN e desempate

O exemplo executa a mesma posição com cada jogador da vez. O valor continua sendo sempre da perspectiva de MAX. `(1, 1, MAX)` tem ações de mesmo valor ótimo; por isso o desempate mantém a primeira ação legal, retirar uma pedra de A.

```python
from agentes import minimax
from jogo import Estado, Jogador

print("MAX:", minimax(Estado(1, 2, Jogador.MAX)))
print("MIN:", minimax(Estado(1, 2, Jogador.MIN)))
print("empate:", minimax(Estado(1, 1, Jogador.MAX)))
```

Saída real:

```text
MAX: (1, Jogada(pilha=<Pilha.B: 'B'>, quantidade=1), 12)
MIN: (-1, Jogada(pilha=<Pilha.B: 'B'>, quantidade=1), 12)
empate: (-1, Jogada(pilha=<Pilha.A: 'A'>, quantidade=1), 5)
```

Cada nó é uma chamada de Minimax: raiz, estados internos e folhas terminais. O algoritmo visita todos os filhos; estados repetidos por caminhos diferentes seriam contados novamente, pois não há memoização.

### Alfa-Beta: janela e poda observável

Alfa-Beta retorna o mesmo valor que Minimax na posição. Neste exemplo `(1, 3, MAX)`, a poda evita visitar dois nós em comparação à busca completa. `alpha` registra a melhor garantia atual de MAX, `beta` a de MIN; quando `alpha >= beta`, os filhos restantes daquele nó não podem mudar a escolha de um ancestral e não são explorados.

```python
from agentes import alfa_beta, minimax
from jogo import Estado, Jogador

estado = Estado(1, 3, Jogador.MAX)
print("Minimax:", minimax(estado))
print("Alfa-Beta:", alfa_beta(estado))
```

Saída real:

```text
Minimax: (1, Jogada(pilha=<Pilha.B: 'B'>, quantidade=2), 28)
Alfa-Beta: (1, Jogada(pilha=<Pilha.B: 'B'>, quantidade=2), 26)
```

Minimax explora a árvore inteira. Alfa-Beta preserva o valor minimax, mas pode interromper a exploração de ramos irrelevantes. O contador inclui apenas chamadas realmente realizadas, incluindo a raiz e estados terminais visitados.

### Ordenação: ação priorizada e busca natural

Em `(3, 1, MAX)`, a ordenação coloca primeiro `(A, 2)`, pois ela deixa `(1, 1)`: as duas pilhas ficam iguais (XOR zero). A lista conserva todas as ações legais. A busca natural usa a ordem de `acoes()`; a ordenada usa essa lista reordenada em todos os níveis.

```python
from agentes import ordenar_acoes, alfa_beta
from jogo import Estado, Jogador, resultado

estado = Estado(3, 1, Jogador.MAX)
for jogada in ordenar_acoes(estado):
    sucessor = resultado(estado, jogada)
    print((jogada.pilha.value, jogada.quantidade),
          (sucessor.pilha_a, sucessor.pilha_b))
print("natural:", alfa_beta(estado))
print("ordenada:", alfa_beta(estado, ordenar=True))
```

Saída real:

```text
('A', 2) (1, 1)
('A', 1) (2, 1)
('A', 3) (0, 1)
('B', 1) (3, 0)
natural: (1, Jogada(pilha=<Pilha.A: 'A'>, quantidade=2), 24)
ordenada: (1, Jogada(pilha=<Pilha.A: 'A'>, quantidade=2), 16)
```

A ordenação muda a ordem de exploração e pode mudar o desempate, mas não o valor da busca completa.

### Heurística: pesos, perspectiva e terminais

Para `(0, 2, MAX)`, existe oportunidade imediata para quem joga: MAX pode retirar todas as pedras restantes. A característica recebe peso `0,8`; o total par recebe sinal `-1` e peso `0,2`. A soma é `0,6` para MAX. Com MIN na vez, o mesmo sinal vira `-0,6` para manter a perspectiva fixa de MAX. Em terminal, a função ignora a estimativa e usa utilidade exata.

```python
from agentes import avaliacao_heuristica
from jogo import Estado, Jogador

print(avaliacao_heuristica(Estado(0, 2, Jogador.MAX)))
print(avaliacao_heuristica(Estado(0, 2, Jogador.MIN)))
print(avaliacao_heuristica(Estado(0, 0, Jogador.MIN)))
```

Saída real:

```text
0.6000000000000001
-0.6000000000000001
1
```

O pequeno resíduo decimal é da representação de ponto flutuante. A estimativa não substitui os resultados exatos de vitória/derrota nos estados terminais.

### Busca limitada: corte heurístico versus terminal

Em `(1, 2, MAX)`, profundidade zero avalia a raiz não terminal pela heurística e não escolhe jogada. Na profundidade 1, escolhe um lance e avalia as folhas não terminais. Na profundidade 2, o valor retornado nesta posição coincide com o Minimax completo; folhas não terminais ainda podem receber avaliação heurística. Terminalidade tem prioridade mesmo se o limite já foi atingido.

```python
from agentes import alfa_beta_limitado
from jogo import Estado, Jogador

estado = Estado(1, 2, Jogador.MAX)
for profundidade in (0, 1, 2):
    print(profundidade, alfa_beta_limitado(estado, profundidade))
print("terminal no corte zero:",
      alfa_beta_limitado(Estado(0, 0, Jogador.MIN), 0))
```

Saída real:

```text
0 (0.2, None, 1)
1 (0.2, Jogada(pilha=<Pilha.B: 'B'>, quantidade=1), 4)
2 (1.0, Jogada(pilha=<Pilha.B: 'B'>, quantidade=1), 9)
terminal no corte zero: (1, None, 1)
```

A busca completa Minimax/Alfa-Beta continua disponível e não usa heurística nem corte de profundidade.

## Testes e verificação de corretude

Na raiz do projeto, execute a suíte completa:

```bash
python3 -m unittest discover -s testes -p 'test_*.py' -v
```

Os testes estão organizados por funcionalidade:

- `testes/test_jogo.py` (13 testes): estado inicial configurável, ações legais, estado terminal, transições, alternância, utilidade e rejeição de entradas inválidas.
- `testes/test_minimax.py` (4 testes): escolhas de MAX e MIN, folha terminal, desempate e contagem de nós.
- `testes/test_alfa_beta.py` (7 testes): MAX/MIN, terminal, desempate, ordenação e equivalência com Minimax em 32 estados; também confirma que Alfa-Beta não visita mais nós que Minimax nesses estados.
- `testes/test_avaliacao.py` (5 testes): utilidade terminal, característica da pilha única, paridade e conversão de sinal, intervalo da avaliação e concordância com Minimax em estados pequenos.
- `testes/test_alfa_beta_limitado.py` (7 testes): corte na raiz, prioridade dos terminais sobre o corte, jogada legal, validação do limite e equivalência com a busca completa quando a profundidade basta.
- `testes/test_agentes.py` (9 testes): legalidade e reprodutibilidade do agente aleatório, retornos/contagem dos agentes de busca, configurações de profundidade e ordenação, além de terminais e corte sem jogada.
- `testes/test_experimentos.py` (15 testes): partidas determinísticas e aleatórias, atribuição dos agentes a MAX/MIN, vencedor, histórico, contagem de nós, reprodução e variação de sementes, jogador inicial e retornos inválidos.
- `testes/test_protocolo_experimentos.py`: posições, combinações, confrontos, sementes, métricas, exportação/reprodutibilidade dos CSVs e cancelamento sem publicação parcial.
- `testes/test_tela_partida.py`: jogadas humanas e automáticas, agentes com profundidade, aleatoriedade, rejeição de jogada inválida, início por MIN e navegação entre telas.
- `testes/test_tela_algoritmos.py`: conceitos, demonstração real de busca, árvore de sucessores e explicação interpretativa.
- `testes/test_tela_resultados.py`: leitura dos CSVs finais, métricas e histórico exibidos.
- `testes/test_tela_experimentos.py`: configuração personalizada, validação, confirmação do protocolo e exportação isolada.
- `testes/test_tela_guia.py`: seções do guia e consulta dos dados finais.
- `testes/test_rolagem_interface.py`: roda do mouse, barra de rolagem, rolagem interna de texto e limpeza de bindings.

**Última execução confirmada nesta versão:** `./.venv/bin/python -m unittest discover -s testes -p 'test_*.py' -v`; 96 testes executados em 13.789 s, todos aprovados (`OK`). A suíte automatizada verifica navegação, rolagem da página e de texto interno, adaptação dos textos da demonstração à largura disponível, guia, leitura dos CSVs, execução personalizada isolada e cancelamento sem publicar resultados parciais.

## Validação do piloto experimental

O piloto foi executado para dois confrontos, com as posições `(0,1)` e `(1,0)`: aleatório vs. busca limitada d1 e busca limitada d1 vs. d2. Foram executadas **24 partidas**, sendo 16 aleatorizadas e 8 determinísticas. Os CSVs estão em [`resultados/piloto/`](./resultados/piloto/). Uma segunda execução em diretório temporário produziu arquivos byte a byte idênticos, verificados por SHA-256.

No confronto aleatório vs. d1, cada lado venceu 8 das 16 partidas (50% cada); o agente de busca teve 8 decisões, média de 2 nós e máximo de 2, enquanto para o aleatório os nós são `N/A`. No confronto d1 vs. d2, cada configuração venceu 4 das 8 partidas (50% cada); ambas tiveram 4 decisões, média de 2 nós e máximo de 2. Como as posições iniciais do piloto continham apenas uma pedra, cada partida terminou em uma jogada. Esses dados verificam a geração e o registro em pequena escala; não são os resultados dos 19.520 jogos, nem demonstram superioridade geral.

Hashes SHA-256 dos CSVs gerados:

```text
91a586ab0981562b1efceaeac49faf5e60ddf8a51cc6059cc3a03c6fe7757c68  jogadas.csv
97c2fbce18be90d7ebd43374b84d818f17f7f8d2b508c70a642080d5bdfa48c3  partidas.csv
6720de365ac0739920cd266579cdb0f908168d0e1bdb49ec190762b61c184364  resumo.csv
```

## Resultados já medidos

Na amostra de 32 estados com cada pilha entre 0 e 3 e ambos os jogadores:

| Busca | Total de nós visitados |
|---|---:|
| Minimax | 1.128 |
| Alfa-Beta natural | 822 |
| Alfa-Beta ordenado | 504 |

Os três métodos completos retornaram o mesmo valor minimax. Em relação a Minimax, Alfa-Beta visitou no máximo o mesmo número de nós em cada estado da amostra; a ordenação reduziu nós em 20 estados, empatou em 12 e não aumentou em nenhum.

Na comparação da heurística com Minimax, considerando as 30 posições **não terminais** da mesma faixa de pilhas, a concordância do sinal foi 26/30 (86,7%) na profundidade 0 (heurística aplicada à raiz), 28/30 (93,3%) na profundidade 1 e 30/30 (100%) nas profundidades 2 ou maiores. Os totais documentados para essas 30 raízes não terminais foram 30, 126, 298, 522 e 692 nós nas profundidades 0 a 4. Os estados terminais não fazem parte dessa medição.

Esses números são verificações pequenas de busca em estados enumerados, separadas dos resultados dos confrontos entre agentes em [`resultados/final/`](./resultados/final/).

## Próximos passos da entrega

O protocolo completo e os CSVs já foram gerados; as telas da interface têm funcionalidades didáticas e de execução. As telas foram inspecionadas visualmente em tamanho normal; a demonstração de Algoritmos ajusta as explicações à largura disponível. A inspeção em janela reduzida não pôde ser concluída neste ambiente: o gerenciador de janelas redimensionou o pedido de 900 px para pelo menos 1280 px. Ainda é necessário revisar e preencher o template acadêmico da disciplina e conferir a ficha e o guia oficiais. A rolagem automatizada e a integração das telas têm testes, mas isso não substitui uma demonstração visual manual em outras configurações. Para acompanhar outras pendências da entrega, consulte [`OQueFaltanoProjeto.md`](./OQueFaltanoProjeto.md).
