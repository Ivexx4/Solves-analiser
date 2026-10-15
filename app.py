from io import BytesIO

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from carregamento_dados import (
    combine_solves,
    deduplicate_solves,
    load_averages,
    load_cstimer,
    load_singles,
)

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Speedcubing Dashboard",
    page_icon="🧩",
    layout="wide"
)


TRANSLATIONS = {
    "Painel Interativo de Análise de Speedcubing": "Interactive Speedcubing Dashboard",
    "Português": "Portuguese",
    "English": "English",
    "Idioma / Language": "Language / Idioma",
    "Importar solves do Cubolandia Timer": "Import solves",
    "Carregue ficheiros do Cubolandia Timer (singles/averages) e/ou uma exportação do CS Timer. Cada importação acrescenta solves ao histórico atual; use o botão de limpar para começar de novo.":
        "Upload Cubolandia Timer singles/averages files and/or a CS Timer export. Each import appends solves to the current history; use the clear button to start over.",
    "Os scrambles são usados para identificar a mesma solve entre ficheiros; solves sem scramble são mantidas para evitar falsos duplicados.":
        "Scrambles identify the same solve across files; solves without a scramble are kept to avoid false duplicates.",
    "Os dados já carregados não incluem scrambles. Limpa os dados e importa os ficheiros novamente para usar a nova deteção de duplicados.":
        "The currently loaded data has no scrambles. Clear it and re-import the files to use the updated duplicate detection.",
    "Ficheiro de singles (.json)": "Singles file (.json)",
    "Ficheiro de averages (.json)": "Averages file (.json)",
    "Exportação CS Timer (.txt ou .json)": "CS Timer export (.txt or .json)",
    "Importar solves": "Import solves",
    "Limpar dados importados": "Clear imported data",
    "Seleciona pelo menos um ficheiro antes de importar.":
        "Select at least one file before importing.",
    "Os ficheiros selecionados não contêm solves para importar.":
        "The selected files contain no solves to import.",
    "Não foi possível importar os ficheiros: ": "Could not import the files: ",
    "O dashboard está vazio. Importa ficheiros do Cubolandia Timer ou CS Timer para começar.":
        "The dashboard is empty. Import files from Cubolandia Timer or CS Timer to get started.",
    "Importação concluída: ": "Import complete: ",
    " solves novas; ": " new solves; ",
    " duplicados removidos (CS Timer: ": " duplicates removed (CS Timer: ",
    "Importadas ": "Imported ",
    " solves singles e ": " singles and ",
    " solves extraídas dos averages; ": " solves extracted from averages; ",
    " solves CS Timer (": " CS Timer solves (",
    " solves no total).": " solves in total).",
    "Passe o rato sobre os gráficos para ver detalhes, utilize os comandos de zoom e explore o seu histórico de resoluções.":
        "Hover over charts for details, use the zoom controls, and explore your solve history.",
    "Filtros": "Filters",
    "Selecione o intervalo de datas": "Select date range",
    "📊 Visão Geral e Indicadores de Desempenho": "📊 Overview and Performance Indicators",
    "Total de Solves": "Total Solves",
    "Tempo Médio": "Average Time",
    "Melhor Tempo (PB)": "Best Time (PB)",
    "Melhor Ao5": "Best Ao5",
    "Melhor Ao12": "Best Ao12",
    "Taxa de Limpeza": "Clean Solve Rate",
    "Taxa de DNF": "DNF Rate",
    "Streak Máxima": "Longest Streak",
    "dias": "days",
    "Desempenho e recordes": "Performance and Records",
    "Consistência": "Consistency",
    "Treino e sessões": "Practice and Sessions",
    "Penalizações e horários": "Penalties and Timing",
    "Gráfico": "Chart",
    "Evolução Temporal": "Time Evolution",
    "Distribuição": "Distribution",
    "PB Progression": "PB Progression",
    "Média Global": "Overall Average",
    "Frequência de PB": "PB Frequency",
    "Probabilidade de PB": "PB Probability",
    "Ao100 / Ao1000": "Ao100 / Ao1000",
    "Consistência Mensal": "Monthly Consistency",
    "Percentis": "Percentiles",
    "Velocidade vs Consistência": "Speed vs Consistency",
    "Aquecimento": "Warm-up",
    "Fadiga": "Fatigue",
    "Control Chart": "Control Chart",
    "Sub-X Rate": "Sub-X Rate",
    "Solves por Dia": "Solves per Day",
    "Sessões": "Sessions",
    "Penalizações": "Penalties",
    "Hora do Dia": "Time of Day",
    "Hora × Dia": "Hour × Day",
    "Evolução Temporal e Médias Móveis (Ao5 / Ao12)": "Time Evolution and Moving Averages (Ao5 / Ao12)",
    "Dica: Pode selecionar uma área para fazer zoom ou clicar nas legendas para ocultar/mostrar séries.":
        "Tip: Select an area to zoom in, or click legend items to hide/show series.",
    "Limpo (0)": "Clean (0)",
    "+2 Segundos": "+2 Seconds",
    "DNF (Não Concluído)": "DNF (Unsolved)",
    "DNF": "DNF",
    "Data": "Date",
    "Tempo (s)": "Time (s)",
    "Penalização": "Penalty",
    "Histórico de Solves e Médias Móveis": "Solve History and Moving Averages",
    "Média Móvel (Ao5)": "Moving Average (Ao5)",
    "Média Móvel (Ao12)": "Moving Average (Ao12)",
    "Distribuição de Frequência dos Tempos": "Solve Time Distribution",
    "Frequência": "Frequency",
    "Histograma e Distribuição dos Tempos": "Solve Time Histogram and Distribution",
    "Proporção de Penalizações": "Penalty Breakdown",
    "Tipo": "Type",
    "Quantidade": "Count",
    "Contagem por Tipo de Penalização": "Count by Penalty Type",
    "Desempenho por Hora do Dia": "Performance by Time of Day",
    "Hora do Dia": "Hour of Day",
    "Distribuição de Tempos por Hora (Boxplot Interativo)": "Solve Time Distribution by Hour (Interactive Box Plot)",
    "Consistência dos Tempos por Mês": "Monthly Solve Time Consistency",
    "Mês": "Month",
    "Evolução Mensal da Consistência": "Monthly Consistency Trend",
    "Progressão do Recorde Pessoal": "Personal Best Progression",
    "PB (s)": "PB (s)",
    "Análise das Sessões de Treino": "Practice Session Analysis",
    "Uma nova sessão começa após mais de 30 minutos sem solves.":
        "A new session starts after more than 30 minutes without a solve.",
    "inicio": "start",
    "fim": "end",
    "solves": "solves",
    "duração (min)": "duration (min)",
    "tempo médio (s)": "average time (s)",
    "melhor solve (s)": "best solve (s)",
    "desvio padrão (s)": "standard deviation (s)",
    "sessão": "session",
    "Melhor sessão (média)": "Best Session (Average)",
    "Sessão mais longa": "Longest Session",
    "Tamanho médio das sessões": "Average Session Size",
    "Número de solves": "Number of Solves",
    "Duração (min)": "Duration (min)",
    "Tamanho, desempenho e duração das sessões": "Session Size, Performance, and Duration",
    "Não há solves no intervalo selecionado.": "There are no solves in the selected date range.",
    "Efeito de Aquecimento": "Warm-up Effect",
    "Compara as primeiras 10 com as últimas 10 solves de cada sessão com pelo menos 20 tempos válidos.":
        "Compares the first 10 and last 10 solves in each session with at least 20 valid times.",
    "Melhoria / piora média": "Average Improvement / Decline",
    "Sessões com melhoria": "Sessions with Improvement",
    "diferença (s)": "difference (s)",
    "Últimas 10 − primeiras 10 (s)": "Last 10 − first 10 (s)",
    "Distribuição das diferenças por sessão": "Distribution of Differences by Session",
    "Grupo": "Group",
    "Primeiras 10 solves": "First 10 Solves",
    "Últimas 10 solves": "Last 10 Solves",
    "Tempo médio (s)": "Average Time (s)",
    "Tempo médio no início vs. final das sessões": "Average Time at the Start vs. End of Sessions",
    "Não existem sessões com pelo menos 20 solves de tempo válido no intervalo selecionado.":
        "There are no sessions with at least 20 valid solve times in the selected date range.",
    "Efeito de Fadiga": "Fatigue Effect",
    "Cada sessão é dividida em 10 blocos de progresso; tempos mais altos no final podem indicar fadiga.":
        "Each session is split into 10 progress blocks; slower times near the end may indicate fatigue.",
    "progresso": "progress",
    "Progresso na sessão": "Session Progress",
    "Evolução Temporal e Médias Móveis (Ao5 / Ao12)": "Time Evolution and Moving Averages (Ao5 / Ao12)",
    "Dica: Pode selecionar uma área para fazer zoom ou clicar nas legendas para ocultar/mostrar séries.": "Tip: Select an area to zoom in, or click legend items to hide/show series.",
    "Distribuição de Frequência dos Tempos": "Solve Time Distribution",
    "Distribuição de Tempos por Hora (Boxplot Interativo)": "Solve Time Distribution by Hour (Interactive Box Plot)",
    "Consistência dos Tempos por Mês": "Monthly Solve Time Consistency",
    "Progressão do Recorde Pessoal": "Personal Best Progression",
    "Análise das Sessões de Treino": "Practice Session Analysis",
    "Sessão": "Session",
    "Melhor sessão (média)": "Best session (average)",
    "Sessão mais longa": "Longest session",
    "Melhoria / piora média": "Average improvement / decline",
    "Sessões com melhoria": "Sessions with improvement",
    "Últimas 10 − primeiras 10 (s)": "Last 10 − first 10 (s)",
    "Taxa de Solves Sub-X": "Sub-X Solve Rate",
    "Quantidade de Solves por Dia": "Solves per Day",
    "Médias Móveis Ao5, Ao12, Ao100 e Ao1000": "Moving Averages Ao5, Ao12, Ao100, and Ao1000",
    "Consistência Relativa ao Longo do Tempo": "Relative Consistency Over Time",
    "CV = desvio padrão ÷ média × 100. Um CV menor indica tempos mais consistentes relativamente ao nível médio de velocidade.": "CV = standard deviation ÷ mean × 100. A lower CV indicates more consistent times relative to the average speed.",
    "O objetivo ideal é aproximar-se do canto inferior esquerdo (mais rápido e mais consistente relativamente à média).": "The ideal is to move toward the lower-left corner (faster and more consistent relative to the mean).",
    "Cada ponto representa uma janela móvel de 50 solves. A cor e a linha ligada indicam a ordem temporal; passe o rato sobre um ponto para ver a data.": "Each point represents a rolling window of 50 solves. Color and the connecting line show chronological order; hover over a point to see the date.",
    "Médias Móveis Ao5, Ao12, Ao100 e Ao1000": "Moving Averages Ao5, Ao12, Ao100, and Ao1000",
    "A estimativa usa apenas solves anteriores dentro do intervalo de datas selecionado.": "This estimate uses only previous solves within the selected date range.",
    "São necessárias pelo menos 50 solves válidas no intervalo selecionado.": "At least 50 valid solves are required in the selected date range.",
    "Últimas ": "Last ",
    " PBs em ": " PBs in ",
    "Nao há dados": "No data",
    "min": "min",
    " solve(s)": " solve(s)",
    "N/A": "N/A",
    "PB (s)": "PB (s)",
    "Histórico de Solves e Médias Móveis": "Solve History and Moving Averages",
    "Média Móvel (Ao5)": "Moving Average (Ao5)",
    "Média Móvel (Ao12)": "Moving Average (Ao12)",
    "Tempo médio (s)": "Average Time (s)",
    "Mês": "Month",
    "Hora do Dia": "Hour of Day",
    "Penalização": "Penalty",
    "Frequência": "Frequency",
    "Contagem por Tipo de Penalização": "Count by Penalty Type",
    "Histograma e Distribuição dos Tempos": "Solve Time Histogram and Distribution",
    "Evolução Mensal da Consistência": "Monthly Consistency Trend",
    "Tempo médio no início vs. final das sessões": "Average Time at Start vs. End of Sessions",
    "Tempo médio por bloco de progresso": "Average Time by Progress Block",
    "Heatmap: Hora do Dia × Dia da Semana": "Heatmap: Hour of Day × Day of Week",
    "Média acumulada e recorde pessoal acumulado": "Cumulative Mean and Cumulative Personal Best",
    "Novos recordes pessoais por mês": "New Personal Bests per Month",
    "Frequência móvel de PBs (janela de 100 solves)": "Rolling PB Frequency (100-solve Window)",
    "Forma atual e nível de desempenho a longo prazo": "Current Form and Long-term Performance Level",
    "Tempo das solves e limites móveis de controlo": "Solve Times and Rolling Control Limits",
    "Variabilidade relativa em janelas de 50 solves": "Relative Variability in 50-solve Windows",
    "Velocidade vs. consistência relativa ao longo do tempo": "Speed vs. Relative Consistency Over Time",
    "Média dos últimos 50 solves (s)": "Average of Last 50 Solves (s)",
    "Coeficiente de variação dos últimos 50 (%)": "Coefficient of Variation of Last 50 Solves (%)",
    "Percurso cronológico": "Chronological Path",
    "Janela de 50 solves": "50-solve Window",
    "Tendência linear": "Linear Trend",
    "Média acumulada": "Cumulative Mean",
    "PB acumulado": "Cumulative PB",
    "Média móvel (linha central)": "Moving Average (Center Line)",
    "Média 7 dias": "7-day Average",
    "Último PB": "Latest PB",
    "Nenhum PB no intervalo": "No PB in the selected date range",
    "Média de dias entre PBs": "Average Days Between PBs",
    "PBs por solve (%)": "PBs per Solve (%)",
    "Primeiras 10 solves": "First 10 Solves",
    "Últimas 10 solves": "Last 10 Solves",
    "Número de solves": "Number of Solves",
    "Tempo médio (s)": "Average Time (s)",
    "Progresso na sessão": "Session Progress",
    "Dia da semana": "Day of Week",
    "Tempo médio (s)": "Average Time (s)",
    "Data": "Date",
    "Tempo (s)": "Time (s)",
    "Hora": "Hour",
    "Número de Solves": "Number of Solves",
    "Média dos últimos 50": "Average of Last 50",
    "Data: %{customdata[0]}<br>Média dos últimos 50: %{x:.2f}s<br>CV dos últimos 50: %{y:.2f}%<extra></extra>":
        "Date: %{customdata[0]}<br>Average of last 50: %{x:.2f}s<br>CV of last 50: %{y:.2f}%<extra></extra>",
    "Os ficheiros selecionados não contêm solves para importar.": "The selected files contain no solves to import.",
    "Não existem sessões com pelo menos 20 solves de tempo válido no intervalo selecionado.": "There are no sessions with at least 20 valid solve times in the selected date range.",
    "Tempo médio por bloco de progresso": "Average Time by Progress Block",
    "Não há tempos válidos para analisar fadiga.": "There are no valid times to analyze fatigue.",
    "Heatmap: Hora do Dia × Dia da Semana": "Heatmap: Hour of Day × Day of Week",
    "Segunda": "Monday",
    "Terça": "Tuesday",
    "Quarta": "Wednesday",
    "Quinta": "Thursday",
    "Sexta": "Friday",
    "Sábado": "Saturday",
    "Domingo": "Sunday",
    "Dia da semana": "Day of Week",
    "Tempo médio (s)": "Average Time (s)",
    "Evolução da Média Global": "Overall Average Progression",
    "média acumulada": "cumulative mean",
    "PB acumulado": "cumulative PB",
    "Média acumulada": "Cumulative Mean",
    "Novos recordes pessoais por mês": "New Personal Bests per Month",
    "Frequência de PB": "PB Frequency",
    "Total de PBs": "Total PBs",
    "Último PB": "Latest PB",
    "Nenhum PB no intervalo": "No PB in this date range",
    "Média de dias entre PBs": "Average Days Between PBs",
    "Quantidade de PBs": "Number of PBs",
    "Probabilidade Histórica de PB": "Historical PB Probability",
    "Últimas ": "Last ",
    " PBs em ": " PBs in ",
    "PBs por solve (%)": "PBs per Solve (%)",
    "Frequência móvel de PBs (janela de 100 solves)": "Rolling PB Frequency (100-solve window)",
    "A estimativa usa apenas solves anteriores dentro do intervalo de datas selecionado.":
        "This estimate uses only previous solves within the selected date range.",
    "Médias Móveis Ao5, Ao12, Ao100 e Ao1000": "Moving Averages Ao5, Ao12, Ao100, and Ao1000",
    "Data": "Date",
    "Forma atual e nível de desempenho a longo prazo": "Current Form and Long-term Performance Level",
    "A linha central e os limites de controlo são calculados numa janela móvel de 100 solves.":
        "The center line and control limits are calculated over a rolling 100-solve window.",
    "Solve": "Solve",
    "Média móvel (linha central)": "Moving Average (Center Line)",
    "Tempo das solves e limites móveis de controlo": "Solve Times and Rolling Control Limits",
    "Não há tempos válidos no intervalo selecionado.": "There are no valid solve times in the selected date range.",
    "Consistência Relativa ao Longo do Tempo": "Relative Consistency Over Time",
    "Coeficiente de variação móvel (%)": "Rolling Coefficient of Variation (%)",
    "Variabilidade relativa em janelas de 50 solves": "Relative Variability in 50-solve Windows",
    "Coeficiente de variação (%)": "Coefficient of Variation (%)",
    "CV = desvio padrão ÷ média × 100. Um CV menor indica tempos mais consistentes relativamente ao nível médio de velocidade.":
        "CV = standard deviation ÷ mean × 100. A lower CV indicates more consistent times relative to the average speed.",
    "Percentis de Desempenho": "Performance Percentiles",
    "Velocidade vs. consistência relativa ao longo do tempo": "Speed vs. Relative Consistency Over Time",
    "Média dos últimos 50 solves (s)": "Average of Last 50 Solves (s)",
    "Coeficiente de variação dos últimos 50 (%)": "Coefficient of Variation of Last 50 Solves (%)",
    "Percurso cronológico": "Chronological Path",
    "Janela de 50 solves": "50-solve Window",
    "CV dos últimos 50: %{y:.2f}%": "CV of Last 50: %{y:.2f}%",
    "Cada ponto representa uma janela móvel de 50 solves. A cor e a linha ligada indicam a ordem temporal; passe o rato sobre um ponto para ver a data.":
        "Each point represents a rolling window of 50 solves. Color and the connecting line show chronological order; hover over a point to see its date.",
    "O objetivo ideal é aproximar-se do canto inferior esquerdo (mais rápido e mais consistente relativamente à média).":
        "The ideal is to move toward the lower-left corner (faster and more consistent relative to the mean).",
    "São necessárias pelo menos 50 solves válidas no intervalo selecionado.":
        "At least 50 valid solves are required in the selected date range.",
    "Taxa de Solves Sub-X": "Sub-X Solve Rate",
    "Tempo alvo (s)": "Target Time (s)",
    "% Solves abaixo do alvo (Média Móvel 100)": "% of Solves Under Target (100-solve Rolling Average)",
    "Quantidade de Solves por Dia": "Solves per Day",
    "Média 7 dias": "7-day Average",
    "Número de Solves": "Number of Solves",
    "Média móvel de 100": "100-solve Rolling Average",
    "Hora": "Hour",
    "Média acumulada e recorde pessoal acumulado": "Cumulative Mean and Personal Best",
    "Tempo médio dos últimos 50": "Average of Last 50",
    "Últimas 10 − primeiras 10 (s)": "Last 10 − First 10 (s)",
    "Sub-X Rate": "Sub-X Rate",
    "Proporção de Penalizações": "Penalty Breakdown",
    "PB (s)": "PB (s)",
    "PBs": "PBs",
    "Recordes pessoais": "Personal Bests",
    "Média dos últimos 50": "Average of Last 50",
    "Tendência linear": "Linear Trend",
    "Número de solves": "Number of Solves",
    "Desempenho por Hora do Dia": "Performance by Time of Day",
    "Quantidade": "Count",
    "Solves abaixo do alvo": "Solves Under Target",
    "Média móvel (Ao5)": "Moving Average (Ao5)",
    "Média móvel (Ao12)": "Moving Average (Ao12)",
    "Porcentagem": "Percentage",
    "Total": "Total",
    "Evolução mensal da consistência": "Monthly Consistency Trend",
    "Média de solves": "Average Solve Time",
    "Não há solves no intervalo selecionado.": "There are no solves in the selected date range.",
    "Não há tempos válidos para analisar fadiga.": "There are no valid solve times to analyze fatigue.",
    "Não há tempos válidos no intervalo selecionado.": "There are no valid solve times in the selected date range.",
    "São necessárias pelo menos 50 solves válidas no intervalo selecionado.": "At least 50 valid solves are required in the selected date range.",
    "Taxa de Solves Sub-X": "Sub-X Solve Rate",
    "Quantidade de Solves por Dia": "Solves per Day",
    "Data": "Date",
    "Minutos": "Minutes",
    "Duracao": "Duration",
    "Média/PB": "Average/PB",
    "Tempo alvo (s)": "Target Time (s)",
    "Hora do Dia × Dia da Semana": "Hour of Day × Day of Week",
    "Percentis de Desempenho": "Performance Percentiles",
    "Melhoria / piora média": "Average Improvement / Decline",
    "Efeito de Aquecimento": "Warm-up Effect",
    "Efeito de Fadiga": "Fatigue Effect",
    "Tamanho médio das sessões": "Average Session Size",
    "A linha central e os limites de controlo são calculados numa janela móvel de 100 solves.": "The center line and control limits are calculated using a rolling window of 100 solves.",
    "O objetivo ideal é aproximar-se do canto inferior esquerdo (mais rápido e mais consistente relativamente à média).": "The ideal is to move toward the lower-left corner (faster and more consistent relative to the mean).",
    "Uma nova sessão começa após mais de 30 minutos sem solves.": "A new session starts after more than 30 minutes without a solve.",
    "Compara as primeiras 10 com as últimas 10 solves de cada sessão com pelo menos 20 tempos válidos.": "Compares the first 10 and last 10 solves of each session with at least 20 valid times.",
    "Cada sessão é dividida em 10 blocos de progresso; tempos mais altos no final podem indicar fadiga.": "Each session is divided into 10 progress blocks; slower times toward the end may indicate fatigue.",
    "Histórico de Solves e Médias Móveis": "Solve History and Moving Averages",
    "Contagem por Tipo de Penalização": "Count by Penalty Type",
    "Histograma e Distribuição dos Tempos": "Solve Time Histogram and Distribution",
    "Distribuição de Tempos por Hora (Boxplot Interativo)": "Solve Time Distribution by Hour (Interactive Box Plot)",
    "Evolução Mensal da Consistência": "Monthly Consistency Trend",
    "Tamanho, desempenho e duração das sessões": "Session Size, Performance, and Duration",
    "Distribuição das diferenças por sessão": "Distribution of Differences by Session",
    "Tempo médio no início vs. final das sessões": "Average Time at the Start vs. End of Sessions",
    "Tempo médio por bloco de progresso": "Average Time by Progress Block",
    "Heatmap: Hora do Dia × Dia da Semana": "Heatmap: Hour of Day × Day of Week",
    "Média acumulada e recorde pessoal acumulado": "Cumulative Mean and Personal Best",
    "Novos recordes pessoais por mês": "New Personal Bests per Month",
    "Frequência móvel de PBs (janela de 100 solves)": "Rolling PB Frequency (100-solve Window)",
    "Forma atual e nível de desempenho a longo prazo": "Current Form and Long-term Performance",
    "Tempo das solves e limites móveis de controlo": "Solve Times and Rolling Control Limits",
    "Variabilidade relativa em janelas de 50 solves": "Relative Variability in 50-solve Windows",
    "Velocidade vs. consistência relativa ao longo do tempo": "Speed vs. Relative Consistency Over Time",
    "Média dos últimos 50 solves (s)": "Average of Last 50 Solves (s)",
    "Coeficiente de variação dos últimos 50 (%)": "Coefficient of Variation of Last 50 Solves (%)",
    "CV dos últimos 50: %{y:.2f}%": "CV of Last 50: %{y:.2f}%",
    "Percurso cronológico": "Chronological Path",
    "Janela de 50 solves": "50-solve Window",
    "Média móvel (linha central)": "Moving Average (Center Line)",
    "Média 7 dias": "7-day Average",
    "Número de Solves": "Number of Solves",
    "PBs por solve (%)": "PBs per Solve (%)",
    "Mês": "Month",
    "Dia da semana": "Day of Week",
    "Tempo médio (s)": "Average Time (s)",
    "Progresso na sessão": "Session Progress",
    "DNF": "DNF",
    "+1 sigma": "+1 sigma",
    "-1 sigma": "-1 sigma",
    "+2 sigma": "+2 sigma",
    "-2 sigma": "-2 sigma",
}


