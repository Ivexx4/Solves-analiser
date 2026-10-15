from io import BytesIO

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from carregamento_dados import (
    combine_solves,
    load_averages,
    load_cstimer,
    load_singles,
)

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Dashboard Interativo de Speedcubing",
    page_icon="🧩",
    layout="wide"
)

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


st.title("🧩 Painel Interativo de Análise de Speedcubing")

if "upload_widget_version" not in st.session_state:
    st.session_state["upload_widget_version"] = 0

widget_version = st.session_state["upload_widget_version"]
with st.container(border=True):
    st.subheader("Importar solves do Cubolandia Timer")
    st.markdown(
        "Carregue ficheiros do Cubolandia Timer (singles/averages) e/ou uma "
        "exportação do CS Timer. "
        "Cada importação acrescenta solves ao histórico atual; use o botão de limpar "
        "para começar de novo."
    )
    upload_cols = st.columns(3)
    with upload_cols[0]:
        uploaded_singles = st.file_uploader(
            "Ficheiro de singles (.json)",
            type=["json"],
            key=f"singles_upload_{widget_version}"
        )
    with upload_cols[1]:
        uploaded_averages = st.file_uploader(
            "Ficheiro de averages (.json)",
            type=["json"],
            key=f"averages_upload_{widget_version}"
        )
    with upload_cols[2]:
        uploaded_cstimer = st.file_uploader(
            "Exportação CS Timer (.txt ou .json)",
            type=["txt", "json"],
            key=f"cstimer_upload_{widget_version}"
        )

    action_cols = st.columns(2)
    import_clicked = action_cols[0].button(
        "Importar solves",
        type="primary",
        key=f"import_solves_{widget_version}"
    )
    clear_clicked = action_cols[1].button(
        "Limpar dados importados",
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
        uploaded_singles is None
        and uploaded_averages is None
        and uploaded_cstimer is None
    ):
        st.warning("Seleciona pelo menos um ficheiro JSON antes de importar.")
    else:
        try:
            imported_data, singles_count, averages_count, cstimer_count = parse_uploaded_solves(
                uploaded_singles.getvalue() if uploaded_singles is not None else None,
                uploaded_averages.getvalue() if uploaded_averages is not None else None,
                uploaded_cstimer.getvalue() if uploaded_cstimer is not None else None,
            )
            if imported_data.empty:
                st.error("Os ficheiros selecionados não contêm solves para importar.")
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

                rows_before_deduplication = len(combined_data)
                combined_data = (
                    combined_data
                    .drop_duplicates(subset=["date", "time", "penalty"], keep="first")
                    .sort_values("date", kind="stable")
                    .reset_index(drop=True)
                )
                duplicates_removed = rows_before_deduplication - len(combined_data)

                st.session_state["solves_df"] = combined_data
                st.session_state["solves_source_summary"] = {
                    "singles": total_singles,
                    "averages": total_averages,
                    "cstimer": total_cstimer,
                }
                st.session_state["last_import_notice"] = (
                    f"Importação concluída: {len(combined_data) - previous_solve_count:,} "
                    f"solves novas; {duplicates_removed:,} duplicados removidos "
                    f"(CS Timer: {cstimer_count:,})."
                )
                st.session_state["upload_widget_version"] += 1
                st.rerun()
        except (ValueError, KeyError, TypeError, OSError) as error:
            st.error(f"Não foi possível importar os ficheiros: {error}")

if "solves_df" not in st.session_state:
    st.info("O dashboard está vazio. Importa os ficheiros do Cubolandia Timer para começar.")
    st.stop()

df = st.session_state["solves_df"]
source_summary = st.session_state["solves_source_summary"]
if "last_import_notice" in st.session_state:
    st.success(st.session_state.pop("last_import_notice"))
