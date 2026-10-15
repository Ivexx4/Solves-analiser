# Dashboard de análise de speedcubing

Dashboard interativo em Streamlit para explorar tempos de resolução, penalizações,
consistência e evolução do desempenho ao longo do tempo. Os gráficos são criados
com Plotly e podem ser ampliados, explorados com o rato e, quando aplicável,
filtrados clicando na legenda.

## Requisitos

- Python 3.10 ou superior
- Streamlit
- pandas
- NumPy
- Plotly
- statsmodels (utilizado pela linha de tendência da análise “Velocidade vs Consistência”)

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

## Executar

Na pasta do projeto, execute:

```powershell
python -m streamlit run app.py
```

O `app.py` exporta a aplicação ASGI e encaminha para a interface definida em
`dashboard.py`. Também podes iniciar diretamente com `python app.py`.
Esta separação permite que runtimes Python que procuram uma variável ASGI
`app` reconheçam o ponto de entrada.

O Streamlit apresenta no terminal o endereço local do dashboard, normalmente
`http://localhost:8501`.

## Importar dados

O dashboard inicia vazio e apresenta um ecrã de importação. Use o seletor
**Idioma / Language** para alternar entre português e inglês. A documentação em
inglês está em [README.en.md](README.en.md). Use o importador único para
selecionar vários ficheiros `.json` ou `.txt`, incluindo ficheiros de ambos os
temporizadores.
Clique em **Importar solves** para acrescentar as solves ao histórico que já
está na sessão atual do Streamlit. A deduplicação compara scramble, tempo
arredondado a centésimos e penalização; não usa data/hora, que pode ser igual
para solves diferentes. Solves sem scramble são mantidas, pois não é possível
confirmar com segurança se são repetidas. Se já tinhas dados carregados antes
desta alteração, limpa-os e importa os ficheiros novamente para incluir os
scrambles.
Duplicados removidos são indicados após a importação. Pode importar novamente
um ficheiro sem repetir solves; use **Limpar dados importados** para começar um
histórico novo. Antes de importar, a tabela de pré-visualização indica o tipo
detetado (Cubolandia singles, Cubolandia averages ou CS Timer), a quantidade de
solves e se o ficheiro está pronto. Se algum ficheiro não for reconhecido, a
importação é bloqueada para evitar ignorar dados inadvertidamente.
O tipo é identificado pela estrutura do JSON: lista de registos Cubolandia
com `c` vazio/`Avg:` para singles, cinco tempos em `c` para averages, ou objeto
com sessões `sessionN` para CS Timer.
Não são carregados ficheiros locais automaticamente. O resultado da leitura é
guardado em cache pelo Streamlit com base no conteúdo dos ficheiros (até 10
combinações diferentes por processo), evitando voltar a analisar os mesmos
JSON em importações repetidas durante a execução do servidor.

Os formatos suportados são:

- `data_Cubo3x3x3Normal.json` — solves individuais.
- `data_Cubo3x3x3NormalAVG.json` — sessões Ao5; o campo `c` é expandido para as
  cinco solves que compõem cada média.
- Exportação CS Timer em `.txt` ou `.json` — ficheiro JSON com sessões `sessionN`;
  os tempos em milissegundos são convertidos para segundos, com suporte para
  penalização +2 e DNF.

O módulo `carregamento_dados.py` disponibiliza `load_singles()`,
`load_averages()`, `load_cstimer()` e `combine_solves()` para que cada etapa
possa ser usada e testada de forma independente. Os registos Ao5 duplicados no
ficheiro de singles (datas terminadas em `(1)` a `(5)`) são ignorados quando o
ficheiro de singles é importado, pois os mesmos tempos vêm do ficheiro AVG.

Para gerar também uma cópia consolidada em CSV, execute:

```powershell
.\.venv\Scripts\python.exe carregamento_dados.py
```

O ficheiro `combined_solves.csv` é uma exportação opcional para análise externa;
o dashboard importa os ficheiros selecionados no ecrã do Streamlit.

Os JSON do Cubolandia Timer devem conter uma lista de registos com estas propriedades:

| Coluna | Tipo esperado | Descrição |
|---|---|---|
| `i` | Data/hora reconhecida por pandas | Data e hora da solve ou sessão |
| `s` | Texto | Scramble associado à solve (ou lista de scrambles no campo `s` dos averages) |
| `n` | Número | Tempo do single em segundos; `-1` representa DNF |
| `t` | Número inteiro | Penalização do single: `0` limpo, `1` +2 segundos, `2` DNF |
| `c` | Texto (ficheiro AVG) | Lista textual das cinco solves, incluindo `DNF`, `+2` e parênteses de corte |