def t(text: str) -> str:
    """Translate visible dashboard text when English is selected."""
    if st.session_state.get("language", "Português") == "English":
        return TRANSLATIONS.get(text, text)
    return text


def show_chart(figure, **kwargs):
    """Translate chart text while preserving all chart data and styling."""
    if st.session_state.get("language", "Português") == "English":
        def translate(value):
            if isinstance(value, str):
                return TRANSLATIONS.get(value, value)
            if isinstance(value, list):
                return [translate(item) for item in value]
            if isinstance(value, dict):
                return {key: translate(item) for key, item in value.items()}
            return value

        figure = go.Figure(translate(figure.to_dict()))
    st.plotly_chart(figure, **kwargs)


def wca_average(times):

    times = np.sort(np.array(times))

    # 2 DNFs => average DNF
    if np.sum(np.isinf(times)) >= 2:
        return np.inf

    trimmed = times[1:-1]

    # ficou um DNF na média
    if np.isinf(trimmed).any():
        return np.inf

    return np.mean(trimmed)


@st.cache_data(max_entries=10)
def parse_uploaded_solves(
    singles_content: bytes | None,
    averages_content: bytes | None,
    cstimer_content: bytes | None,
) -> tuple[pd.DataFrame, int, int, int]:
    """Parse uploaded timer exports once per distinct file-content combination."""
    singles_data = (
        load_singles(BytesIO(singles_content))
        if singles_content is not None
        else pd.DataFrame(columns=["date", "time", "penalty"])
    )
    averages_data = (
        load_averages(BytesIO(averages_content))
        if averages_content is not None
        else pd.DataFrame(columns=["date", "time", "penalty"])
    )
    cstimer_data = (
        load_cstimer(BytesIO(cstimer_content))
        if cstimer_content is not None
        else pd.DataFrame(columns=["date", "time", "penalty"])
    )
    return (
        combine_solves(combine_solves(singles_data, averages_data), cstimer_data),
        len(singles_data),
        len(averages_data),
        len(cstimer_data),
    )