st.caption(
    f"Importadas {source_summary['singles']:,} solves singles e "
    f"{source_summary['averages']:,} solves extraídas dos averages; "
    f"{source_summary['cstimer']:,} solves CS Timer "
    f"({len(df):,} solves no total)."
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

st.markdown("Passe o rato sobre os gráficos para ver detalhes, utilize os comandos de zoom e explore o seu histórico de resoluções.")

# Barra lateral para filtros
st.sidebar.header("Filtros")
min_date = df['date'].min().date()
max_date = df['date'].max().date()

date_range = st.sidebar.date_input(
    "Selecione o intervalo de datas",
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
st.subheader("📊 Visão Geral e Indicadores de Desempenho")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Solves", total_solves)
col2.metric("Tempo Médio", f"{valid_filtered['time'].mean():.2f}s" if not valid_filtered.empty else "N/A")
col3.metric("Melhor Tempo (PB)", f"{valid_filtered['time'].min():.2f}s" if not valid_filtered.empty else "N/A")
col4.metric("Melhor Ao5", f"{best_ao5:.2f}s" if not np.isnan(best_ao5) else "N/A")

col5, col6, col7, col8 = st.columns(4)
col5.metric("Melhor Ao12", f"{best_ao12:.2f}s" if not np.isnan(best_ao12) else "N/A")
col6.metric("Taxa de Limpeza", f"{clean_rate:.1f}%")
col7.metric("Taxa de DNF", f"{dnf_rate:.1f}%")
col8.metric("Streak Máxima", f"{max_streak} dias")

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
    analysis_categories,
    key="analysis_category_tabs",
    on_change="rerun"
)
analysis_selections = {}
for category_name, category_tab in zip(analysis_categories, category_tabs):
    with category_tab:
        analysis_selections[category_name] = st.selectbox(
            "Gráfico",
            analysis_groups[category_name],
            format_func=lambda analysis: analysis.split(". ", 1)[1],
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
    st.subheader("Evolução Temporal e Médias Móveis (Ao5 / Ao12)")
    st.markdown("Dica: Pode selecionar uma área para fazer zoom ou clicar nas legendas para ocultar/mostrar séries.")

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
    st.plotly_chart(fig1, use_container_width=True)

if selected_analysis == "2. Distribuição":
    st.subheader("Distribuição de Frequência dos Tempos")
    fig2 = px.histogram(
        valid_filtered, x='time', nbins=40,
        marginal="box",
        labels={'time': 'Tempo (s)', 'count': 'Frequência'},
        title="Histograma e Distribuição dos Tempos"
    )
    fig2.update_layout(height=550, template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)

if selected_analysis == "3. Penalizações":
    st.subheader("Proporção de Penalizações")
    penalty_map = {0: 'Limpo (0)', 1: '+2 Segundos', 2: 'DNF (Não Concluído)'}
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
    st.plotly_chart(fig3, use_container_width=True)

if selected_analysis == "4. Hora do Dia":
    st.subheader("Desempenho por Hora do Dia")
    valid_filtered_copy = valid_filtered.copy()
    valid_filtered_copy['hour'] = valid_filtered_copy['date'].dt.hour

    fig4 = px.box(
        valid_filtered_copy, x='hour', y='time',
        labels={'hour': 'Hora do Dia', 'time': 'Tempo (s)'},
        title="Distribuição de Tempos por Hora (Boxplot Interativo)"
    )
    fig4.update_layout(height=550, template="plotly_white")
    st.plotly_chart(fig4, use_container_width=True)

if selected_analysis == "5. Consistência Mensal":
    st.subheader("Consistência dos Tempos por Mês")
    valid_filtered_copy = valid_filtered.copy()
    valid_filtered_copy['year_month'] = valid_filtered_copy['date'].dt.to_period('M').astype(str)

    fig5 = px.box(
        valid_filtered_copy, x='year_month', y='time',
        labels={'year_month': 'Mês', 'time': 'Tempo (s)'},
        title="Evolução Mensal da Consistência"
    )
    fig5.update_layout(height=550, template="plotly_white", xaxis={'categoryorder': 'category ascending'})
    st.plotly_chart(fig5, use_container_width=True)

if selected_analysis == "6. PB Progression":

    st.subheader("Progressão do Recorde Pessoal")

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

    st.plotly_chart(
        fig,
        use_container_width=True
    )

if selected_analysis == "12. Sessões":
    st.subheader("Análise das Sessões de Treino")
    st.markdown("Uma nova sessão começa após mais de 30 minutos sem solves.")

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
        st.dataframe(session_table, hide_index=True, use_container_width=True)

        metric_cols = st.columns(3)
        best_session = session_summary.loc[session_summary["tempo médio (s)"].idxmin()] if session_summary["tempo médio (s)"].notna().any() else None
        longest_session = session_summary.loc[session_summary["duração (min)"].idxmax()]
        metric_cols[0].metric(
            "Melhor sessão (média)",
            f"{best_session['tempo médio (s)']:.2f}s" if best_session is not None else "N/A"
        )
        metric_cols[1].metric("Sessão mais longa", f"{longest_session['duração (min)']:.1f} min")
        metric_cols[2].metric("Tamanho médio das sessões", f"{session_summary['solves'].mean():.1f} solves")

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
            st.plotly_chart(fig12, use_container_width=True)
    else:
        st.info("Não há solves no intervalo selecionado.")

if selected_analysis == "13. Aquecimento":
    st.subheader("Efeito de Aquecimento")
    st.markdown("Compara as primeiras 10 com as últimas 10 solves de cada sessão com pelo menos 20 tempos válidos.")

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
        improvement_cols[0].metric("Melhoria / piora média", f"{warmup_summary['diferença (s)'].mean():+.2f}s")
        improvement_cols[1].metric(
            "Sessões com melhoria",
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
        st.plotly_chart(fig13_hist, use_container_width=True)

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
        st.plotly_chart(fig13_bar, use_container_width=True)
    else:
        st.info("Não existem sessões com pelo menos 20 solves de tempo válido no intervalo selecionado.")

if selected_analysis == "14. Fadiga":
    st.subheader("Efeito de Fadiga")
    st.markdown("Cada sessão é dividida em 10 blocos de progresso; tempos mais altos no final podem indicar fadiga.")

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
            st.plotly_chart(fig14, use_container_width=True)
        else:
            st.info("Não há tempos válidos para analisar fadiga.")
    else:
        st.info("Não há solves no intervalo selecionado.")

if selected_analysis == "15. Hora × Dia":
    st.subheader("Heatmap: Hora do Dia × Dia da Semana")
    heatmap_source = valid_filtered.copy()
    weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
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
                y=weekdays,
                aspect="auto",
                color_continuous_scale="Viridis",
                labels={"x": "Hora", "y": "Dia da semana", "color": "Tempo médio (s)"},
                title="Tempo médio (s)"
            )
            fig15_mean.update_layout(height=500, template="plotly_white")
            st.plotly_chart(fig15_mean, use_container_width=True)
        with heat_cols[1]:
            fig15_count = px.imshow(
                count_grid,
                x=list(range(24)),
                y=weekdays,
                aspect="auto",
                color_continuous_scale="Blues",
                labels={"x": "Hora", "y": "Dia da semana", "color": "Número de solves"},
                title="Número de solves"
            )
            fig15_count.update_layout(height=500, template="plotly_white")
            st.plotly_chart(fig15_count, use_container_width=True)
    else:
        st.info("Não há tempos válidos no intervalo selecionado.")

if selected_analysis == "16. Média Global":
    st.subheader("Evolução da Média Global")
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
        st.plotly_chart(fig16, use_container_width=True)
    else:
        st.info("Não há tempos válidos no intervalo selecionado.")

if selected_analysis == "17. Frequência de PB":
    st.subheader("Frequência de PB")
    if not valid_filtered.empty:
        pb_frequency = valid_filtered[["date", "time"]].copy()
        pb_frequency["é_pb"] = pb_frequency["time"] < pb_frequency["time"].cummin().shift(1)
        pb_events = pb_frequency[pb_frequency["é_pb"]].copy()
        pb_frequency_cols = st.columns(3)
        pb_frequency_cols[0].metric("Total de PBs", len(pb_events))
        pb_frequency_cols[1].metric(
            "Último PB",
            f"{pb_events.iloc[-1]['time']:.2f}s" if not pb_events.empty else "N/A",
            delta_description=(
                pb_events.iloc[-1]["date"].strftime("%d/%m/%Y")
                if not pb_events.empty else "Nenhum PB no intervalo"
            )
        )
        days_between = pb_events["date"].diff().dt.total_seconds().div(86400).dropna()
        pb_frequency_cols[2].metric(
            "Média de dias entre PBs",
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
        st.plotly_chart(fig17, use_container_width=True)
    else:
        st.info("Não há tempos válidos no intervalo selecionado.")

if selected_analysis == "18. Probabilidade de PB":
    st.subheader("Probabilidade Histórica de PB")
    if not valid_filtered.empty:
        pb_probability = valid_filtered[["date", "time"]].copy()
        pb_probability["é_pb"] = pb_probability["time"] < pb_probability["time"].cummin().shift(1)
        probability_cols = st.columns(3)
        for col, window in zip(probability_cols, [100, 500, 1000]):
            recent_solves = pb_probability.tail(window)
            probability = recent_solves["é_pb"].mean() * 100
            col.metric(
                f"Últimas {window} solves",
                f"{probability:.2f}%",
                delta_description=f"{int(recent_solves['é_pb'].sum())} PBs em {len(recent_solves)} solves"
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
        st.plotly_chart(fig18, use_container_width=True)
        st.caption("A estimativa usa apenas solves anteriores dentro do intervalo de datas selecionado.")
    else:
        st.info("Não há tempos válidos no intervalo selecionado.")

if selected_analysis == "19. Ao100 / Ao1000":
    st.subheader("Médias Móveis Ao5, Ao12, Ao100 e Ao1000")
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
        st.plotly_chart(fig19, use_container_width=True)
    else:
        st.info("Não há tempos válidos no intervalo selecionado.")

if selected_analysis == "20. Control Chart":
    st.subheader("Control Chart")
    st.markdown("A linha central e os limites de controlo são calculados numa janela móvel de 100 solves.")
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
        st.plotly_chart(fig20, use_container_width=True)
    else:
        st.info("Não há tempos válidos no intervalo selecionado.")

if selected_analysis == "7. Consistência":

    st.subheader("Consistência Relativa ao Longo do Tempo")

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

    st.plotly_chart(
        fig,
        use_container_width=True
    )
    st.caption(
        "CV = desvio padrão ÷ média × 100. Um CV menor indica tempos mais "
        "consistentes relativamente ao nível médio de velocidade."
    )

if selected_analysis == "8. Percentis":

    st.subheader("Percentis de Desempenho")

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

    st.plotly_chart(
        fig,
        use_container_width=True
    )

if selected_analysis == "9. Velocidade vs Consistência":

    st.subheader("Velocidade vs Consistência")

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
        st.info("São necessárias pelo menos 50 solves válidas no intervalo selecionado.")
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
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Cada ponto representa uma janela móvel de 50 solves. A cor e a linha "
            "ligada indicam a ordem temporal; passe o rato sobre um ponto para ver a data."
        )

    st.info(
        "O objetivo ideal é aproximar-se do canto inferior esquerdo "
        "(mais rápido e mais consistente relativamente à média)."
    )

if selected_analysis == "10. Sub-X Rate":

    st.subheader("Taxa de Solves Sub-X")

    threshold = st.slider(
        "Tempo alvo (s)",
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

    st.plotly_chart(
        fig,
        use_container_width=True
    )

if selected_analysis == "11. Solves por Dia":

    st.subheader("Quantidade de Solves por Dia")

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
            name="Solves"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=daily_solves["date"],
            y=daily_solves["rolling7"],
            mode="lines",
            name="Média 7 dias",
            line=dict(color="red", width=3)
        )
    )

    fig.update_layout(
        height=550,
        template="plotly_white",
        xaxis_title="Data",
        yaxis_title="Número de Solves"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