As linhas combinadas são normalizadas para as colunas `date`, `time` e
`penalty`, e ordenadas por `date`. O carregador converte DNFs para tempo
infinito (`time = inf`) e penalização `2`.

Na exportação CS Timer, cada chave `sessionN` contém solves no formato
`[[penalty, time_ms], scramble, comment, timestamp]`. O carregador converte
`time_ms` para segundos, adiciona a penalização de 2000 ms (+2), trata tempos
negativos ou penalização `-1` como DNF e interpreta `timestamp` como Unix time
em segundos.

## Utilização

Selecione o intervalo de datas na barra lateral. As análises e gráficos usam os
registos dentro desse intervalo. Navegue pelas categorias usando os separadores
e escolha o gráfico pretendido no menu “Gráfico” dentro do separador. O gráfico
selecionado é apresentado abaixo dos separadores. As métricas “Melhor Ao5” e
“Melhor Ao12” no cabeçalho são uma exceção: são calculadas sobre todo o
histórico carregado.

As métricas e gráficos de tempo usam apenas solves com `time` finito. As
contagens gerais, taxas de penalização, sessões e solves por dia podem incluir
registos DNF, conforme indicado em cada análise.

## Navegação e análises

O dashboard está organizado em quatro **abas de categoria**. Dentro da aba
selecionada, use o menu **Gráfico** para escolher uma análise. O gráfico escolhido
é apresentado abaixo das abas; todas as opções existentes continuam disponíveis.

### Desempenho e recordes

- **Evolução Temporal** — tempos individuais por penalização e médias móveis Ao5 e Ao12.
- **Distribuição** — histograma e boxplot dos tempos válidos.
- **PB Progression** — melhor tempo acumulado ao longo do intervalo.
- **Média Global** — média acumulada e PB acumulado.
- **Frequência de PB** — novos recordes por mês, último PB e média de dias entre recordes.
- **Probabilidade de PB** — frequência de PBs nas últimas 100, 500 e 1000 solves, mais a frequência móvel de 100.
- **Ao100 / Ao1000** — médias móveis simples de 100 e 1000 solves comparadas com Ao5 e Ao12.

### Consistência

- **Consistência Mensal** — boxplot dos tempos por mês.
- **Consistência** — coeficiente de variação móvel (desvio padrão ÷ média × 100) em janelas de 50 solves.
- **Percentis** — percentis 10, 50 e 90 em janelas de 100 solves.
- **Velocidade vs Consistência** — média móvel e coeficiente de variação de 50 solves, com tendência linear.
- **Aquecimento** — compara primeiras e últimas 10 solves de sessões com pelo menos 20 tempos válidos; diferença negativa significa melhoria.
- **Fadiga** — divide cada sessão em dez blocos de progresso e mostra o tempo médio por bloco.
- **Control Chart** — tempos, média móvel de 100 solves e limites móveis de ±1 e ±2 desvios padrão.

### Treino e sessões

- **Sub-X Rate** — percentagem móvel de tempos iguais ou inferiores ao alvo escolhido.
- **Solves por Dia** — volume diário e média móvel de sete dias.
- **Sessões** — uma pausa superior a 30 minutos inicia outra sessão. A tabela apresenta tamanho, duração, média, melhor tempo e desvio padrão. DNFs contam para o tamanho, mas não para estatísticas de tempo; a melhor sessão é a de menor média.

### Penalizações e horários

- **Penalizações** — contagem de solves limpas, +2 e DNF.
- **Hora do Dia** — distribuição de tempos por hora.
- **Hora × Dia** — heatmaps do tempo médio e número de solves válidos por hora e dia da semana.

## Notas sobre os cálculos

- Ao5 e Ao12 aplicam o corte WCA: removem o melhor e o pior tempo de cada janela e calculam a média dos restantes. Os tempos usados são os valores finitos existentes na coluna `time`.
- Médias Ao100 e Ao1000 são médias aritméticas móveis simples.
- As análises de consistência usam o coeficiente de variação (CV), calculado
  como desvio padrão ÷ média × 100, para comparar a dispersão relativa mesmo
  quando o nível médio dos tempos muda. Um CV menor representa maior
  consistência relativa.
- As médias móveis normalmente só aparecem depois de existir uma janela completa de solves.
- Os PBs nas análises “Frequência de PB” e “Probabilidade de PB” são detetados relativamente aos tempos válidos dentro do intervalo selecionado. Assim, o primeiro tempo do intervalo serve de referência e não é contado como novo PB; alterar a data inicial pode alterar as contagens.
- “Probabilidade de PB” é uma frequência histórica observada, não uma previsão estatística da próxima solve.
- A duração da sessão é o tempo entre a primeira e a última solve dessa sessão; não inclui o tempo de pausa até à sessão seguinte.