st.sidebar.selectbox(
    "Idioma / Language",
    ["Português", "English"],
    key="language",
    format_func=lambda language: language,
)
st.title(t("Painel Interativo de Análise de Speedcubing"))

if "upload_widget_version" not in st.session_state:
    st.session_state["upload_widget_version"] = 0

widget_version = st.session_state["upload_widget_version"]
with st.container(border=True):
    st.subheader(t("Importar solves"))
    st.markdown(
        t(
            "Carregue ficheiros do Cubolandia Timer (singles/averages) e/ou uma exportação do CS Timer. "
            "Cada importação acrescenta solves ao histórico atual; use o botão de limpar para começar de novo. "
            "Os scrambles são usados para identificar a mesma solve entre ficheiros; "
            "solves sem scramble são mantidas para evitar falsos duplicados."
        )
    )
    upload_cols = st.columns(3)
    with upload_cols[0]:
        uploaded_singles = st.file_uploader(
            t("Ficheiro de singles (.json)"),
            type=["json"],
            key=f"singles_upload_{widget_version}"
        )
    with upload_cols[1]:
        uploaded_averages = st.file_uploader(
            t("Ficheiro de averages (.json)"),
            type=["json"],
            key=f"averages_upload_{widget_version}"
        )
    with upload_cols[2]:
        uploaded_cstimer = st.file_uploader(
            t("Exportação CS Timer (.txt ou .json)"),
            type=["txt", "json"],
            key=f"cstimer_upload_{widget_version}"
        )

    action_cols = st.columns(2)
    import_clicked = action_cols[0].button(
        t("Importar solves"),
        type="primary",
        key=f"import_solves_{widget_version}"
    )
    clear_clicked = action_cols[1].button(
        t("Limpar dados importados"),
        disabled="solves_df" not in st.session_state,
        key=f"clear_solves_{widget_version}"
    )

