from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px
import streamlit as st
import pandas as pd
import io
import folium
import numpy as np
import plotly.graph_objects as go
from supabase import create_client
from streamlit import cache_data
from streamlit_folium import st_folium

# 🔐 Supabase config
SUPABASE_URL = "https://wrhysptzozlodsgbonor.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndyaHlzcHR6b3psb2RzZ2Jvbm9yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg5NjYwMzksImV4cCI6MjA2NDU0MjAzOX0.Clp7BvkTZDxnD3iXhFITBDdnnwJ-6-BYwtPVTi2OFmc"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# 🔁 Nome da view usada
VIEW = "view_resultados"


@cache_data
def fetch_table(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        if hasattr(response, 'error') and response.error:
            st.error(
                f"Erro ao obter dados da view {table_name}: {response.error}")
            return pd.DataFrame()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Erro ao processar a view {table_name}: {str(e)}")
        return pd.DataFrame()

# 📄 Função para exportar para Excel


def to_excel(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    buffer.seek(0)
    return buffer


# 🖼️ Configuração da página
st.set_page_config(page_title="Painel GD", layout="wide")

# 🎯 Logo + Título
col1, col2 = st.columns([1, 4])
with col1:
    st.image(
        "https://wrhysptzozlodsgbonor.supabase.co/storage/v1/object/public/imagens/fotos/logo_stine_vertical_original%201.png",
        width=100
    )
with col2:
    st.markdown(
        """
        <h1 style='text-align: center; font-size: 40px; margin-top: 10px;'>
            Painel Resultados Geração de Demanda (GD)
        </h1>
        """,
        unsafe_allow_html=True
    )


# 🔁 Botão para atualizar base
if st.button("🔄 Atualizar base de dados"):
    with st.spinner("Atualizando..."):
        st.session_state["df_resultados"] = fetch_table(VIEW)
    st.success("Dados atualizados com sucesso!")


# 🔄 Carregar dados se ainda não carregado
if "df_resultados" not in st.session_state:
    with st.spinner("Carregando dados..."):
        st.session_state["df_resultados"] = fetch_table(VIEW)

# ✅ Define variável local
df_resultados = st.session_state["df_resultados"]

# 🎛️ Filtros visíveis
st.markdown("### 🔍 Filtros")

df_filtros = df_resultados.copy()

# Filtro 1 - Época (não depende dos outros)
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    filtro_epoca = st.selectbox(
        "Época",
        ["Todos"] + sorted(df_filtros["epoca"].dropna().unique().tolist()),
        key="filtro_epoca_card"
    )

# Aplicar filtro da Época para os próximos filtros dependentes
if filtro_epoca != "Todos":
    df_filtros = df_filtros[df_filtros["epoca"] == filtro_epoca]

# Filtro 2 - Regional
with col2:
    filtro_regional = st.selectbox(
        "Regional",
        ["Todos"] + sorted(df_filtros["regional"].dropna().unique().tolist()),
        key="filtro_regional_card"
    )
if filtro_regional != "Todos":
    df_filtros = df_filtros[df_filtros["regional"] == filtro_regional]

# Filtro 3 - Estado
with col3:
    filtro_estado = st.selectbox(
        "Estado",
        ["Todos"] +
        sorted(df_filtros["nome_estado"].dropna().unique().tolist()),
        key="filtro_estado_card"
    )
if filtro_estado != "Todos":
    df_filtros = df_filtros[df_filtros["nome_estado"] == filtro_estado]

# Filtro 4 - Cidade
with col4:
    filtro_cidade = st.selectbox(
        "Cidade",
        ["Todos"] +
        sorted(df_filtros["nome_cidade"].dropna().unique().tolist()),
        key="filtro_cidade_card"
    )
if filtro_cidade != "Todos":
    df_filtros = df_filtros[df_filtros["nome_cidade"] == filtro_cidade]

# Filtro 5 - Responsável (coluna "nome")
with col5:
    filtro_responsavel = st.selectbox(
        "Responsável",
        ["Todos"] + sorted(df_filtros["nome"].dropna().unique().tolist()),
        key="filtro_responsavel_card"
    )
if filtro_responsavel != "Todos":
    df_filtros = df_filtros[df_filtros["nome"] == filtro_responsavel]

# Atualiza o df_resultados para os dados filtrados
df_resultados_filtrados = df_filtros.copy()

# 🧮 Indicadores
total_fazendas = df_resultados_filtrados["fazenda_id"].nunique()
total_resultados = len(df_resultados_filtrados)
gd_em_andamento = df_resultados_filtrados["data_colheita"].isna().sum()
gd_colhido = df_resultados_filtrados["data_colheita"].notna().sum()

# 💡 Cards HTML com f-strings
st.markdown(f"""
<style>
.card-container {{
    display: flex;
    gap: 20px;
    justify-content: space-between;
    margin-top: 25px;
    margin-bottom: 25px;
    flex-wrap: wrap;
}}
.card {{
    flex: 1;
    min-width: 220px;
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 2px 4px 12px rgba(0, 0, 0, 0.12);
    text-align: center;
}}
.card-title {{
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 10px;
}}
.card-number {{
    font-size: 36px;
    font-weight: bold;
    margin: 10px 0;
}}
.card-subtitle {{
    font-size: 14px;
    color: #1f77b4;
}}
</style>

<div class="card-container">
    <div class="card">
        <div class="card-title"># Total de Fazendas (Clientes)</div>
        <div class="card-number">{total_fazendas}</div>
        <div class="card-subtitle">Total de fazendas com resultados</div>
    </div>
    <div class="card">
        <div class="card-title"># GD Total</div>
        <div class="card-number">{total_resultados}</div>
        <div class="card-subtitle">Total de materiais na base</div>
    </div>
    <div class="card">
        <div class="card-title"># GD Em andamento</div>
        <div class="card-number">{gd_em_andamento}</div>
        <div class="card-subtitle">Áreas de GD ainda em andamento</div>
    </div>
    <div class="card">
        <div class="card-title"># GD Colhido</div>
        <div class="card-number">{gd_colhido}</div>
        <div class="card-subtitle">Áreas de GD já colhidas</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 🔄 Status
df_resultados_filtrados["status_gd"] = df_resultados_filtrados["data_colheita"].apply(
    lambda x: "Colhido" if pd.notnull(x) else "Em andamento"
)

# 📊 Dados agregados para gráfico de contagem
df_contagem = df_resultados_filtrados.groupby(
    ["regional", "status_gd"]).size().reset_index(name="quantidade")

# 📉 Dados para gráfico de % por regional
df_total_por_regiao = df_contagem.groupby(
    "regional")["quantidade"].transform("sum")
df_contagem["percentual"] = (
    df_contagem["quantidade"] / df_total_por_regiao * 100).round(1)


# 🎨 Gráficos
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📊 Quantidade de Resultados por Regional e Status")
    fig1 = px.bar(
        df_contagem,
        x="regional",
        y="quantidade",
        color="status_gd",
        barmode="group",
        text="quantidade",
        labels={
            "quantidade": "Qtd Resultados",
            "regional": "Regional",
            "status_gd": "Status"
        },
    )
    fig1.update_traces(
        textposition="outside",
        textfont=dict(size=16, family="Arial", color="black"),
        cliponaxis=False  # 👈 Garante que os rótulos fora da barra não sejam cortados
    )
    fig1.update_layout(
        font=dict(size=16, family="Arial", color="black"),
        xaxis=dict(
            title=dict(
                text="Regional",
                font=dict(size=18, family="Arial", color="black")
            ),
            tickfont=dict(size=14, family="Arial", color="black")
        ),
        yaxis=dict(
            title=dict(
                text="Qtd Resultados",
                font=dict(size=18, family="Arial", color="black")
            ),
            tickfont=dict(size=14, family="Arial", color="black")
        ),
        legend=dict(
            font=dict(size=16, family="Arial", color="black")
        ),
        margin=dict(t=60, b=80, l=60, r=60)  # 👈 Margens maiores
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("#### 📉 Percentual de Resultados por Regional e Status")
    fig2 = px.bar(
        df_contagem,
        x="regional",
        y="percentual",
        color="status_gd",
        barmode="stack",
        text="percentual",
        labels={
            "percentual": "%",
            "regional": "Regional",
            "status_gd": "Status"
        },
    )
    fig2.update_traces(
        textposition="outside",
        textfont=dict(size=16, family="Arial", color="black"),
        cliponaxis=False
    )
    fig2.update_layout(
        font=dict(size=16, family="Arial", color="black"),
        xaxis=dict(
            title=dict(
                text="Regional",
                font=dict(size=18, family="Arial", color="black")
            ),
            tickfont=dict(size=14, family="Arial", color="black")
        ),
        yaxis=dict(
            title=dict(
                text="Percentual (%)",
                font=dict(size=18, family="Arial", color="black")
            ),
            tickfont=dict(size=14, family="Arial", color="black")
        ),
        legend=dict(
            font=dict(size=16, family="Arial", color="black")
        ),
        margin=dict(t=60, b=80, l=60, r=60)
    )
    st.plotly_chart(fig2, use_container_width=True)


# 🎯 Análise de Produção por Material
st.markdown("#### 📊 Produção média por Material (sc/ha corrigido para 13%)")
st.write("Selecione os filtros abaixo, incluindo o intervalo de datas (Plantio) e os materiais para visualizar a análise.")

# 🔁 Garantir tipo numérico e datetime
df_resultados["prod_13_sc_ha"] = pd.to_numeric(
    df_resultados["prod_13_sc_ha"], errors="coerce")
df_resultados["data_plantio"] = pd.to_datetime(
    df_resultados["data_plantio"], errors="coerce")

# 📅 Datas mínima e máxima
data_min = df_resultados["data_plantio"].min().date()
data_max = df_resultados["data_plantio"].max().date()

# 📅 Seletor de Datas
col_data_ini, col_data_fim = st.columns(2)
with col_data_ini:
    data_inicio = st.date_input("Data Inicial", value=data_min, min_value=data_min, max_value=data_max,
                                format="DD/MM/YYYY", key="data_ini_mat")
with col_data_fim:
    data_final = st.date_input("Data Final", value=data_max, min_value=data_min, max_value=data_max,
                               format="DD/MM/YYYY", key="data_fim_mat")

# ⏳ Aplicar filtro de datas
df_data = df_resultados[
    (df_resultados["data_plantio"].dt.date >= data_inicio) &
    (df_resultados["data_plantio"].dt.date <= data_final)
]

# 🎯 Filtros hierárquicos
col_epoca, col_reg, col_est, col_cid, col_prod, col_faz, col_resp = st.columns(
    7)

with col_epoca:
    filtro_epoca = st.selectbox("Época", [
                                "Todos"] + sorted(df_data["epoca"].dropna().unique().tolist()), key="epoca_mat")
with col_reg:
    filtro_regional = st.selectbox("Regional", [
                                   "Todos"] + sorted(df_data["regional"].dropna().unique().tolist()), key="reg_mat")

df_temp = df_data.copy()
if filtro_epoca != "Todos":
    df_temp = df_temp[df_temp["epoca"] == filtro_epoca]
if filtro_regional != "Todos":
    df_temp = df_temp[df_temp["regional"] == filtro_regional]

with col_est:
    filtro_estado = st.selectbox("Estado", [
                                 "Todos"] + sorted(df_temp["nome_estado"].dropna().unique().tolist()), key="estado_mat")
if filtro_estado != "Todos":
    df_temp = df_temp[df_temp["nome_estado"] == filtro_estado]

with col_cid:
    filtro_cidade = st.selectbox("Cidade", [
                                 "Todos"] + sorted(df_temp["nome_cidade"].dropna().unique().tolist()), key="cid_mat")
if filtro_cidade != "Todos":
    df_temp = df_temp[df_temp["nome_cidade"] == filtro_cidade]

with col_prod:
    filtro_produtor = st.selectbox("Produtor", [
                                   "Todos"] + sorted(df_temp["produtor"].dropna().unique().tolist()), key="prod_mat")
if filtro_produtor != "Todos":
    df_temp = df_temp[df_temp["produtor"] == filtro_produtor]

with col_faz:
    filtro_fazenda = st.selectbox("Fazenda", [
                                  "Todos"] + sorted(df_temp["fazenda"].dropna().unique().tolist()), key="faz_mat")
if filtro_fazenda != "Todos":
    df_temp = df_temp[df_temp["fazenda"] == filtro_fazenda]

with col_resp:
    filtro_responsavel = st.selectbox("Responsável", [
                                      "Todos"] + sorted(df_temp["nome"].dropna().unique().tolist()), key="resp_mat")
if filtro_responsavel != "Todos":
    df_temp = df_temp[df_temp["nome"] == filtro_responsavel]

# 📈 Gráfico
df_plot = df_temp.dropna(
    subset=["prod_13_sc_ha", "tratamento", "resultado_id"])
df_agrupado = (
    df_plot.groupby("tratamento", as_index=False)
    .agg(prod_13_sc_ha=("prod_13_sc_ha", "mean"), n_resultados=("resultado_id", "count"))
    .round(1)
    .sort_values("prod_13_sc_ha", ascending=False)
)

df_agrupado["rotulo"] = df_agrupado["prod_13_sc_ha"].astype(
    str) + " (" + df_agrupado["n_resultados"].astype(str) + ")"

col_graf, col_exp = st.columns([9, 1])
with col_exp:
    with st.expander("🔎 Filtrar Materiais", expanded=False):
        tratamentos_disponiveis = sorted(
            df_agrupado["tratamento"].unique().tolist())
        st.markdown("**Selecione os materiais:**")
        tratamentos_selecionados = [t for t in tratamentos_disponiveis if st.checkbox(
            t, value=True, key=f"check_mat_{t}")]

with col_graf:
    df_final = df_agrupado[df_agrupado["tratamento"].isin(
        tratamentos_selecionados)]
    if not df_final.empty:
        fig = px.bar(
            df_final,
            x="tratamento",
            y="prod_13_sc_ha",
            text="rotulo",
            color="tratamento",
            labels={"tratamento": "Material",
                    "prod_13_sc_ha": "Produção média (sc/ha)"}
        )
        fig.update_traces(textposition="outside", textfont=dict(
            size=16, family="Arial", color="black"))
        fig.update_layout(
            font=dict(size=16, family="Arial", color="black"),
            xaxis=dict(title=dict(text="Material", font=dict(size=18))),
            yaxis=dict(title=dict(
                text="Produção média (sc/ha)", font=dict(size=18))),
            showlegend=False,
            margin=dict(t=80, b=60)
        )
        st.plotly_chart(fig, use_container_width=True)


# 🎯 Dispersão: Produção vs Umidade de Colheita
st.markdown("### 📈 Dispersão: Produção vs Umidade de Colheita")
st.markdown(
    "Selecione os filtros abaixo, incluindo o intervalo de datas (Plantio) e os materiais desejados para análise.")

# 🔁 Conversão de colunas
df_resultados["prod_13_sc_ha"] = pd.to_numeric(
    df_resultados["prod_13_sc_ha"], errors="coerce")
df_resultados["umid_colheita"] = pd.to_numeric(
    df_resultados["umid_colheita"].astype(str).str.replace(",", "."), errors="coerce")
df_resultados["data_plantio"] = pd.to_datetime(
    df_resultados["data_plantio"], errors="coerce")

# 📅 Filtros de Data
data_min = df_resultados["data_plantio"].min()
data_max = df_resultados["data_plantio"].max()

col_data1, col_data2 = st.columns(2)
with col_data1:
    data_inicio_disp2 = st.date_input("Data Inicial", value=data_min.date(), min_value=data_min.date(),
                                      max_value=data_max.date(), format="DD/MM/YYYY", key="data_inicio_disp2")
with col_data2:
    data_final_disp2 = st.date_input("Data Final", value=data_max.date(), min_value=data_min.date(),
                                     max_value=data_max.date(), format="DD/MM/YYYY", key="data_final_disp2")

# 🔎 Filtros
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    filtro_epoca_disp2 = st.selectbox("Época", ["Todos"] + sorted(
        df_resultados["epoca"].dropna().unique().tolist()), key="epoca_disp2")
with col2:
    filtro_regional_disp2 = st.selectbox("Regional", ["Todos"] + sorted(
        df_resultados["regional"].dropna().unique().tolist()), key="regional_disp2")

df_temp_disp2 = df_resultados.copy()
if filtro_epoca_disp2 != "Todos":
    df_temp_disp2 = df_temp_disp2[df_temp_disp2["epoca"] == filtro_epoca_disp2]
if filtro_regional_disp2 != "Todos":
    df_temp_disp2 = df_temp_disp2[df_temp_disp2["regional"]
                                  == filtro_regional_disp2]

with col3:
    filtro_estado_disp2 = st.selectbox("Estado", ["Todos"] + sorted(
        df_temp_disp2["nome_estado"].dropna().unique().tolist()), key="estado_disp2")
if filtro_estado_disp2 != "Todos":
    df_temp_disp2 = df_temp_disp2[df_temp_disp2["nome_estado"]
                                  == filtro_estado_disp2]

with col4:
    filtro_cidade_disp2 = st.selectbox("Cidade", ["Todos"] + sorted(
        df_temp_disp2["nome_cidade"].dropna().unique().tolist()), key="cidade_disp2")
if filtro_cidade_disp2 != "Todos":
    df_temp_disp2 = df_temp_disp2[df_temp_disp2["nome_cidade"]
                                  == filtro_cidade_disp2]

with col5:
    filtro_produtor_disp2 = st.selectbox("Produtor", ["Todos"] + sorted(
        df_temp_disp2["produtor"].dropna().unique().tolist()), key="produtor_disp2")
if filtro_produtor_disp2 != "Todos":
    df_temp_disp2 = df_temp_disp2[df_temp_disp2["produtor"]
                                  == filtro_produtor_disp2]

with col6:
    filtro_fazenda_disp2 = st.selectbox("Fazenda", ["Todos"] + sorted(
        df_temp_disp2["fazenda"].dropna().unique().tolist()), key="fazenda_disp2")
if filtro_fazenda_disp2 != "Todos":
    df_temp_disp2 = df_temp_disp2[df_temp_disp2["fazenda"]
                                  == filtro_fazenda_disp2]

# 🎯 Filtro por Data
df_temp_disp2 = df_temp_disp2[
    (df_temp_disp2["data_plantio"].dt.date >= data_inicio_disp2) &
    (df_temp_disp2["data_plantio"].dt.date <= data_final_disp2)
]

# 📊 Dados finais
df_plot_disp2 = df_temp_disp2.dropna(
    subset=["prod_13_sc_ha", "umid_colheita", "tratamento"])

# Médias por tratamento
df_media_disp2 = df_plot_disp2.groupby("tratamento", as_index=False)[
    ["prod_13_sc_ha", "umid_colheita"]].mean().round(2)

# 📦 Layout: gráfico (90%) + expander (10%)
col_graf_disp2, col_exp_disp2 = st.columns([9, 1])
with col_exp_disp2:
    with st.expander("🔎 Filtrar Materiais", expanded=False):
        tratamentos_disp2 = sorted(
            df_media_disp2["tratamento"].dropna().unique().tolist())
        st.markdown("**Selecione os materiais:**")
        tratamentos_selecionados_disp2 = [t for t in tratamentos_disp2 if st.checkbox(
            t, value=False, key=f"check_disp2_{t}")]

# Exibir todos se nada for marcado
if not tratamentos_selecionados_disp2:
    tratamentos_selecionados_disp2 = tratamentos_disp2

with col_graf_disp2:
    df_filtrado_disp2 = df_media_disp2[df_media_disp2["tratamento"].isin(
        tratamentos_selecionados_disp2)]

    media_producao = df_filtrado_disp2["prod_13_sc_ha"].mean().round(2)
    media_umidade = df_filtrado_disp2["umid_colheita"].mean().round(2)

    fig_disp2 = px.scatter(
        df_filtrado_disp2,
        x="umid_colheita",
        y="prod_13_sc_ha",
        hover_name="tratamento",
        text="tratamento",
        labels={
            "umid_colheita": "Umidade de Colheita (%)",
            "prod_13_sc_ha": "Produção Média (sc/ha)"
        }
    )

    fig_disp2.update_traces(
        marker=dict(size=10, color="gray", opacity=0.8),
        textposition="top center",
        textfont=dict(size=16, family="Arial", color="black")
    )

    fig_disp2.add_shape(
        type="line",
        x0=df_filtrado_disp2["umid_colheita"].min(),
        x1=df_filtrado_disp2["umid_colheita"].max(),
        y0=media_producao,
        y1=media_producao,
        line=dict(color="red", width=2, dash="dash")
    )
    fig_disp2.add_annotation(
        x=df_filtrado_disp2["umid_colheita"].max(),
        y=media_producao,
        text=f"Média Produção: {media_producao} sc/ha",
        showarrow=False,
        xanchor="left",
        yanchor="middle",
        xshift=5,
        font=dict(color="red", size=14)
    )

    fig_disp2.add_shape(
        type="line",
        x0=media_umidade,
        x1=media_umidade,
        y0=df_filtrado_disp2["prod_13_sc_ha"].min(),
        y1=df_filtrado_disp2["prod_13_sc_ha"].max(),
        line=dict(color="blue", width=2, dash="dash")
    )
    fig_disp2.add_annotation(
        x=media_umidade,
        y=df_filtrado_disp2["prod_13_sc_ha"].max(),
        text=f"Média Umidade: {media_umidade}%",
        showarrow=False,
        xanchor="center",
        yanchor="bottom",
        yshift=10,
        font=dict(color="blue", size=14)
    )

    fig_disp2.update_layout(
        font=dict(size=16, family="Arial", color="black"),
        xaxis=dict(
            title=dict(text="Umidade de Colheita (%)", font=dict(
                size=18, family="Arial", color="black")),
            tickfont=dict(size=14, family="Arial", color="black")
        ),
        yaxis=dict(
            title=dict(text="Produção Média (sc/ha)",
                       font=dict(size=18, family="Arial", color="black")),
            tickfont=dict(size=14, family="Arial", color="black")
        ),
        showlegend=False,
        margin=dict(t=80, b=60)
    )

    st.plotly_chart(fig_disp2, use_container_width=True)


# 📈 Relação: Média do Local vs Produção do Material
st.markdown(
    "### 📈Índice Ambiental: Relação entre Média do Local e Produção do Material")
st.write("Selecione os filtros abaixo, incluíndo o intervalo de datas (Plantio) e escolha os materiais para visualizar a análise.")

# 🔁 Conversão de data
df_resultados["data_plantio"] = pd.to_datetime(
    df_resultados["data_plantio"], errors="coerce")

# 📅 Filtros por data (ANTES dos filtros geográficos)
data_min_ia = df_resultados["data_plantio"].min().date()
data_max_ia = df_resultados["data_plantio"].max().date()

col_d1, col_d2 = st.columns(2)
with col_d1:
    data_inicio_ia = st.date_input(
        "Data Inicial",
        value=data_min_ia,
        min_value=data_min_ia,
        max_value=data_max_ia,
        format="DD/MM/YYYY",
        key="data_ini_ia"
    )
with col_d2:
    data_final_ia = st.date_input(
        "Data Final",
        value=data_max_ia,
        min_value=data_min_ia,
        max_value=data_max_ia,
        format="DD/MM/YYYY",
        key="data_fim_ia"
    )

# 🔎 Filtros específicos do bloco
col1, col2, col3, col4 = st.columns(4)

with col1:
    filtro_epoca_ia = st.selectbox("Época", [
                                   "Todos"] + sorted(df_resultados["epoca"].dropna().unique()), key="epoca_ia")
with col2:
    filtro_regional_ia = st.selectbox("Regional", [
                                      "Todos"] + sorted(df_resultados["regional"].dropna().unique()), key="regional_ia")

df_temp_ia = df_resultados.copy()
if filtro_epoca_ia != "Todos":
    df_temp_ia = df_temp_ia[df_temp_ia["epoca"] == filtro_epoca_ia]
if filtro_regional_ia != "Todos":
    df_temp_ia = df_temp_ia[df_temp_ia["regional"] == filtro_regional_ia]

with col3:
    filtro_estado_ia = st.selectbox("Estado", [
                                    "Todos"] + sorted(df_temp_ia["nome_estado"].dropna().unique()), key="estado_ia")
if filtro_estado_ia != "Todos":
    df_temp_ia = df_temp_ia[df_temp_ia["nome_estado"] == filtro_estado_ia]

with col4:
    filtro_cidade_ia = st.selectbox("Cidade", [
                                    "Todos"] + sorted(df_temp_ia["nome_cidade"].dropna().unique()), key="cidade_ia")
if filtro_cidade_ia != "Todos":
    df_temp_ia = df_temp_ia[df_temp_ia["nome_cidade"] == filtro_cidade_ia]

# 📅 Aplicar filtro de data
df_temp_ia = df_temp_ia[
    (df_temp_ia["data_plantio"].dt.date >= data_inicio_ia) &
    (df_temp_ia["data_plantio"].dt.date <= data_final_ia)
]

# 📊 Cálculo da média do local e da produção
df_t = df_temp_ia.dropna(subset=["tratamento", "fazenda", "prod_13_sc_ha"])
df_t = df_t.groupby(["fazenda", "tratamento"], as_index=False)[
    "prod_13_sc_ha"].mean()
media_local = df_t.groupby(
    "fazenda")["prod_13_sc_ha"].mean().reset_index(name="media_local")
df_t = df_t.merge(media_local, on="fazenda")

# 📦 Layout com gráfico + filtro de tratamentos
col_graf_ia, col_exp_ia = st.columns([9, 1])

with col_exp_ia:
    with st.expander("🔎 Filtrar Materiais", expanded=False):
        tratamentos_ia = sorted(df_t["tratamento"].dropna().unique().tolist())
        st.markdown("**Selecione os materiais:**")
        tratamentos_selecionados_ia = [
            t for t in tratamentos_ia if st.checkbox(t, value=False, key=f"check_ia_{t}")]

with col_graf_ia:
    import numpy as np
    import plotly.graph_objects as go

    fig_ia = go.Figure()

    if tratamentos_selecionados_ia:
        df_filtrado_ia = df_t[df_t["tratamento"].isin(
            tratamentos_selecionados_ia)]

        for t in tratamentos_selecionados_ia:
            df_mat = df_filtrado_ia[df_filtrado_ia["tratamento"] == t]

            fig_ia.add_trace(go.Scatter(
                x=df_mat["media_local"],
                y=df_mat["prod_13_sc_ha"],
                mode="markers",
                marker=dict(size=10, opacity=0.7),
                name=t,
                showlegend=True,
                hovertext=[
                    f"{t} — {round(y, 1)} sc/ha" for y in df_mat["prod_13_sc_ha"]],
                hoverinfo="text"
            ))

            if len(df_mat) >= 2:
                coef = np.polyfit(df_mat["media_local"],
                                  df_mat["prod_13_sc_ha"], 1)
                linha_x = np.linspace(
                    df_mat["media_local"].min(), df_mat["media_local"].max(), 100)
                linha_y = coef[0] * linha_x + coef[1]

                fig_ia.add_trace(go.Scatter(
                    x=linha_x,
                    y=linha_y,
                    mode="lines",
                    line=dict(width=2),
                    name=f"{t} (reta)",
                    hoverinfo="skip",
                    showlegend=True
                ))
            else:
                fig_ia.add_annotation(
                    x=df_mat["media_local"].mean() if not df_mat.empty else 0,
                    y=df_mat["prod_13_sc_ha"].mean(
                    ) if not df_mat.empty else 0,
                    text="Número de resultados insuficiente",
                    showarrow=False,
                    font=dict(color="gray", size=12)
                )
    else:
        fig_ia.add_trace(go.Scatter(
            x=df_t["media_local"],
            y=df_t["prod_13_sc_ha"],
            mode="markers",
            marker=dict(size=8, color="lightgray", opacity=0.6),
            hovertext=[f"{t} — {round(y, 1)} sc/ha" for t,
                       y in zip(df_t["tratamento"], df_t["prod_13_sc_ha"])],
            hoverinfo="text",
            showlegend=False
        ))

    fig_ia.update_layout(
        title="Relação entre Média do Local e Produção do Material",
        xaxis=dict(
            title=dict(text="Média do Local (sc/ha)",
                       font=dict(size=18, family="Arial", color="black")),
            tickfont=dict(size=14, family="Arial", color="black")
        ),
        yaxis=dict(
            title=dict(text="Produção do Material (sc/ha)",
                       font=dict(size=18, family="Arial", color="black")),
            tickfont=dict(size=14, family="Arial", color="black")
        ),
        font=dict(size=16, family="Arial", color="black"),
        margin=dict(t=60, b=60),
        showlegend=bool(tratamentos_selecionados_ia)
    )

    st.plotly_chart(fig_ia, use_container_width=True)


# 📊 Tabela + botão de exportar com AgGrid


# 🏷️ Dicionário de renomeação
renomear_colunas = {
    "resultado_id": "ID Resultado",
    "criado_por": "Criado Por",
    "cultura": "Cultura",
    "data_plantio": "Data Plantio",
    "data_colheita": "Data Colheita",
    "pop_inicial": "População Inicial",
    "pop_final": "População Final",
    "area_total": "Área Total (ha)",
    "umid_colheita": "Umidade (%)",
    "resultado": "Produção (sc)",
    "observacoes": "Observações Resultado",
    "tratamento": "Material",
    "epoca": "Época",
    "fazenda": "Fazenda",
    "produtor": "Produtor",
    "chave_resultado": "Chave Resultado",
    "prod_13_sc_ha": "Prod. Corrigida 13% (sc/ha)",
    "nome": "Nome Responsável",
    "time": "Time",
    "gerente": "Gerente",
    "regional": "Regional",
    "fazenda_id": "ID Fazenda",
    "textura_solo": "Textura Solo",
    "fertilidade_solo": "Fertilidade Solo",
    "isIrrigado": "Irrigado?",
    "tipo_GD": "Tipo GD",
    "latitude": "Latitude",
    "longitude": "Longitude",
    "altitude": "Altitude",
    "obs_fazenda": "Observações Fazenda",
    "aut_imagem": "Imagem Fazenda",
    "nome_cidade": "Cidade",
    "nome_estado": "Estado",
    "cidade_id": "ID Cidade",
    "estado_id": "ID Estado",
    "pmg": "PMG",
    "avariados": "Avariados(%)",
    "obs_resultado": "Observações Resultado",

}

# 👁️ Lista de colunas visíveis (pode ajustar à vontade)
colunas_visiveis = [
    "cultura", "epoca", "gerente", "regional", "nome_estado", "nome_cidade", "fazenda", "produtor", "obs_fazenda", "nome",
    "data_plantio", "data_colheita", "tratamento",
    "pop_inicial", "pop_final", "umid_colheita", "prod_13_sc_ha",
    "pmg", "avariados", "obs_resultado"

]

# 📦 Aplicar seleção + renomeação
df_visu = df_resultados[colunas_visiveis].rename(columns=renomear_colunas)

# 📅 Formatar datas para exibição
df_visu["Data Plantio"] = pd.to_datetime(
    df_visu["Data Plantio"], errors="coerce").dt.strftime("%d/%m/%Y")
df_visu["Data Colheita"] = pd.to_datetime(
    df_visu["Data Colheita"], errors="coerce").dt.strftime("%d/%m/%Y")

# 📋 Exibir com AgGrid
st.markdown("### 📋 Resultados")
gb = GridOptionsBuilder.from_dataframe(df_visu)
gb.configure_default_column(cellStyle={'fontSize': '14px'})
gb.configure_grid_options(headerHeight=30)

custom_css = {
    ".ag-header-cell-label": {
        "font-weight": "bold",
        "font-size": "15px",
        "color": "black"
    }
}

AgGrid(
    df_visu,
    gridOptions=gb.build(),
    height=500,
    custom_css=custom_css
)

# 💾 Exportar
output = io.BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df_visu.to_excel(writer, index=False, sheet_name="resultados_gd")

st.download_button(
    label="📥 Exportar Resultados para Excel",
    data=output.getvalue(),
    file_name="resultados_gd.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