if clear_clicked:
    st.session_state.pop("solves_df", None)
    st.session_state.pop("solves_source_summary", None)
    st.session_state.pop("last_import_notice", None)
    st.session_state["upload_widget_version"] += 1
    st.rerun()

if import_clicked:
    if (
        "solves_df" in st.session_state
        and "scramble" not in st.session_state["solves_df"].columns
    ):
        st.warning(
            t(
                "Os dados já carregados não incluem scrambles. Limpa os dados e "
                "importa os ficheiros novamente para usar a nova deteção de duplicados."
            )
        )
    elif (
        uploaded_singles is None
        and uploaded_averages is None
        and uploaded_cstimer is None
    ):
        st.warning(t("Seleciona pelo menos um ficheiro antes de importar."))
    else:
        try:
            imported_data, singles_count, averages_count, cstimer_count = parse_uploaded_solves(
                uploaded_singles.getvalue() if uploaded_singles is not None else None,
                uploaded_averages.getvalue() if uploaded_averages is not None else None,
                uploaded_cstimer.getvalue() if uploaded_cstimer is not None else None,
            )
            if imported_data.empty:
                st.error(t("Os ficheiros selecionados não contêm solves para importar."))
            else:
                if "solves_df" in st.session_state:
                    previous_summary = st.session_state["solves_source_summary"]
                    previous_solve_count = len(st.session_state["solves_df"])
                    combined_data = combine_solves(
                        st.session_state["solves_df"],
                        imported_data
                    )
                    total_singles = previous_summary["singles"] + singles_count
                    total_averages = previous_summary["averages"] + averages_count
                    total_cstimer = previous_summary.get("cstimer", 0) + cstimer_count
                else:
                    previous_solve_count = 0
                    combined_data = imported_data
                    total_singles = singles_count
                    total_averages = averages_count
                    total_cstimer = cstimer_count

                combined_data, duplicates_removed = deduplicate_solves(combined_data)

                st.session_state["solves_df"] = combined_data
                st.session_state["solves_source_summary"] = {
                    "singles": total_singles,
                    "averages": total_averages,
                    "cstimer": total_cstimer,
                }
                st.session_state["last_import_notice"] = (
                    f"{t('Importação concluída: ')}{len(combined_data) - previous_solve_count:,}"
                    f"{t(' solves novas; ')}{duplicates_removed:,}"
                    f"{t(' duplicados removidos (CS Timer: ')}{cstimer_count:,})."
                )
                st.session_state["upload_widget_version"] += 1
                st.rerun()
        except (ValueError, KeyError, TypeError, OSError) as error:
            st.error(f"{t('Não foi possível importar os ficheiros: ')}{error}")

if "solves_df" not in st.session_state:
    st.info(t("O dashboard está vazio. Importa ficheiros do Cubolandia Timer ou CS Timer para começar."))
    st.stop()

df = st.session_state["solves_df"]
source_summary = st.session_state["solves_source_summary"]
if "last_import_notice" in st.session_state:
    st.success(st.session_state.pop("last_import_notice"))
st.caption(
    f"{t('Importadas ')}{source_summary['singles']:,}{t(' solves singles e ')}"
    f"{source_summary['averages']:,}{t(' solves extraídas dos averages; ')}"
    f"{source_summary['cstimer']:,}{t(' solves CS Timer (')}"
    f"{len(df):,}{t(' solves no total).')}"
)

valid_df = df[np.isfinite(df["time"])].copy()
valid_df['rolling_avg_5'] = (
    valid_df['time']
    .rolling(5)
    .apply(wca_average, raw=True)
)
valid_df['rolling_avg_12'] = (
    valid_df['time']
    .rolling(12)
    .apply(wca_average, raw=True)
)

st.markdown(t("Passe o rato sobre os gráficos para ver detalhes, utilize os comandos de zoom e explore o seu histórico de resoluções."))

# Barra lateral para filtros
st.sidebar.header(t("Filtros"))
min_date = df['date'].min().date()
max_date = df['date'].max().date()

date_range = st.sidebar.date_input(
    t("Selecione o intervalo de datas"),
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
    df_filtered = df.loc[mask]
    valid_filtered = valid_df.loc[(valid_df['date'].dt.date >= start_date) & (valid_df['date'].dt.date <= end_date)]
else:
    df_filtered = df
    valid_filtered = valid_df

# 1. Recordes e Médias Móveis (Ao5 e Ao12)
best_ao5 = valid_df['rolling_avg_5'].min() if not valid_df['rolling_avg_5'].empty else np.nan
best_ao12 = valid_df['rolling_avg_12'].min() if not valid_df['rolling_avg_12'].empty else np.nan

# 2. Taxas de Sucesso e Penalizações
total_solves = len(df_filtered)
clean_solves = len(df_filtered[df_filtered['penalty'] == 0])
dnf_solves = len(df_filtered[df_filtered['penalty'] == 2])

clean_rate = (clean_solves / total_solves * 100) if total_solves > 0 else 0.0
dnf_rate = (dnf_solves / total_solves * 100) if total_solves > 0 else 0.0

# 3. Consistência de Prática (Streak Máxima em dias)
if not df_filtered.empty:
    unique_dates = df_filtered['date'].dt.date.sort_values().unique()
    streak = 0
    max_streak = 0
    if len(unique_dates) > 0:
        streak = 1
        max_streak = 1
        for i in range(1, len(unique_dates)):
            if (unique_dates[i] - unique_dates[i - 1]).days == 1:
                streak += 1
            elif (unique_dates[i] - unique_dates[i - 1]).days > 1:
                streak = 1
            max_streak = max(max_streak, streak)
else:
    max_streak = 0

# --- PAINEL DE MÉTRICAS RÁPIDAS NO TOPO ---
st.subheader(t("📊 Visão Geral e Indicadores de Desempenho"))

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("Total de Solves"), total_solves)
col2.metric(t("Tempo Médio"), f"{valid_filtered['time'].mean():.2f}s" if not valid_filtered.empty else "N/A")
col3.metric(t("Melhor Tempo (PB)"), f"{valid_filtered['time'].min():.2f}s" if not valid_filtered.empty else "N/A")
col4.metric(t("Melhor Ao5"), f"{best_ao5:.2f}s" if not np.isnan(best_ao5) else "N/A")

col5, col6, col7, col8 = st.columns(4)
col5.metric(t("Melhor Ao12"), f"{best_ao12:.2f}s" if not np.isnan(best_ao12) else "N/A")
col6.metric(t("Taxa de Limpeza"), f"{clean_rate:.1f}%")
col7.metric(t("Taxa de DNF"), f"{dnf_rate:.1f}%")
col8.metric(t("Streak Máxima"), f"{max_streak} {t('dias')}")

st.markdown("---")

analysis_groups = {
    "Desempenho e recordes": [
        "1. Evolução Temporal",
        "2. Distribuição",
        "6. PB Progression",
        "16. Média Global",
        "17. Frequência de PB",
        "18. Probabilidade de PB",
        "19. Ao100 / Ao1000",
    ],
    "Consistência": [
        "5. Consistência Mensal",
        "7. Consistência",
        "8. Percentis",
        "9. Velocidade vs Consistência",
        "13. Aquecimento",
        "14. Fadiga",
        "20. Control Chart",
    ],
    "Treino e sessões": [
        "10. Sub-X Rate",
        "11. Solves por Dia",
        "12. Sessões",
    ],
    "Penalizações e horários": [
        "3. Penalizações",
        "4. Hora do Dia",
        "15. Hora × Dia",
    ],
}

analysis_categories = list(analysis_groups)
category_tabs = st.tabs(
    [t(category) for category in analysis_categories],
    key="analysis_category_tabs",
    on_change="rerun"
)
analysis_selections = {}
for category_name, category_tab in zip(analysis_categories, category_tabs):
    with category_tab:
        analysis_selections[category_name] = st.selectbox(
            t("Gráfico"),
            analysis_groups[category_name],
            format_func=lambda analysis: t(analysis.split(". ", 1)[1]),
            key=f"analysis_{category_name}"
        )

active_category = next(
    (
        category_name
        for category_name, category_tab in zip(analysis_categories, category_tabs)
        if category_tab.open
    ),
    analysis_categories[0]
)
selected_analysis = analysis_selections[active_category]

st.markdown("---")

if selected_analysis == "1. Evolução Temporal":
    st.subheader(t("Evolução Temporal e Médias Móveis (Ao5 / Ao12)"))
    st.markdown(t("Dica: Pode selecionar uma área para fazer zoom ou clicar nas legendas para ocultar/mostrar séries."))

    # Converter penalização para texto categórico para evitar a barra de cores contínua
    valid_filtered['penalty_str'] = valid_filtered['penalty'].map({0: 'Limpo (0)', 1: '+2 Segundos', 2: 'DNF'})

    fig1 = px.scatter(
        valid_filtered, x='date', y='time',
        color='penalty_str',
        labels={'date': 'Data', 'time': 'Tempo (s)', 'penalty_str': 'Penalização'},
        opacity=0.6,
        title="Histórico de Solves e Médias Móveis"
    )
    fig1.add_trace(
        go.Scatter(x=valid_filtered['date'], y=valid_filtered['rolling_avg_5'], mode='lines', name='Média Móvel (Ao5)',
                   line=dict(color='blue', width=1.5)))
    fig1.add_trace(go.Scatter(x=valid_filtered['date'], y=valid_filtered['rolling_avg_12'], mode='lines',
                              name='Média Móvel (Ao12)', line=dict(color='orange', width=2.5)))

    fig1.update_layout(
        height=580,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    show_chart(fig1, use_container_width=True)

if selected_analysis == "2. Distribuição":
    st.subheader(t("Distribuição de Frequência dos Tempos"))
    fig2 = px.histogram(
        valid_filtered, x='time', nbins=40,
        marginal="box",
        labels={'time': 'Tempo (s)', 'count': 'Frequência'},
        title="Histograma e Distribuição dos Tempos"
    )
    fig2.update_layout(height=550, template="plotly_white")
    show_chart(fig2, use_container_width=True)

if selected_analysis == "3. Penalizações":
    st.subheader(t("Proporção de Penalizações"))
    penalty_map = {0: t('Limpo (0)'), 1: t('+2 Segundos'), 2: t('DNF (Não Concluído)')}
    df_filtered_copy = df_filtered.copy()
    df_filtered_copy['penalty_label'] = df_filtered_copy['penalty'].map(penalty_map)
    penalty_counts = df_filtered_copy['penalty_label'].value_counts().reset_index()
    penalty_counts.columns = ['Tipo', 'Quantidade']

    fig3 = px.bar(
        penalty_counts, x='Tipo', y='Quantidade',
        text='Quantidade', color='Tipo',
        title="Contagem por Tipo de Penalização"
    )
    fig3.update_traces(textposition='outside')
    fig3.update_layout(height=550, template="plotly_white", showlegend=False)
    show_chart(fig3, use_container_width=True)

if selected_analysis == "4. Hora do Dia":
    st.subheader(t("Desempenho por Hora do Dia"))
    valid_filtered_copy = valid_filtered.copy()
    valid_filtered_copy['hour'] = valid_filtered_copy['date'].dt.hour

    fig4 = px.box(
        valid_filtered_copy, x='hour', y='time',
        labels={'hour': 'Hora do Dia', 'time': 'Tempo (s)'},
        title="Distribuição de Tempos por Hora (Boxplot Interativo)"
    )
    fig4.update_layout(height=550, template="plotly_white")
    show_chart(fig4, use_container_width=True)

if selected_analysis == "5. Consistência Mensal":
    st.subheader(t("Consistência dos Tempos por Mês"))
    valid_filtered_copy = valid_filtered.copy()
    valid_filtered_copy['year_month'] = valid_filtered_copy['date'].dt.to_period('M').astype(str)

    fig5 = px.box(
        valid_filtered_copy, x='year_month', y='time',
        labels={'year_month': 'Mês', 'time': 'Tempo (s)'},
        title="Evolução Mensal da Consistência"
    )
    fig5.update_layout(height=550, template="plotly_white", xaxis={'categoryorder': 'category ascending'})
    show_chart(fig5, use_container_width=True)

if selected_analysis == "6. PB Progression":

    st.subheader(t("Progressão do Recorde Pessoal"))

    pb_df = valid_filtered.copy()

    pb_df["pb"] = pb_df["time"].cummin()

    fig = px.line(
        pb_df,
        x="date",
        y="pb",
        labels={
            "pb": "PB (s)",
            "date": "Data"
        }
    )

    fig.update_layout(
        height=550,
        template="plotly_white"
    )

    show_chart(
        fig,
        use_container_width=True
    )

if selected_analysis == "12. Sessões":
    st.subheader(t("Análise das Sessões de Treino"))
    st.markdown(t("Uma nova sessão começa após mais de 30 minutos sem solves."))

    session_source = df_filtered.sort_values("date").copy()
    if not session_source.empty:
        session_source["session_id"] = (
            session_source["date"].diff().gt(pd.Timedelta(minutes=30)).cumsum() + 1
        )
        session_times = session_source[np.isfinite(session_source["time"])]

        session_summary = (
            session_source.groupby("session_id")
            .agg(
                inicio=("date", "min"),
                fim=("date", "max"),
                solves=("time", "size")
            )
        )
        session_summary["duração (min)"] = (
            session_summary["fim"] - session_summary["inicio"]
        ).dt.total_seconds() / 60

        if not session_times.empty:
            time_stats = session_times.groupby("session_id")["time"].agg(
                **{"tempo médio (s)": "mean", "melhor solve (s)": "min", "desvio padrão (s)": "std"}
            )
            session_summary = session_summary.join(time_stats)
        else:
            session_summary[["tempo médio (s)", "melhor solve (s)", "desvio padrão (s)"]] = np.nan

        session_summary = session_summary.reset_index()
        session_summary["sessão"] = session_summary["session_id"]
        session_table = session_summary[
            ["sessão", "inicio", "fim", "solves", "duração (min)",
             "tempo médio (s)", "melhor solve (s)", "desvio padrão (s)"]
        ].copy()
        session_table["duração (min)"] = session_table["duração (min)"].round(1)
        session_table[["tempo médio (s)", "melhor solve (s)", "desvio padrão (s)"]] = (
            session_table[["tempo médio (s)", "melhor solve (s)", "desvio padrão (s)"]].round(2)
        )
        display_session_table = session_table.rename(columns={column: t(column) for column in session_table.columns})
        st.dataframe(display_session_table, hide_index=True, use_container_width=True)

        metric_cols = st.columns(3)
        best_session = session_summary.loc[session_summary["tempo médio (s)"].idxmin()] if session_summary["tempo médio (s)"].notna().any() else None
        longest_session = session_summary.loc[session_summary["duração (min)"].idxmax()]
        metric_cols[0].metric(
            t("Melhor sessão (média)"),
            f"{best_session['tempo médio (s)']:.2f}s" if best_session is not None else "N/A"
        )
        metric_cols[1].metric(t("Sessão mais longa"), f"{longest_session['duração (min)']:.1f} {t('min')}")
        metric_cols[2].metric(t("Tamanho médio das sessões"), f"{session_summary['solves'].mean():.1f} {t('solves')}")

        scatter_df = session_summary.dropna(subset=["tempo médio (s)"])
        if not scatter_df.empty:
            fig12 = px.scatter(
                scatter_df,
                x="solves",
                y="tempo médio (s)",
                color="duração (min)",
                hover_data=["sessão", "melhor solve (s)", "desvio padrão (s)"],
                labels={
                    "solves": "Número de solves",
                    "tempo médio (s)": "Tempo médio (s)",
                    "duração (min)": "Duração (min)"
                },
                title="Tamanho, desempenho e duração das sessões"
            )
            fig12.update_layout(height=550, template="plotly_white")
            show_chart(fig12, use_container_width=True)
    else:
        st.info(t("Não há solves no intervalo selecionado."))

if selected_analysis == "13. Aquecimento":
    st.subheader(t("Efeito de Aquecimento"))
    st.markdown(t("Compara as primeiras 10 com as últimas 10 solves de cada sessão com pelo menos 20 tempos válidos."))

    warmup_rows = []
    if not df_filtered.empty:
        warmup_source = df_filtered.sort_values("date").copy()
        warmup_source["session_id"] = (
            warmup_source["date"].diff().gt(pd.Timedelta(minutes=30)).cumsum() + 1
        )
        warmup_times = warmup_source[np.isfinite(warmup_source["time"])]
        for session_id, group in warmup_times.groupby("session_id", sort=True):
            if len(group) >= 20:
                first_mean = group["time"].iloc[:10].mean()
                last_mean = group["time"].iloc[-10:].mean()
                warmup_rows.append({
                    "sessão": session_id,
                    "primeiras 10 (s)": first_mean,
                    "últimas 10 (s)": last_mean,
                    "diferença (s)": last_mean - first_mean
                })

    warmup_summary = pd.DataFrame(warmup_rows)
    if not warmup_summary.empty:
        improvement_cols = st.columns(2)
        improvement_cols[0].metric(t("Melhoria / piora média"), f"{warmup_summary['diferença (s)'].mean():+.2f}s")
        improvement_cols[1].metric(
            t("Sessões com melhoria"),
            f"{(warmup_summary['diferença (s)'] < 0).mean() * 100:.1f}%"
        )

        fig13_hist = px.histogram(
            warmup_summary,
            x="diferença (s)",
            nbins=30,
            labels={"diferença (s)": "Últimas 10 − primeiras 10 (s)"},
            title="Distribuição das diferenças por sessão"
        )
        fig13_hist.add_vline(x=0, line_dash="dash", line_color="red")
        fig13_hist.update_layout(height=450, template="plotly_white")
        show_chart(fig13_hist, use_container_width=True)

        warmup_means = pd.DataFrame({
            "Grupo": ["Primeiras 10 solves", "Últimas 10 solves"],
            "Tempo médio (s)": [
                warmup_summary["primeiras 10 (s)"].mean(),
                warmup_summary["últimas 10 (s)"].mean()
            ]
        })
        fig13_bar = px.bar(
            warmup_means,
            x="Grupo",
            y="Tempo médio (s)",
            text_auto=".2f",
            title="Tempo médio no início vs. final das sessões"
        )
        fig13_bar.update_layout(height=450, template="plotly_white", showlegend=False)
        show_chart(fig13_bar, use_container_width=True)
    else:
        st.info(t("Não existem sessões com pelo menos 20 solves de tempo válido no intervalo selecionado."))

if selected_analysis == "14. Fadiga":
    st.subheader(t("Efeito de Fadiga"))
    st.markdown(t("Cada sessão é dividida em 10 blocos de progresso; tempos mais altos no final podem indicar fadiga."))

    fatigue_source = df_filtered.sort_values("date").copy()
    if not fatigue_source.empty:
        fatigue_source["session_id"] = (
            fatigue_source["date"].diff().gt(pd.Timedelta(minutes=30)).cumsum() + 1
        )
        fatigue_source = fatigue_source[np.isfinite(fatigue_source["time"])].copy()
        if not fatigue_source.empty:
            fatigue_source["position"] = fatigue_source.groupby("session_id").cumcount()
            session_sizes = fatigue_source.groupby("session_id")["time"].transform("size")
            normalized_position = fatigue_source["position"] / (session_sizes - 1).replace(0, 1)
            fatigue_source["bloco"] = np.minimum((normalized_position * 10).astype(int), 9)
            fatigue_summary = (
                fatigue_source.groupby("bloco", as_index=False)["time"]
                .mean()
                .set_index("bloco")
                .reindex(range(10))
                .rename_axis("bloco")
                .reset_index()
            )
            fatigue_summary["progresso"] = [f"{i * 10}-{(i + 1) * 10}%" for i in range(10)]
            fig14 = px.line(
                fatigue_summary,
                x="progresso",
                y="time",
                markers=True,
                labels={"progresso": "Progresso na sessão", "time": "Tempo médio (s)"},
                title="Tempo médio por bloco de progresso"
            )
            fig14.update_layout(height=550, template="plotly_white")
            show_chart(fig14, use_container_width=True)
        else:
            st.info(t("Não há tempos válidos para analisar fadiga."))
    else:
        st.info(t("Não há solves no intervalo selecionado."))

if selected_analysis == "15. Hora × Dia":
    st.subheader(t("Heatmap: Hora do Dia × Dia da Semana"))
    heatmap_source = valid_filtered.copy()
    weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    displayed_weekdays = [t(day) for day in weekdays]
    if not heatmap_source.empty:
        heatmap_source["dia_semana"] = pd.Categorical(
            heatmap_source["date"].dt.dayofweek.map(dict(enumerate(weekdays))),
            categories=weekdays,
            ordered=True
        )
        heatmap_source["hora"] = heatmap_source["date"].dt.hour
        mean_grid = (
            heatmap_source.pivot_table(
                index="dia_semana", columns="hora", values="time", observed=False
            ).reindex(index=weekdays, columns=range(24))
        )
        count_grid = (
            heatmap_source.pivot_table(
                index="dia_semana", columns="hora", values="time",
                aggfunc="count", observed=False
            ).reindex(index=weekdays, columns=range(24), fill_value=0)
        )
        heat_cols = st.columns(2)
        with heat_cols[0]:
            fig15_mean = px.imshow(
                mean_grid,
                x=list(range(24)),
                y=displayed_weekdays,
                aspect="auto",
                color_continuous_scale="Viridis",
                labels={"x": "Hora", "y": "Dia da semana", "color": "Tempo médio (s)"},
                title="Tempo médio (s)"
            )
            fig15_mean.update_layout(height=500, template="plotly_white")
            show_chart(fig15_mean, use_container_width=True)
        with heat_cols[1]:
            fig15_count = px.imshow(
                count_grid,
                x=list(range(24)),
                y=displayed_weekdays,
                aspect="auto",
                color_continuous_scale="Blues",
                labels={"x": "Hora", "y": "Dia da semana", "color": "Número de solves"},
                title="Número de solves"
            )
            fig15_count.update_layout(height=500, template="plotly_white")
            show_chart(fig15_count, use_container_width=True)
    else:
        st.info(t("Não há tempos válidos no intervalo selecionado."))

if selected_analysis == "16. Média Global":
    st.subheader(t("Evolução da Média Global"))
    if not valid_filtered.empty:
        global_progress = valid_filtered[["date", "time"]].copy()
        global_progress["média acumulada"] = global_progress["time"].expanding().mean()
        global_progress["PB acumulado"] = global_progress["time"].cummin()

        fig16 = go.Figure()
        fig16.add_trace(go.Scatter(
            x=global_progress["date"], y=global_progress["média acumulada"],
            mode="lines", name="Média acumulada"
        ))
        fig16.add_trace(go.Scatter(
            x=global_progress["date"], y=global_progress["PB acumulado"],
            mode="lines", name="PB acumulado"
        ))
        fig16.update_layout(
            height=550,
            template="plotly_white",
            xaxis_title="Data",
            yaxis_title="Tempo (s)",
            title="Média acumulada e recorde pessoal acumulado"
        )
        show_chart(fig16, use_container_width=True)
    else:
        st.info(t("Não há tempos válidos no intervalo selecionado."))

if selected_analysis == "17. Frequência de PB":
    st.subheader(t("Frequência de PB"))
    if not valid_filtered.empty:
        pb_frequency = valid_filtered[["date", "time"]].copy()
        pb_frequency["é_pb"] = pb_frequency["time"] < pb_frequency["time"].cummin().shift(1)
        pb_events = pb_frequency[pb_frequency["é_pb"]].copy()
        pb_frequency_cols = st.columns(3)
        pb_frequency_cols[0].metric(t("Total de PBs"), len(pb_events))
        pb_frequency_cols[1].metric(
            t("Último PB"),
            f"{pb_events.iloc[-1]['time']:.2f}s" if not pb_events.empty else "N/A",
            delta_description=(
                pb_events.iloc[-1]["date"].strftime("%d/%m/%Y")
                if not pb_events.empty else t("Nenhum PB no intervalo")
            )
        )
        days_between = pb_events["date"].diff().dt.total_seconds().div(86400).dropna()
        pb_frequency_cols[2].metric(
            t("Média de dias entre PBs"),
            f"{days_between.mean():.1f}" if not days_between.empty else "N/A"
        )

        if not pb_events.empty:
            pb_events["mês"] = pb_events["date"].dt.to_period("M").astype(str)
            monthly_pbs = pb_events.groupby("mês").size().rename("PBs").reset_index()
        else:
            monthly_pbs = pd.DataFrame(columns=["mês", "PBs"])
        fig17 = px.bar(
            monthly_pbs,
            x="mês",
            y="PBs",
            text="PBs",
            labels={"mês": "Mês", "PBs": "Quantidade de PBs"},
            title="Novos recordes pessoais por mês"
        )
        fig17.update_layout(height=500, template="plotly_white")
        show_chart(fig17, use_container_width=True)
    else:
        st.info(t("Não há tempos válidos no intervalo selecionado."))

if selected_analysis == "18. Probabilidade de PB":
    st.subheader(t("Probabilidade Histórica de PB"))
    if not valid_filtered.empty:
        pb_probability = valid_filtered[["date", "time"]].copy()
        pb_probability["é_pb"] = pb_probability["time"] < pb_probability["time"].cummin().shift(1)
        probability_cols = st.columns(3)
        for col, window in zip(probability_cols, [100, 500, 1000]):
            recent_solves = pb_probability.tail(window)
            probability = recent_solves["é_pb"].mean() * 100
            col.metric(
                f"{t('Últimas ')}{window} {t('solves')}",
                f"{probability:.2f}%",
                delta_description=f"{int(recent_solves['é_pb'].sum())}{t(' PBs em ')}{len(recent_solves)} {t('solves')}"
            )

        pb_probability["probabilidade móvel (%)"] = (
            pb_probability["é_pb"].rolling(100, min_periods=1).mean() * 100
        )
        fig18 = px.line(
            pb_probability,
            x="date",
            y="probabilidade móvel (%)",
            labels={"date": "Data", "probabilidade móvel (%)": "PBs por solve (%)"},
            title="Frequência móvel de PBs (janela de 100 solves)"
        )
        fig18.update_layout(height=500, template="plotly_white", yaxis=dict(rangemode="tozero"))
        show_chart(fig18, use_container_width=True)
        st.caption(t("A estimativa usa apenas solves anteriores dentro do intervalo de datas selecionado."))
    else:
        st.info(t("Não há tempos válidos no intervalo selecionado."))

if selected_analysis == "19. Ao100 / Ao1000":
    st.subheader(t("Médias Móveis Ao5, Ao12, Ao100 e Ao1000"))
    if not valid_filtered.empty:
        average_progress = valid_filtered[["date", "time"]].copy()
        average_progress["Ao5"] = valid_filtered["rolling_avg_5"]
        average_progress["Ao12"] = valid_filtered["rolling_avg_12"]
        average_progress["Ao100"] = average_progress["time"].rolling(100).mean()
        average_progress["Ao1000"] = average_progress["time"].rolling(1000).mean()
        fig19 = go.Figure()
        for average_name in ["Ao5", "Ao12", "Ao100", "Ao1000"]:
            fig19.add_trace(go.Scatter(
                x=average_progress["date"],
                y=average_progress[average_name],
                mode="lines",
                name=average_name
            ))
        fig19.update_layout(
            height=550,
            template="plotly_white",
            xaxis_title="Data",
            yaxis_title="Tempo médio (s)",
            title="Forma atual e nível de desempenho a longo prazo"
        )
        show_chart(fig19, use_container_width=True)
    else:
        st.info(t("Não há tempos válidos no intervalo selecionado."))

if selected_analysis == "20. Control Chart":
    st.subheader(t("Control Chart"))
    st.markdown(t("A linha central e os limites de controlo são calculados numa janela móvel de 100 solves."))
    if not valid_filtered.empty:
        control_chart = valid_filtered[["date", "time"]].copy()
        control_chart["rolling_mean"] = control_chart["time"].rolling(100).mean()
        control_chart["rolling_std"] = control_chart["time"].rolling(100).std()
        fig20 = go.Figure()
        fig20.add_trace(go.Scatter(
            x=control_chart["date"], y=control_chart["time"],
            mode="lines", name="Solve", line=dict(color="lightgray", width=1)
        ))
        fig20.add_trace(go.Scatter(
            x=control_chart["date"], y=control_chart["rolling_mean"],
            mode="lines", name="Média móvel (linha central)", line=dict(color="blue", width=2)
        ))
        for sigma, color in [(1, "orange"), (2, "red")]:
            fig20.add_trace(go.Scatter(
                x=control_chart["date"],
                y=control_chart["rolling_mean"] + sigma * control_chart["rolling_std"],
                mode="lines",
                name=f"+{sigma} sigma",
                line=dict(color=color, dash="dash")
            ))
            fig20.add_trace(go.Scatter(
                x=control_chart["date"],
                y=control_chart["rolling_mean"] - sigma * control_chart["rolling_std"],
                mode="lines",
                name=f"-{sigma} sigma",
                line=dict(color=color, dash="dash")
            ))
        fig20.update_layout(
            height=600,
            template="plotly_white",
            xaxis_title="Data",
            yaxis_title="Tempo (s)",
            title="Tempo das solves e limites móveis de controlo"
        )
        show_chart(fig20, use_container_width=True)
    else:
        st.info(t("Não há tempos válidos no intervalo selecionado."))

if selected_analysis == "7. Consistência":

    st.subheader(t("Consistência Relativa ao Longo do Tempo"))

    consistency_df = valid_filtered.copy()

    rolling_mean = consistency_df["time"].rolling(50).mean()
    rolling_std = consistency_df["time"].rolling(50).std()
    consistency_df["cv50"] = (
        rolling_std.div(rolling_mean.where(rolling_mean > 0)) * 100
    )

    fig = px.line(
        consistency_df,
        x="date", y="cv50",
        labels={
            "cv50": "Coeficiente de variação móvel (%)",
            "date": "Data",
        },
        title="Variabilidade relativa em janelas de 50 solves"
    )

    fig.update_layout(
        height=550,
        template="plotly_white",
        yaxis_title="Coeficiente de variação (%)"
    )

    show_chart(
        fig,
        use_container_width=True
    )
    st.caption(
        t(
            "CV = desvio padrão ÷ média × 100. Um CV menor indica tempos mais "
            "consistentes relativamente ao nível médio de velocidade."
        )
    )

if selected_analysis == "8. Percentis":

    st.subheader(t("Percentis de Desempenho"))

    p_df = valid_filtered.copy()

    p_df["P10"] = (
        p_df["time"]
        .rolling(100)
        .quantile(0.10)
    )

    p_df["P50"] = (
        p_df["time"]
        .rolling(100)
        .quantile(0.50)
    )

    p_df["P90"] = (
        p_df["time"]
        .rolling(100)
        .quantile(0.90)
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=p_df["date"],
            y=p_df["P10"],
            name="P10"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=p_df["date"],
            y=p_df["P50"],
            name="P50"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=p_df["date"],
            y=p_df["P90"],
            name="P90"
        )
    )

    fig.update_layout(
        height=550,
        template="plotly_white"
    )

    show_chart(
        fig,
        use_container_width=True
    )

if selected_analysis == "9. Velocidade vs Consistência":

    st.subheader(t("Velocidade vs Consistência"))

    vc_df = valid_filtered.copy()

    vc_df["AO50"] = (
        vc_df["time"]
        .rolling(50)
        .mean()
    )

    rolling_std50 = (
        vc_df["time"]
        .rolling(50)
        .std()
    )
    vc_df["CV50"] = rolling_std50.div(vc_df["AO50"].where(vc_df["AO50"] > 0)) * 100

    vc_df = vc_df.dropna()
    if vc_df.empty:
        st.info(t("São necessárias pelo menos 50 solves válidas no intervalo selecionado."))
    else:
        vc_df["data_ord"] = vc_df["date"].astype("int64") / 1_000_000_000
        vc_df["data_label"] = vc_df["date"].dt.strftime("%d/%m/%Y %H:%M")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=vc_df["AO50"],
            y=vc_df["CV50"],
            mode="lines",
            name="Percurso cronológico",
            line=dict(color="lightgray", width=1.5),
            hoverinfo="skip"
        ))
        fig.add_trace(go.Scatter(
            x=vc_df["AO50"],
            y=vc_df["CV50"],
            mode="markers",
            name="Janela de 50 solves",
            customdata=vc_df[["data_label"]],
            marker=dict(
                size=8,
                color=vc_df["data_ord"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Data"),
                symbol="circle"
            ),
            hovertemplate=(
                "Data: %{customdata[0]}<br>"
                "Média dos últimos 50: %{x:.2f}s<br>"
                "CV dos últimos 50: %{y:.2f}%<extra></extra>"
            )
        ))

        if len(vc_df) > 1 and vc_df["AO50"].nunique() > 1:
            slope, intercept = np.polyfit(vc_df["AO50"], vc_df["CV50"], 1)
            x_trend = np.linspace(vc_df["AO50"].min(), vc_df["AO50"].max(), 100)
            fig.add_trace(go.Scatter(
                x=x_trend,
                y=slope * x_trend + intercept,
                mode="lines",
                name="Tendência linear",
                line=dict(color="red", dash="dash")
            ))

        month_ticks = pd.date_range(
            vc_df["date"].min().normalize(),
            vc_df["date"].max().normalize(),
            freq="MS"
        )
        colorbar_ticks = month_ticks.astype("int64") / 1_000_000_000
        if not len(month_ticks):
            month_ticks = pd.DatetimeIndex([vc_df["date"].min(), vc_df["date"].max()]).drop_duplicates()
            colorbar_ticks = month_ticks.astype("int64") / 1_000_000_000
        fig.update_traces(
            selector=dict(name="Janela de 50 solves"),
            marker_colorbar=dict(
                title="Data",
                tickmode="array",
                tickvals=colorbar_ticks,
                ticktext=month_ticks.strftime("%b %Y")
            )
        )
        fig.update_layout(
            title="Velocidade vs. consistência relativa ao longo do tempo",
            xaxis_title="Média dos últimos 50 solves (s)",
            yaxis_title="Coeficiente de variação dos últimos 50 (%)"
        )

    fig.update_layout(
        height=550,
        template="plotly_white"
    )

    if not vc_df.empty:
        show_chart(fig, use_container_width=True)
        st.caption(
            t(
                "Cada ponto representa uma janela móvel de 50 solves. A cor e a linha "
                "ligada indicam a ordem temporal; passe o rato sobre um ponto para ver a data."
            )
        )

    st.info(
        t(
            "O objetivo ideal é aproximar-se do canto inferior esquerdo "
            "(mais rápido e mais consistente relativamente à média)."
        )
    )

if selected_analysis == "10. Sub-X Rate":

    st.subheader(t("Taxa de Solves Sub-X"))

    threshold = st.slider(
        t("Tempo alvo (s)"),
        min_value=10,
        max_value=60,
        value=20
    )

    sub_df = valid_filtered.copy()

    sub_df["sub"] = (
        sub_df["time"] <= threshold
    ).astype(int)

    # Correção: Calcular a média móvel e multiplicar por 100 para transformar em percentagem (%)
    sub_df["sub_rate"] = (
        sub_df["sub"]
        .rolling(100)
        .mean() * 100
    )

    fig = px.line(
        sub_df,
        x="date",
        y="sub_rate",
        labels={
            "sub_rate": "% Solves abaixo do alvo (Média Móvel 100)",
            "date": "Data"
        }
    )

    fig.update_layout(
        height=550,
        template="plotly_white",
        yaxis=dict(range=[0, 105]) # Fixar o eixo Y entre 0% e 105% para melhor visualização
    )

    show_chart(
        fig,
        use_container_width=True
    )

if selected_analysis == "11. Solves por Dia":

    st.subheader(t("Quantidade de Solves por Dia"))

    daily_solves = (
        df_filtered
        .groupby(df_filtered["date"].dt.date)
        .size()
        .reset_index(name="count")
    )

    daily_solves["rolling7"] = (
        daily_solves["count"]
        .rolling(7)
        .mean()
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=daily_solves["date"],
            y=daily_solves["count"],
            name=t("Solves")
        )
    )

    fig.add_trace(
        go.Scatter(
            x=daily_solves["date"],
            y=daily_solves["rolling7"],
            mode="lines",
            name=t("Média 7 dias"),
            line=dict(color="red", width=3)
        )
    )

    fig.update_layout(
        height=550,
        template="plotly_white",
        xaxis_title="Data",
        yaxis_title="Número de Solves"
    )

    show_chart(
        fig,
        use_container_width=True
    )
