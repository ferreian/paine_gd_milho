from st_aggrid import AgGrid, GridOptionsBuilder
import plotly.express as px
import streamlit as st
import pandas as pd
import io
import folium
import numpy as np
import plotly.graph_objects as go
from supabase import create_client
from streamlit_folium import st_folium
import requests
import unicodedata
import datetime
import os
import tempfile
from plotly.colors import qualitative as plotly_qual

# =====================
# 1. IMPORTS E CONFIGS
# =====================

# Supabase config
SUPABASE_URL = "https://wrhysptzozlodsgbonor.supabase.co"
SUPABASE_KEY = os.environ.get(
    "SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndyaHlzcHR6b3psb2RzZ2Jvbm9yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg5NjYwMzksImV4cCI6MjA2NDU0MjAzOX0.Clp7BvkTZDxnD3iXhFITBDdnnwJ-6-BYwtPVTi2OFmc")
if not SUPABASE_KEY:
    st.warning(
        "Chave do Supabase não encontrada. Defina a variável de ambiente SUPABASE_KEY.")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Painel GD", layout="wide")

# =====================
# 2. FUNÇÕES UTILITÁRIAS
# =====================

# Função para atualizar as bases (usada no sidebar)


def atualizar_bases():
    st.cache_data.clear()  # Limpa o cache para forçar atualização
    st.session_state["df_usuarios"] = fetch_table("usuarios")
    st.session_state["df_fazenda"] = fetch_table("fazenda")
    st.session_state["df_resultados"] = fetch_table("resultados")


@st.cache_data
def fetch_table(table_name):
    try:
        response = supabase.table(table_name).select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar dados da tabela '{table_name}': {e}")
        return pd.DataFrame()


def rename_and_reorder(df, rename_dict, order_list):
    df = df.rename(columns=rename_dict)
    return df[[col for col in order_list if col in df.columns]]


def format_dates(df, cols, fmt):
    for col in cols:
        if col in df.columns:
            datas = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
            df[col] = datas.map(lambda x: x.strftime(fmt)
                                if pd.notnull(x) else "")
    return df


def create_key(df, cols, key_name='key'):
    if all(col in df.columns for col in cols):
        df[key_name] = df[cols[0]].astype(str)
        for c in cols[1:]:
            df[key_name] += '_' + df[c].astype(str)
    return df


def upper_case_columns(df, cols):
    for col in cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper()
    return df


def format_float_cols(df, cols):
    for col in cols:
        if col in df.columns:
            s = pd.Series(df[col])
            df[col] = s.apply(lambda x: "" if pd.isna(x)
                              or x == "" else f"{x:.2f}")
    return df


def padronizar_pop_cols(df, cols):
    for col in cols:
        if col in df.columns:
            serie = pd.Series(df[col]).astype(str)
            serie = (
                serie.str.replace(".", "", regex=False)
                .replace("nan", "0")
                .replace("", "0")
                .astype(int)
                .astype(str)
            )
            df[col] = serie
    return df


def convert_to_float(df, cols):
    for col in cols:
        if col in df.columns:
            temp = pd.Series(df[col]).astype(str).str.replace(
                ".", "", regex=False).str.replace(",", ".", regex=False)
            temp = pd.to_numeric(temp, errors='coerce')
            df[col] = pd.Series(temp).fillna(0.0)
    return df


def calc_prod_corr(row):
    resultado = row["resultado"]
    umid = row["umid_colheita"]
    if pd.isna(resultado) or pd.isna(umid) or resultado == 0 or umid == 0:
        return None
    return round(resultado * (100 - umid) / (100 - 13.5), 2)


# Função para formatar datas apenas para exibição
def formatar_datas_para_exibicao(df, colunas, formato="%d/%m/%Y"):
    for col in colunas:
        if col in df.columns:
            df[col + '_exib'] = pd.to_datetime(df[col],
                                               errors='coerce').dt.strftime(formato)
    return df


# =====================
# 3. CARREGAMENTO DE DADOS
# =====================
df_usuarios = fetch_table("usuarios")
df_fazenda = fetch_table("fazenda")
df_resultados = fetch_table("resultados")

# =====================
# 4. PROCESSAMENTO df_fazenda_usuarios
# =====================
col_rename = {
    "fazenda_id": "fazenda_id",
    "criado_em_x": "fazenda_criado_em",
    "modificado_por": "fazenda_modificado_por",
    "produtor": "produtor",
    "fazenda": "fazenda",
    "textura_solo": "textura_solo",
    "fertilidade_solo": "fertilidade_solo",
    "isIrrigado": "irrigado",
    "tipo_GD": "tipo_GD",
    "latitude": "latitude",
    "longitude": "longitude",
    "altitude": "altitude_m",
    "observacoes": "obs_fazenda",
    "aut_imagem": "aut_imagem",
    "modificado_em": "fazenda_modificado_em",
    "criado_por": "usuario_criado_por",
    "nome_cidade": "cidade",
    "codigo_estado": "uf_estado",
    "nome_estado": "estado",
    "cidade_id": "cidade_id",
    "estado_id": "estado_id",
    "usuario_id": "usuario_id",
    "criado_em_y": "usuario_criado_em",
    "nome": "responsavel",
    "email": "email",
    "time": "time",
    "gerente": "gerente",
    "regiao": "regional",
    "isAtivo": "usuario_ativo",
    "isGerente": "usuario_gerente",
    "isAdmin": "usuario_admin",
    "foto_url": "usuario_foto",
}

nova_ordem = [
    "fazenda_id",
    "fazenda",
    "produtor",
    "cidade_id",
    "cidade",
    "estado_id",
    "uf_estado",
    "estado",
    "latitude",
    "longitude",
    "altitude_m",
    "textura_solo",
    "fertilidade_solo",
    "irrigado",
    "tipo_GD",
    "obs_fazenda",
    "aut_imagem",
    "fazenda_criado_em",
    "fazenda_modificado_por",
    "fazenda_modificado_em",
    "usuario_id",
    "usuario_criado_por",
    "responsavel",
    "email",
    "time",
    "gerente",
    "regional",
    "usuario_ativo",
    "usuario_gerente",
    "usuario_admin",
    "usuario_foto",
    "usuario_criado_em",
]

df_fazenda_usuarios = pd.merge(
    df_fazenda, df_usuarios, left_on="criado_por", right_on="usuario_id", how="left"
)
df_fazenda_usuarios = rename_and_reorder(
    df_fazenda_usuarios, col_rename, nova_ordem)
df_fazenda_usuarios = format_dates(df_fazenda_usuarios, [
                                   "fazenda_criado_em", "fazenda_modificado_em", "usuario_criado_em"], "%d/%m/%Y %H:%M:%S")
df_fazenda_usuarios = upper_case_columns(
    df_fazenda_usuarios, ["fazenda", "produtor", "responsavel"])
df_fazenda_usuarios = create_key(
    df_fazenda_usuarios, ["fazenda", "produtor", "usuario_id"])

# =====================
# 5. PROCESSAMENTO df_resultados_usuarios
# =====================
col_rename_resultados = {
    "resultado_id": "resultado_id",
    "fazenda_id": "fazenda_id",
    "criado_por": "resultado_criado_por",
    "criado_em_x": "resultado_criado_em",
    "modificado_por": "resultado_modificado_por",
    "modificado_em": "resultado_modificado_em",
    "cultura": "cultura",
    "data_plantio": "data_plantio",
    "data_colheita": "data_colheita",
    "pop_inicial": "pop_inicial",
    "pop_final": "pop_final",
    "tratamento_id": "tratamento_id",
    "area_total": "area_total",
    "umid_colheita": "umid_colheita",
    "resultado": "resultado",
    "observacoes": "obs_resultado",
    "tratamento": "tratamento",
    "epoca": "epoca",
    "fazenda": "fazenda",
    "produtor": "produtor",
    "pmg": "pmg",
    "avariados": "avariados",
    "usuario_id": "usuario_id",
    "criado_em_y": "usuario_criado_em",
    "nome": "responsavel",
    "email": "email",
    "time": "time",
    "gerente": "gerente",
    "regiao": "regional",
    "isAtivo": "usuario_ativo",
    "isGerente": "usuario_gerente",
    "isAdmin": "usuario_admin",
    "foto_url": "usuario_foto",
}

nova_ordem_resultados = [
    "resultado_id", "fazenda_id", "fazenda", "produtor", "cultura", "data_plantio", "data_colheita",
    "pop_inicial", "pop_final", "tratamento_id", "tratamento", "area_total", "umid_colheita", "resultado", "obs_resultado",
    "pmg", "avariados", "epoca", "resultado_criado_por", "resultado_criado_em",
    "resultado_modificado_por", "resultado_modificado_em", "usuario_id", "usuario_criado_em", "responsavel",
    "email", "time", "gerente", "regional", "usuario_ativo", "usuario_gerente", "usuario_admin", "usuario_foto",
    "key"
]

df_resultados_usuarios = pd.merge(
    df_resultados, df_usuarios, left_on="criado_por", right_on="usuario_id", how="left"
)
df_resultados_usuarios = rename_and_reorder(
    df_resultados_usuarios, col_rename_resultados, nova_ordem_resultados)
df_resultados_usuarios = upper_case_columns(
    df_resultados_usuarios, ["fazenda", "produtor", "responsavel"])
df_resultados_usuarios = create_key(
    df_resultados_usuarios, ["fazenda", "produtor", "usuario_id"])

# 1. Converter para float
convert_to_float(df_resultados_usuarios, [
                 "umid_colheita", "resultado", "area_total"])

# 2. Calcular prod_corr
if "resultado" in df_resultados_usuarios.columns and "umid_colheita" in df_resultados_usuarios.columns:
    df_resultados_usuarios["prod_corr"] = df_resultados_usuarios.apply(
        calc_prod_corr, axis=1)

# 3. Padronizar pop_inicial e pop_final
df_resultados_usuarios = padronizar_pop_cols(
    df_resultados_usuarios, ["pop_inicial", "pop_final"])

# 4. Formatar para exibição (apenas no final, com ponto decimal)
format_float_cols(df_resultados_usuarios, [
                  "umid_colheita", "resultado", "prod_corr", "area_total"])

# 5. NÃO chame convert_to_float nessas colunas novamente!

# Remover a coluna 'fazenda_id' antes do merge final
if 'fazenda_id' in df_resultados_usuarios.columns:
    df_resultados_usuarios = df_resultados_usuarios.drop(columns=[
                                                         'fazenda_id'])

# =====================
# 6. MERGE FINAL E REORDENAÇÃO
# =====================
if not isinstance(df_resultados_usuarios, pd.DataFrame):
    df_resultados_usuarios = pd.DataFrame(df_resultados_usuarios)
if not isinstance(df_fazenda_usuarios, pd.DataFrame):
    df_fazenda_usuarios = pd.DataFrame(df_fazenda_usuarios)
if all(col in df_resultados_usuarios.columns for col in ['key']) and all(col in df_fazenda_usuarios.columns for col in ['key', 'fazenda_id', 'cidade', 'estado']):
    df_resultados_usuarios = df_resultados_usuarios.merge(
        df_fazenda_usuarios[['key', 'fazenda_id',
                             'cidade', 'estado', 'altitude_m', 'tipo_GD']],
        on='key', how='left', suffixes=('', '_fazenda')
    )
# Reordenar as colunas para que cidade, estado, fazenda_id, altitude_m, tipo_GD venham após resultado_id e prod_corr venha após resultado
cols = list(df_resultados_usuarios.columns)
for c in ["cidade", "estado", "fazenda_id", "altitude_m", "tipo_GD", "prod_corr"]:
    if c in cols:
        cols.remove(c)
if "resultado_id" in cols:
    idx = cols.index("resultado_id") + 1
    for c in ["cidade", "estado", "fazenda_id", "altitude_m", "tipo_GD"]:
        if c in df_resultados_usuarios.columns:
            cols.insert(idx, c)
            idx += 1
if "resultado" in cols:
    idx = cols.index("resultado") + 1
    if "prod_corr" in df_resultados_usuarios.columns:
        cols.insert(idx, "prod_corr")
df_resultados_usuarios = df_resultados_usuarios[cols]

# =====================
# 8. PREPARAÇÃO PARA FILTROS (DATAFRAMES FILTRADOS)
# =====================
# Remover duplicados por fazenda_id antes de criar o DataFrame filtrado
if 'fazenda_id' in df_fazenda_usuarios.columns:
    df_fazenda_usuarios = df_fazenda_usuarios.drop_duplicates(
        subset=['fazenda_id'])  # type: ignore
# Remover duplicados por resultado_id antes de criar o DataFrame filtrado
if 'resultado_id' in df_resultados_usuarios.columns:
    df_resultados_usuarios = df_resultados_usuarios.drop_duplicates(
        subset=['resultado_id'])  # type: ignore

df_fazenda_filtrado = df_fazenda_usuarios.copy()
df_resultados_filtrado = df_resultados_usuarios.copy()

# Use SEMPRE os DataFrames *_filtrado para métricas, gráficos e tabelas filtradas

# =====================
# SIDEBAR E CABEÇALHO
# =====================
with st.sidebar:
    st.image(
        "https://wrhysptzozlodsgbonor.supabase.co/storage/v1/object/public/imagens/fotos/logo_stine_vertical_original%201.png",
        width=100
    )

    if st.button("♻️ Carregar e Atualizar Dados"):
        fetch_table.clear()  # limpa o cache da função
        TABELAS = ["usuarios", "fazenda", "resultados"]
        dataframes = {tabela: fetch_table(tabela) for tabela in TABELAS}
        st.session_state["df_usuarios"] = dataframes["usuarios"]
        st.session_state["df_fazenda"] = dataframes["fazenda"]
        st.session_state["df_resultados"] = dataframes["resultados"]
        st.success("✅ Dados carregados com sucesso!")
    st.markdown(
        """
        <div style='margin-top: 20px; font-size: 14px;'>
            Desenvolvido por: <a href='https://www.linkedin.com/in/eng-agro-andre-ferreira/' target='_blank'><b>Andre Ferreira</b></a>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.divider()
    st.markdown("### Filtros para Resultados")

    # Filtros em cascata
    df_filtros = df_resultados_usuarios.copy()

    # Época
    epocas = ["Todos"] + sorted(pd.Series(df_filtros["epoca"]).dropna().astype(str).unique()) if (
        isinstance(df_filtros, pd.DataFrame) and "epoca" in df_filtros.columns) else ["Todos"]
    filtro_epoca = st.selectbox("Época", epocas)
    if filtro_epoca and filtro_epoca != "Todos":
        df_filtros = df_filtros[df_filtros["epoca"] == filtro_epoca]

    # Regional
    regionais = ["Todos"] + sorted(pd.Series(df_filtros["regional"]).dropna().astype(str).unique()) if (
        isinstance(df_filtros, pd.DataFrame) and "regional" in df_filtros.columns) else ["Todos"]
    filtro_regional = st.selectbox("Regional", regionais)
    if filtro_regional and filtro_regional != "Todos":
        df_filtros = df_filtros[df_filtros["regional"] == filtro_regional]

    # Responsável
    responsaveis = ["Todos"] + sorted(pd.Series(df_filtros["responsavel"]).dropna().astype(str).unique()) if (
        isinstance(df_filtros, pd.DataFrame) and "responsavel" in df_filtros.columns) else ["Todos"]
    filtro_responsavel = st.selectbox("Responsável", responsaveis)
    if filtro_responsavel and filtro_responsavel != "Todos":
        df_filtros = df_filtros[df_filtros["responsavel"]
                                == filtro_responsavel]

    # Estado
    estados = ["Todos"] + sorted(pd.Series(df_filtros["estado"]).dropna().astype(str).unique()) if (
        isinstance(df_filtros, pd.DataFrame) and "estado" in df_filtros.columns) else ["Todos"]
    filtro_estado = st.selectbox("Estado", estados)
    if filtro_estado and filtro_estado != "Todos":
        df_filtros = df_filtros[df_filtros["estado"] == filtro_estado]

    # Cidade
    cidades = ["Todos"] + sorted(pd.Series(df_filtros["cidade"]).dropna().astype(str).unique()) if (
        isinstance(df_filtros, pd.DataFrame) and "cidade" in df_filtros.columns) else ["Todos"]
    filtro_cidade = st.selectbox("Cidade", cidades)
    if filtro_cidade and filtro_cidade != "Todos":
        df_filtros = df_filtros[df_filtros["cidade"] == filtro_cidade]

    # Produtor
    produtores = ["Todos"] + sorted(pd.Series(df_filtros["produtor"]).dropna().astype(str).unique()) if (
        isinstance(df_filtros, pd.DataFrame) and "produtor" in df_filtros.columns) else ["Todos"]
    filtro_produtor = st.selectbox("Produtor", produtores)
    if filtro_produtor and filtro_produtor != "Todos":
        df_filtros = df_filtros[df_filtros["produtor"] == filtro_produtor]

    # Fazenda
    fazendas = ["Todos"] + sorted(pd.Series(df_filtros["fazenda"]).dropna().astype(str).unique()) if (
        isinstance(df_filtros, pd.DataFrame) and "fazenda" in df_filtros.columns) else ["Todos"]
    filtro_fazenda = st.selectbox("Fazenda", fazendas)
    if filtro_fazenda and filtro_fazenda != "Todos":
        df_filtros = df_filtros[df_filtros["fazenda"] == filtro_fazenda]

# =====================
# 10. APLICAÇÃO DOS FILTROS NO DATAFRAME FILTRADO
# =====================

# Filtros dropdown
if filtro_epoca and filtro_epoca != "Todos":
    df_resultados_filtrado = df_resultados_filtrado[df_resultados_filtrado["epoca"] == filtro_epoca]

if filtro_regional and filtro_regional != "Todos":
    df_resultados_filtrado = df_resultados_filtrado[df_resultados_filtrado["regional"]
                                                    == filtro_regional]

if filtro_responsavel and filtro_responsavel != "Todos":
    df_resultados_filtrado = df_resultados_filtrado[df_resultados_filtrado["responsavel"]
                                                    == filtro_responsavel]

if filtro_estado and filtro_estado != "Todos":
    df_resultados_filtrado = df_resultados_filtrado[df_resultados_filtrado["estado"] == filtro_estado]

if filtro_cidade and filtro_cidade != "Todos":
    df_resultados_filtrado = df_resultados_filtrado[df_resultados_filtrado["cidade"] == filtro_cidade]

if filtro_produtor and filtro_produtor != "Todos":
    df_resultados_filtrado = df_resultados_filtrado[df_resultados_filtrado["produtor"]
                                                    == filtro_produtor]

if filtro_fazenda and filtro_fazenda != "Todos":
    df_resultados_filtrado = df_resultados_filtrado[df_resultados_filtrado["fazenda"] == filtro_fazenda]

# Garante a coluna status correta ANTES dos gráficos
if isinstance(df_resultados_filtrado, pd.DataFrame) and 'data_colheita' in df_resultados_filtrado.columns:
    if 'status' not in df_resultados_filtrado.columns:
        df_resultados_filtrado = df_resultados_filtrado.copy()
        df_resultados_filtrado['status'] = df_resultados_filtrado['data_colheita'].apply(
            lambda x: 'Em andamento' if pd.isna(
                x) or str(x).strip() == '' else 'Colhido'
        )

# Após a criação de df_resultados_filtrado, garantir tratamento de nulos em data_colheita
if isinstance(df_resultados_filtrado, pd.DataFrame) and 'data_colheita' in df_resultados_filtrado.columns:
    df_resultados_filtrado['data_colheita'] = df_resultados_filtrado['data_colheita'].replace(
        ['', 'nan', 'None', 'NULL', ' '], pd.NA)
    df_resultados_filtrado['data_colheita'] = df_resultados_filtrado['data_colheita'].apply(
        lambda x: pd.NA if isinstance(x, str) and x.strip() == '' else x)

# Garantir que df_resultados_filtrado é um DataFrame antes do filtro de altitude
if not isinstance(df_resultados_filtrado, pd.DataFrame):
    df_resultados_filtrado = pd.DataFrame(df_resultados_filtrado)

# =====================
# 9. VISUALIZAÇÃO FINAL DOS DATAFRAMES FILTRADOS
# =====================
colunas_datas = ["data_plantio", "data_colheita"]


def exibir_tabela_formatada(df, nome_tabela=None):
    if isinstance(df, pd.DataFrame):
        df_exibe = df.copy()
        df_exibe = formatar_datas_para_exibicao(df_exibe, colunas_datas)
        # Reordenar: cada *_exib logo após a original
        cols_exib = []
        for col in df_exibe.columns:
            if col in colunas_datas:
                cols_exib.append(col)
                exib_col = col + '_exib'
                if exib_col in df_exibe.columns:
                    cols_exib.append(exib_col)
        # Adicionar as demais colunas (que não são data_plantio/data_colheita nem *_exib)
        for col in df_exibe.columns:
            if col not in cols_exib and not col.endswith('_exib'):
                cols_exib.append(col)
        if nome_tabela:
            st.markdown(f"#### {nome_tabela}")
        st.dataframe(df_exibe[cols_exib])
        if not df_exibe.empty:
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                with pd.ExcelWriter(tmp.name, engine='openpyxl') as writer:
                    df_exibe[cols_exib].to_excel(writer, index=False)
                tmp.seek(0)
                st.download_button(
                    label=f"📥 Exportar {nome_tabela or 'tabela'} para Excel",
                    data=tmp.read(),
                    file_name=f"{nome_tabela or 'tabela'}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# =====================
# 11. EXIBIÇÃO DAS TABELAS
# =====================


# =====================
# CABEÇALHO
# =====================
st.markdown(
    """
        <h1 style='text-align: center; font-size: 40px; margin-top: 10px;'>
            Painel Resultados Geração de Demanda (GD)
        </h1>
        """,
    unsafe_allow_html=True
)

# --- KPIs, gráficos, mapas, tabelas (usando df_resultados_filtrado para todos os cards, contando resultado_id únicos para andamento/colhido) ---
total_fazendas = df_resultados_filtrado["fazenda_id"].nunique() if isinstance(
    df_resultados_filtrado, pd.DataFrame) and "fazenda_id" in df_resultados_filtrado.columns else 0
total_resultados = df_resultados_filtrado["resultado_id"].nunique() if isinstance(
    df_resultados_filtrado, pd.DataFrame) and "resultado_id" in df_resultados_filtrado.columns else 0
gd_em_andamento = df_resultados_filtrado.loc[df_resultados_filtrado["data_colheita"].isna(), "resultado_id"].nunique() if isinstance(
    df_resultados_filtrado, pd.DataFrame) and "resultado_id" in df_resultados_filtrado.columns and "data_colheita" in df_resultados_filtrado.columns else 0
gd_colhido = df_resultados_filtrado.loc[df_resultados_filtrado["data_colheita"].notna(), "resultado_id"].nunique() if isinstance(
    df_resultados_filtrado, pd.DataFrame) and "resultado_id" in df_resultados_filtrado.columns and "data_colheita" in df_resultados_filtrado.columns else 0

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
    background-color: #f8fafc;
    border-radius: 14px;
    padding: 22px 18px 18px 18px;
    box-shadow: 2px 4px 16px rgba(0, 0, 0, 0.10);
    text-align: center;
    border: 1px solid #e3e8ee;
}}
.card-title {{
    font-size: 19px;
    font-weight: 600;
    margin-bottom: 8px;
    color: #22223b;
}}
.card-number {{
    font-size: 38px;
    font-weight: bold;
    margin: 10px 0 6px 0;
    color: #1f77b4;
}}
.card-subtitle {{
    font-size: 14px;
    color: #4a5568;
}}
</style>

<div class="card-container">
    <div class="card">
        <div class="card-title"># Total de Fazendas (Clientes)</div>
        <div class="card-number">{total_fazendas}</div>
        <div class="card-subtitle">Total de fazendas com resultados</div>
    </div>
    <div class="card">
        <div class="card-title"># Total de Áreas</div>
        <div class="card-number">{total_resultados}</div>
        <div class="card-subtitle">Total de materiais na base</div>
    </div>
    <div class="card">
        <div class="card-title"># Áreas em andamento</div>
        <div class="card-number">{gd_em_andamento}</div>
        <div class="card-subtitle">Áreas de GD ainda em andamento</div>
    </div>
    <div class="card">
        <div class="card-title"># Áreas colhidas</div>
        <div class="card-number">{gd_colhido}</div>
        <div class="card-subtitle">Áreas de GD já colhidas</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Gráficos de quantidade e percentual por regional e status (logo após KPIs)
if isinstance(df_resultados_filtrado, pd.DataFrame) and \
   'regional' in df_resultados_filtrado.columns and \
   'data_colheita' in df_resultados_filtrado.columns:
    # Conta resultado_id únicos por regional e status
    df_contagem = (
        df_resultados_filtrado.groupby(['regional', 'status'])['resultado_id']
        .nunique()
        .reset_index()
        .rename(columns={'resultado_id': 'quantidade'})
    )
    df_total_por_regiao = df_contagem.groupby(
        "regional")['quantidade'].transform('sum')
    df_contagem["percentual"] = (
        df_contagem["quantidade"] / df_total_por_regiao.replace(0, 1) * 100).round(1)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Quantidade de Resultados por Regional e Status")
        fig1 = px.bar(
            df_contagem,
            x="regional",
            y="quantidade",
            color="status",
            barmode="group",
            text="quantidade",
            labels={
                "quantidade": "Qtd Resultados",
                "regional": "Regional",
                "status": "Status"
            },
        )
        fig1.update_traces(
            textposition="outside",
            textfont=dict(size=16, family="Arial", color="black"),
            cliponaxis=False
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
            margin=dict(t=60, b=80, l=60, r=60)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("#### 📉 Percentual de Resultados por Regional e Status")
        fig2 = px.bar(
            df_contagem,
            x="regional",
            y="percentual",
            color="status",
            barmode="stack",
            text="percentual",
            labels={
                "percentual": "%",
                "regional": "Regional",
                "status": "Status"
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

# Carregar GeoJSON dos estados do Brasil (com cache)


@st.cache_data
def carregar_geojson():
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
    try:
        resposta = requests.get(url)
        resposta.raise_for_status()
        return resposta.json()
    except Exception as e:
        st.error(f"Erro ao carregar GeoJSON: {e}")
        return {"features": []}


geojson = carregar_geojson()
# Lista de nomes dos estados conforme GeoJSON
nomes_estados_geojson = [f["properties"]["name"] for f in geojson["features"]]

# Função para converter sigla para nome completo (caso necessário)
sigla_para_nome = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia', 'CE': 'Ceará',
    'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás', 'MA': 'Maranhão', 'MT': 'Mato Grosso',
    'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais', 'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná',
    'PE': 'Pernambuco', 'PI': 'Piauí', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
    'RS': 'Rio Grande do Sul', 'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina',
    'SP': 'São Paulo', 'SE': 'Sergipe', 'TO': 'Tocantins'
}


def estado_para_nome(estado):
    if pd.isna(estado):
        return None
    if estado in nomes_estados_geojson:
        return estado
    return sigla_para_nome.get(estado, estado)


col3, col4 = st.columns(2)

# Mapa 1: Em andamento
with col3:
    st.markdown("#### 🗺️ Status por Estado (Em andamento)")
    # Em andamento: mesma lógica dos KPIs, incluindo 'Sem Estado'
    if isinstance(df_resultados_filtrado, pd.DataFrame) and "data_colheita" in df_resultados_filtrado.columns:
        andamento_mask = df_resultados_filtrado["data_colheita"].isna()
        df_andamento_estado = df_resultados_filtrado.loc[andamento_mask].copy()
    else:
        df_andamento_estado = pd.DataFrame(
            {'estado': pd.Series(dtype='str'), 'valor': pd.Series(dtype='float')})
    # Preencher estado_nome: se não houver estado, marcar como 'Sem Estado'
    df_andamento_estado['estado_nome'] = df_andamento_estado['estado'].apply(lambda x: estado_para_nome(
        x) if pd.notnull(x) and x != '' else 'Sem Estado') if not df_andamento_estado.empty else pd.Series(dtype='str')
    df_estado_andamento = (
        df_andamento_estado.groupby('estado_nome')['resultado_id']
        .nunique()
        .reset_index()
        .rename(columns={'resultado_id': 'valor', 'estado_nome': 'estado'})
    ) if not df_andamento_estado.empty else pd.DataFrame({'estado': pd.Series(dtype='str'), 'valor': pd.Series(dtype='float')})
    # Merge com todos os estados do GeoJSON + 'Sem Estado'
    estados_completo = nomes_estados_geojson + ['Sem Estado']
    df_todos = pd.DataFrame({'estado': estados_completo})
    df_todos = df_todos.merge(df_estado_andamento, on='estado', how='left')

    # Usar azul ainda mais claro para 'Em andamento'
    azul_base_andamento = '#9ecae1'
    azul_claro = '#e3e8ee'
    df_todos['cor'] = df_todos['valor'].apply(
        lambda x: azul_base_andamento if pd.notnull(x) and x > 0 else azul_claro)
    fig_andamento = px.choropleth(
        df_todos[df_todos['estado'] != 'Sem Estado'],
        geojson=geojson,
        locations='estado',
        featureidkey='properties.name',
        color='cor',
        color_discrete_map='identity',
        labels={'cor': 'Qtd Em andamento', 'estado': 'Estado'},
        title='Em andamento por Estado'
    )
    fig_andamento.update_geos(
        fitbounds="locations",
        visible=False,
        showcountries=True,
        countrycolor="Black",
        showcoastlines=False,
        showland=True,
        landcolor="#fff",
        projection_type="mercator",
        center={"lat": -14.2350, "lon": -51.9253},
        lataxis_range=[-35, 5],
        lonaxis_range=[-75, -30]
    )
    fig_andamento.update_layout(
        margin=dict(t=40, b=0, l=0, r=0),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        geo=dict(bgcolor="#fff"),
        coloraxis_showscale=False,
        showlegend=False,
    )
    # Adicionar número e nome do estado centralizados
    lon_list, lat_list, text_list = [], [], []
    for feature in geojson["features"]:
        estado_nome = feature["properties"]["name"]
        if estado_nome in df_todos['estado'].values:
            valor = df_todos.loc[df_todos['estado']
                                 == estado_nome, 'valor'].values[0]
            if pd.notnull(valor) and valor > 0:
                coords = feature["geometry"]["coordinates"][0][0]
                lon_coords = [c[0] for c in coords]
                lat_coords = [c[1] for c in coords]
                lon_centroid = sum(lon_coords) / len(lon_coords)
                lat_centroid = sum(lat_coords) / len(lat_coords)
                texto = f"<b style='font-size:22px;color:#222'>{int(valor)}</b><br><span style='font-size:14px;color:#222'>{estado_nome.upper()}</span>"
                lon_list.append(lon_centroid)
                lat_list.append(lat_centroid)
                text_list.append(texto)
                scatter = go.Scattergeo(
                    lon=lon_list,
                    lat=lat_list,
                    text=text_list,
                    mode="text",
                    textfont=dict(size=16, color="#222"),
                )
    fig_andamento.add_trace(scatter)
    st.plotly_chart(fig_andamento, use_container_width=True)

    # Exibir badge para 'Sem Estado' em andamento
    valor_sem_estado_andamento = df_estado_andamento.loc[
        df_estado_andamento['estado'] == 'Sem Estado', 'valor']
    if not valor_sem_estado_andamento.empty and valor_sem_estado_andamento.values[0] > 0:
        st.markdown(f"""
        <div style='background:#6e6e6e;color:white;padding:12px 18px;border-radius:8px;display:inline-block;font-size:20px;margin-top:10px;'>
            <b>Em andamento sem Estado:</b> {int(valor_sem_estado_andamento.values[0])}
        </div>
        """, unsafe_allow_html=True)

# Mapa 2: Colhido
with col4:
    st.markdown("#### 🗺️ Status por Estado (Colhido)")
    # Colhido: mesma lógica dos KPIs, incluindo 'Sem Estado'
    if isinstance(df_resultados_filtrado, pd.DataFrame) and "data_colheita" in df_resultados_filtrado.columns:
        colhido_mask = df_resultados_filtrado["data_colheita"].notna()
        df_colhido_estado = df_resultados_filtrado.loc[colhido_mask].copy()
    else:
        df_colhido_estado = pd.DataFrame(
            {'estado': pd.Series(dtype='str'), 'valor': pd.Series(dtype='float')})
    df_colhido_estado['estado_nome'] = df_colhido_estado['estado'].apply(lambda x: estado_para_nome(
        x) if pd.notnull(x) and x != '' else 'Sem Estado') if not df_colhido_estado.empty else pd.Series(dtype='str')
    df_estado_colhido = (
        df_colhido_estado.groupby('estado_nome')['resultado_id']
        .nunique()
        .reset_index()
        .rename(columns={'resultado_id': 'valor', 'estado_nome': 'estado'})
    ) if not df_colhido_estado.empty else pd.DataFrame({'estado': pd.Series(dtype='str'), 'valor': pd.Series(dtype='float')})
    estados_completo = nomes_estados_geojson + ['Sem Estado']
    df_todos = pd.DataFrame({'estado': estados_completo})
    df_todos = df_todos.merge(df_estado_colhido, on='estado', how='left')

    # Usar azul escuro para 'Colhido'
    azul_base_colhido = '#3182bd'
    df_todos['cor'] = df_todos['valor'].apply(
        lambda x: azul_base_colhido if pd.notnull(x) and x > 0 else azul_claro)
    fig_colhido = px.choropleth(
        df_todos[df_todos['estado'] != 'Sem Estado'],
        geojson=geojson,
        locations='estado',
        featureidkey='properties.name',
        color='cor',
        color_discrete_map='identity',
        labels={'cor': 'Qtd Colhido', 'estado': 'Estado'},
        title='Colhido por Estado'
    )
    fig_colhido.update_geos(
        fitbounds="locations",
        visible=False,
        showcountries=True,
        countrycolor="Black",
        showcoastlines=False,
        showland=True,
        landcolor="#fff",
        projection_type="mercator",
        center={"lat": -14.2350, "lon": -51.9253},
        lataxis_range=[-35, 5],
        lonaxis_range=[-75, -30]
    )
    fig_colhido.update_layout(
        margin=dict(t=40, b=0, l=0, r=0),
        paper_bgcolor="#fff",
        plot_bgcolor="#fff",
        geo=dict(bgcolor="#fff"),
        coloraxis_showscale=False,
        showlegend=False,
    )
    # Adicionar número e nome do estado centralizados
    lon_list, lat_list, text_list = [], [], []
    for feature in geojson["features"]:
        estado_nome = feature["properties"]["name"]
        if estado_nome in df_todos['estado'].values:
            valor = df_todos.loc[df_todos['estado']
                                 == estado_nome, 'valor'].values[0]
            if pd.notnull(valor) and valor > 0:
                coords = feature["geometry"]["coordinates"][0][0]
                lon_coords = [c[0] for c in coords]
                lat_coords = [c[1] for c in coords]
                lon_centroid = sum(lon_coords) / len(lon_coords)
                lat_centroid = sum(lat_coords) / len(lat_coords)
                texto = f"<b style='font-size:22px;color:#222'>{int(valor)}</b><br><span style='font-size:14px;color:#222'>{estado_nome.upper()}</span>"
                lon_list.append(lon_centroid)
                lat_list.append(lat_centroid)
                text_list.append(texto)
    scatter = go.Scattergeo(
        lon=lon_list,
        lat=lat_list,
        text=text_list,
        mode="text",
        textfont=dict(size=16, color="#222"),
    )
    fig_colhido.add_trace(scatter)
    st.plotly_chart(fig_colhido, use_container_width=True)
    # Exibir badge para 'Sem Estado' colhido
    valor_sem_estado_colhido = df_estado_colhido.loc[df_estado_colhido['estado']
                                                     == 'Sem Estado', 'valor']
    if not valor_sem_estado_colhido.empty and valor_sem_estado_colhido.values[0] > 0:
        st.markdown(f"""
        <div style='background:#6e6e6e;color:white;padding:12px 18px;border-radius:8px;display:inline-block;font-size:20px;margin-top:10px;'>
            <b>Colhidos sem Estado:</b> {int(valor_sem_estado_colhido.values[0])}
        </div>
        """, unsafe_allow_html=True)

# Após os mapas e badges, adicionar bloco de análise de produção por material
st.markdown("---")
st.markdown("#### 📊 Produção média por Híbrido (sc/ha corrigido para 13.5%)")
# st.write("Selecione os híbridos abaixo para visualizar a análise.")

# Cálculo de datas e agrupamento ANTES do expander
if "data_plantio" in df_resultados_filtrado.columns:
    df_resultados_filtrado["data_plantio"] = pd.to_datetime(
        df_resultados_filtrado["data_plantio"], errors="coerce"
    )
else:
    df_resultados_filtrado["data_plantio"] = pd.NaT

data_min = df_resultados_filtrado["data_plantio"].min()
data_max = df_resultados_filtrado["data_plantio"].max()
# Corrigir caso data_min/data_max sejam Series
if isinstance(data_min, pd.Series):
    data_min = data_min.iloc[0]
if isinstance(data_max, pd.Series):
    data_max = data_max.iloc[0]
data_min = pd.to_datetime(data_min, errors="coerce")
data_max = pd.to_datetime(data_max, errors="coerce")
if pd.notna(data_min) and pd.notna(data_max):
    data_min = data_min.date()
    data_max = data_max.date()
else:
    data_min = pd.Timestamp.now().date()
    data_max = pd.Timestamp.now().date()

# 1. Garantir tipo numérico para prod_corr
if "prod_corr" in df_resultados_filtrado.columns:
    df_resultados_filtrado["prod_corr_float"] = pd.to_numeric(
        df_resultados_filtrado["prod_corr"], errors="coerce"
    )
else:
    df_resultados_filtrado["prod_corr_float"] = float('nan')
# 2. Agrupar e calcular média e contagem
_df_plot = df_resultados_filtrado.dropna(
    subset=["prod_corr_float", "tratamento", "resultado_id"])  # type: ignore
df_agrupado = (
    _df_plot.groupby("tratamento", as_index=False)
    .agg(
        prod_corr_float=("prod_corr_float", "mean"),
        n_resultados=("resultado_id", "count")
    )
    .round(1)
)
if not isinstance(df_agrupado, pd.DataFrame):
    df_agrupado = pd.DataFrame(df_agrupado)
if not df_agrupado.empty and "prod_corr_float" in df_agrupado.columns:
    df_agrupado = df_agrupado.sort_values(
        by="prod_corr_float", ascending=False)
df_agrupado["rotulo"] = (
    df_agrupado["prod_corr_float"].astype(str)
    + " (" + df_agrupado["n_resultados"].astype(str) + ")"
)

# Filtros dentro de um expander
with st.expander('Filtros de Produção Média por Material', expanded=True):
    col_data_ini, col_data_fim = st.columns(2)
    with col_data_ini:
        data_inicio = st.date_input(
            "Data Inicial do Plantio",
            value=data_min,
            min_value=data_min,
            max_value=data_max,
            format="DD/MM/YYYY",
            key="data_ini_mat"
        )
    with col_data_fim:
        data_final = st.date_input(
            "Data Final do Plantio",
            value=data_max,
            min_value=data_min,
            max_value=data_max,
            format="DD/MM/YYYY",
            key="data_fim_mat"
        )
    # Multiselect para materiais (mantendo ordem)
    materiais_unicos = df_agrupado["tratamento"].tolist()
    selecionados_materiais = st.multiselect(
        "Híbridos:",
        options=materiais_unicos,
        default=materiais_unicos,
        help="Selecione um ou mais híbridos para analisar a produção média.",
        key="multiselect_hibridos"
    )

# Filtrar pelo intervalo de datas selecionado
# Corrigir: comparar datetime com datetime

data_inicio_ts = pd.to_datetime(data_inicio)
data_final_ts = pd.to_datetime(data_final)
mask_datas = (
    (df_resultados_filtrado["data_plantio"] >= data_inicio_ts) &
    (df_resultados_filtrado["data_plantio"] <= data_final_ts)
)
df_resultados_filtrado = df_resultados_filtrado[mask_datas]

# Garantir que df_resultados_filtrado é um DataFrame antes de usar métodos pandas (análise de produção por material)
if not isinstance(df_resultados_filtrado, pd.DataFrame):
    df_resultados_filtrado = pd.DataFrame(df_resultados_filtrado)

# 4. Filtrar DataFrame final
df_final = df_agrupado[
    (df_agrupado["tratamento"].isin(selecionados_materiais)) &
    (df_agrupado["n_resultados"] > 0) &
    (df_agrupado["prod_corr_float"] > 0)
]
if not isinstance(df_final, pd.DataFrame):
    df_final = pd.DataFrame(df_final)

# 5. Construir o gráfico
st.markdown('#### Média de Produção por Híbrido (sc/ha corrigido 13.5%)')
if not df_final.empty:
    fig = px.bar(
        df_final,
        x="tratamento",
        y="prod_corr_float",
        text="rotulo",
        color="tratamento",
        labels={
            "tratamento": "Híbrido",
            "prod_corr_float": "Média Prod. Corrigida (sc/ha)"
        }
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=16, family="Arial", color="black")
    )
    fig.update_layout(
        title="Média de Produção por Híbrido (sc/ha corrigido 13.5%)",
        font=dict(size=16, family="Arial", color="black"),
        xaxis=dict(title=dict(text="Híbrido", font=dict(
            size=18, family="Arial", color="black"))),
        yaxis=dict(title=dict(text="Média Prod. Corrigida (sc/ha)",
                   font=dict(size=18, family="Arial", color="black"))),
        showlegend=False,
        margin=dict(t=80, b=60),
        plot_bgcolor="#fff",
        paper_bgcolor="#fff"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info('Nenhum dado disponível para os filtros selecionados.')

# Exibir e exportar DataFrame filtrado
# Garantir que df_resultados_filtrado é um DataFrame antes de exportação
if not isinstance(df_resultados_filtrado, pd.DataFrame):
    df_resultados_filtrado = pd.DataFrame(df_resultados_filtrado)
colunas_export = [
    "regional", "responsavel", "estado", "cidade", "produtor", "fazenda",
    "data_plantio", "data_colheita", "tratamento", "umid_colheita", "prod_corr"
]
colunas_export = [
    col for col in colunas_export if col in df_resultados_filtrado.columns]

# Garante que df_export é DataFrame
df_export = df_resultados_filtrado[df_resultados_filtrado["tratamento"].isin(
    selecionados_materiais)].copy()
if not isinstance(df_export, pd.DataFrame):
    df_export = pd.DataFrame(df_export)
rotulos_dict = dict(zip(df_agrupado["tratamento"], df_agrupado["rotulo"]))
# Corrigir uso de .map para Series pandas
if "tratamento" in df_export.columns:
    df_export["média_tratamento (n)"] = pd.Series(
        df_export["tratamento"]).map(rotulos_dict)
else:
    df_export["média_tratamento (n)"] = ""

# Adicionar coluna de diferença da média (sc/ha) (%)
media_dict = dict(
    zip(df_agrupado["tratamento"], df_agrupado["prod_corr_float"]))


def diff_media(row):
    media = media_dict.get(row["tratamento"], None)
    try:
        prod = float(row["prod_corr"])
    except Exception:
        prod = None
    if media is not None and prod is not None and not pd.isnull(prod):
        dif = prod - media
        perc = (dif / media * 100) if media != 0 else 0
        return f"{dif:+.1f} ({perc:+.1f}%)"
    return ""


if "prod_corr" in df_export.columns and "tratamento" in df_export.columns:
    df_export["diferença da média (sc/ha) (%)"] = df_export.apply(
        diff_media, axis=1)

colunas_finais = colunas_export + \
    ["média_tratamento (n)", "diferença da média (sc/ha) (%)"]
df_export_final = df_export[colunas_finais]

# Formatar datas para dd/mm/yyyy (garantir Series)
for col in ["data_plantio", "data_colheita"]:
    if col in df_export_final.columns:
        serie = pd.to_datetime(df_export_final[col], errors="coerce")
        df_export_final[col] = pd.Series(serie).apply(
            lambda x: x.strftime('%d/%m/%Y') if not pd.isnull(x) else '')

st.markdown("#### Dados para exportação")

gb_export = GridOptionsBuilder.from_dataframe(df_export_final)
for col in df_export_final.columns:
    gb_export.configure_column(
        col, resizable=True, sortable=True, filter=True, rowGroup=True)
gb_export.configure_pagination(paginationAutoPageSize=True)
gb_export.configure_side_bar()
gridOptions_export = gb_export.build()
if not isinstance(df_export_final, pd.DataFrame):
    df_export_final = pd.DataFrame(df_export_final)

custom_css = {
    ".ag-header-cell-label": {
        "font-weight": "bold !important",
        "color": "black !important"
    },
    ".ag-cell": {
        "color": "black !important"
    }
}

if not df_export_final.empty:
    AgGrid(
        df_export_final,
        gridOptions=gridOptions_export,
        enable_enterprise_modules=False,
        allow_unsafe_jscode=True,
        theme='streamlit',
        fit_columns_on_grid_load=True,
        custom_css=custom_css
    )
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        with pd.ExcelWriter(tmp.name, engine='openpyxl') as writer:
            df_export_final.to_excel(writer, index=False)
        tmp.seek(0)
        st.download_button(
            label="📥 Exportar dados(Excel)",
            data=tmp.read(),
            file_name="producao_hibridos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Nenhum dado disponível para os filtros selecionados.")

# === Dispersão: Produção vs Umidade de Colheita ===
st.markdown("---")
st.markdown("### 📈 Dispersão: Produção vs Umidade de Colheita")
# st.markdown(
#    "Selecione o intervalo de datas (Plantio) e os materiais desejados para análise. Os demais filtros globais já estão aplicados."
# )

df_disp = df_resultados_filtrado.copy()

# Conversão de tipos (garantir robustez)
if "prod_corr" in df_disp.columns:
    df_disp["prod_corr"] = pd.to_numeric(df_disp["prod_corr"], errors="coerce")
if "umid_colheita" in df_disp.columns:
    df_disp["umid_colheita"] = pd.to_numeric(
        pd.Series(df_disp["umid_colheita"]).astype(str).str.replace(",", "."), errors="coerce"
    )
if "data_plantio" in df_disp.columns:
    df_disp["data_plantio"] = pd.to_datetime(
        df_disp["data_plantio"], errors="coerce")

# Filtro de datas
if "data_plantio" in df_disp.columns:
    data_min = df_disp["data_plantio"].min()
    data_max = df_disp["data_plantio"].max()
    # Corrigir caso sejam Series
    if isinstance(data_min, pd.Series):
        data_min = data_min.iloc[0]
    if isinstance(data_max, pd.Series):
        data_max = data_max.iloc[0]
    if pd.notna(data_min) and pd.notna(data_max):
        data_min = data_min.date()
        data_max = data_max.date()
    else:
        data_min = pd.Timestamp.now().date()
        data_max = pd.Timestamp.now().date()
else:
    data_min = pd.Timestamp.now().date()
    data_max = pd.Timestamp.now().date()

# Filtros dentro de um expander
with st.expander('Filtros de Dispersão: Produção vs Umidade de Colheita', expanded=True):
    col_data1, col_data2 = st.columns(2)
    with col_data1:
        data_inicio_disp2 = st.date_input("Data Inicial (Plantio)", value=data_min, min_value=data_min,
                                          max_value=data_max, format="DD/MM/YYYY", key="data_inicio_disp2")
    with col_data2:
        data_final_disp2 = st.date_input("Data Final (Plantio)", value=data_max, min_value=data_min,
                                         max_value=data_max, format="DD/MM/YYYY", key="data_final_disp2")
    # Filtro por material (multiselect, ordenado por produção)
    materiais_unicos = []
    if "tratamento" in df_disp.columns and "prod_corr" in df_disp.columns:
        try:
            srt = pd.Series(df_disp.groupby("tratamento")["prod_corr"].mean())
            srt = srt.sort_values(ascending=False)
            materiais_unicos = list(srt.index.astype(str))
        except Exception:
            tratamentos = pd.Series(df_disp["tratamento"])
            materiais_unicos = sorted(
                tratamentos.dropna().astype(str).unique().tolist())
    selecionados_materiais = st.multiselect(
        "Materiais (híbridos):",
        options=materiais_unicos,
        default=materiais_unicos,
        help="Selecione um ou mais híbridos para analisar a dispersão.",
        key="multiselect_disp2"
    )

# Filtrar DataFrame final
if not isinstance(df_disp, pd.DataFrame):
    df_disp = pd.DataFrame(df_disp)
df_plot_disp2 = df_disp[
    (df_disp["tratamento"].isin(selecionados_materiais)) &
    (df_disp["prod_corr"].notna()) &
    (df_disp["umid_colheita"].notna())
]

# Agrupar por tratamento e calcular médias
if not df_plot_disp2.empty:
    df_media_disp2 = (
        df_plot_disp2.groupby("tratamento", as_index=False)[
            ["prod_corr", "umid_colheita"]]
        .mean()
        .round(2)
    )
else:
    df_media_disp2 = pd.DataFrame(
        {"tratamento": [], "prod_corr": [], "umid_colheita": []})

# Médias globais
media_producao = float(
    df_media_disp2["prod_corr"].mean()) if not df_media_disp2.empty else None
media_umidade = float(
    df_media_disp2["umid_colheita"].mean()) if not df_media_disp2.empty else None

# Gráfico
st.markdown("#### Dispersão: Produção Média vs Umidade de Colheita (por híbrido)")
if not df_media_disp2.empty:
    fig_disp2 = px.scatter(
        df_media_disp2,
        x="umid_colheita",
        y="prod_corr",
        hover_name="tratamento",
        text="tratamento",
        labels={
            "umid_colheita": "Umidade de Colheita (%)",
            "prod_corr": "Produção Corrigida (sc/ha)"
        }
    )
    fig_disp2.update_traces(
        marker=dict(size=7, opacity=0.8, color="#1f77b4"),
        textposition="top center",
        textfont=dict(size=16, family="Arial", color="black")
    )
    if media_producao is not None:
        fig_disp2.add_hline(
            y=media_producao, line_dash="dash", line_color="red",
            annotation_text=f"Média Produção: {media_producao:.2f} sc/ha",
            annotation_position="top right",
            annotation_font_size=16
        )
    if media_umidade is not None:
        fig_disp2.add_vline(
            x=media_umidade, line_dash="dash", line_color="blue",
            annotation_text=f"Média Umidade: {media_umidade:.2f}%",
            annotation_position="top left",
            annotation_font_size=16
        )
    fig_disp2.update_layout(
        font=dict(size=16, family="Arial",
                  color="black"), margin=dict(t=60, b=60))
    st.plotly_chart(fig_disp2, use_container_width=True)
else:
    st.info("Nenhum dado disponível para os filtros selecionados.")

# =====================
# 11. EXIBIÇÃO DAS TABELAS
# =====================

# Exibir tabelas principais com datas formatadas
# exibir_tabela_formatada(df_fazenda_filtrado, "Fazenda Filtrada")
# exibir_tabela_formatada(df_resultados_filtrado, "Resultados Filtrados")
st.markdown("#### Tabelas com os dados de Resultados e Fazenda")
# Defina aqui as colunas e a ordem desejada para exibição na tabela Resultados Filtrados
colunas_resultados = [
    "resultado_id",
    "fazenda",
    "produtor",
    "cidade",
    "estado",
    "regional",
    "responsavel",
    "data_plantio",
    "data_colheita",
    "tratamento",
    "umid_colheita",
    "prod_corr",
    "pmg",
    "avariados",
    "obs_resultado"
    # Adicione/remova colunas conforme desejar
]
# colunas disponíveis em df_resultados_filtrado:
# Todas as colunas disponíveis em df_resultados_filtrado:
# colunas_resultados_disponiveis = [
#    "resultado_id",
#    "fazenda",
#    "produtor",
#    "cidade",
#    "estado",
#    "fazenda_id",
#    "altitude_m",
#    "tipo_GD",
#    "cultura",
#    "data_plantio",
#    "data_colheita",
#    "pop_inicial",
#    "pop_final",
#    "tratamento_id",
#    "tratamento",
#    "area_total",
#    "umid_colheita",
#    "resultado",
#    "prod_corr",
#    "obs_resultado",
#    "pmg",
#    "avariados",
#    "epoca",
#    "resultado_criado_por",
#    "resultado_criado_em",
#    "resultado_modificado_por",
#    "resultado_modificado_em",
#    "usuario_id",
#    "usuario_criado_em",
#    "responsavel",
#    "email",
#    "time",
#    "gerente",
#    "regional",
#    "usuario_ativo",
#    "usuario_gerente",
#    "usuario_admin",
#    "usuario_foto",
#    "key",
#    "status"
# ...e possíveis colunas extras criadas por filtros ou processamento
# ]


# Filtrar e reordenar o DataFrame antes de exibir
colunas_para_exibir_res = [
    col for col in colunas_resultados if col in df_resultados_filtrado.columns]
df_resultados_exibe = df_resultados_filtrado[colunas_para_exibir_res]

# Garantir que df_resultados_exibe é sempre um DataFrame
if not isinstance(df_resultados_exibe, pd.DataFrame):
    df_resultados_exibe = pd.DataFrame(df_resultados_exibe)

# Contador de resultados (número de resultado_id únicos, igual à métrica)
qtde_resultados_filtrados = df_resultados_exibe["resultado_id"].nunique(
) if "resultado_id" in df_resultados_exibe.columns else 0

st.markdown("#### Resultados ")
gb_res = GridOptionsBuilder.from_dataframe(df_resultados_exibe)
for col in df_resultados_exibe.columns:
    gb_res.configure_column(col, resizable=True,
                            sortable=True, filter=True, rowGroup=True)
gb_res.configure_pagination(paginationAutoPageSize=True)
gb_res.configure_side_bar()
gridOptions_res = gb_res.build()

custom_css_res = {
    ".ag-header-cell-label": {
        "font-weight": "bold !important",
        "color": "black !important"
    },
    ".ag-cell": {
        "color": "black !important"
    }
}

if not df_resultados_exibe.empty:
    # Formatar datas para dd/mm/yyyy imediatamente antes do AgGrid
    for col in ["data_plantio", "data_colheita"]:
        if col in df_resultados_exibe.columns:
            df_resultados_exibe[col] = pd.to_datetime(
                df_resultados_exibe[col], errors="coerce").dt.strftime('%d/%m/%Y').replace('NaT', '')
    AgGrid(
        df_resultados_exibe,
        gridOptions=gridOptions_res,
        enable_enterprise_modules=False,
        allow_unsafe_jscode=True,
        theme='streamlit',
        fit_columns_on_grid_load=True,
        custom_css=custom_css_res
    )
    # Botão para exportar para Excel
    import tempfile
    import pandas as pd
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        with pd.ExcelWriter(tmp.name, engine='openpyxl') as writer:
            df_resultados_exibe.to_excel(writer, index=False)
        tmp.seek(0)
        st.download_button(
            label="📥 Exportar Resultados  (Excel)",
            data=tmp.read(),
            file_name="resultados.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Nenhum dado disponível para os filtros selecionados.")

# Tabela Fazenda Filtrada
# Filtros em linha para df_fazenda_filtrado
if not df_fazenda_filtrado.empty:
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    # Regional
    regionais = [
        "Todos"] + sorted(pd.Series(df_fazenda_filtrado["regional"]).dropna().astype(str).unique())
    with col1:
        filtro_regional_faz = st.selectbox(
            "Regional", regionais, key="faz_regional")
    df_faz = df_fazenda_filtrado.copy()
    if filtro_regional_faz != "Todos":
        df_faz = df_faz[df_faz["regional"] == filtro_regional_faz]

    # Responsável
    responsaveis = [
        "Todos"] + sorted(pd.Series(df_faz["responsavel"]).dropna().astype(str).unique())
    with col2:
        filtro_responsavel_faz = st.selectbox(
            "Responsável", responsaveis, key="faz_responsavel")
    if filtro_responsavel_faz != "Todos":
        df_faz = df_faz[df_faz["responsavel"] == filtro_responsavel_faz]

    # Estado
    estados = ["Todos"] + \
        sorted(pd.Series(df_faz["estado"]).dropna().astype(str).unique())
    with col3:
        filtro_estado_faz = st.selectbox("Estado", estados, key="faz_estado")
    if filtro_estado_faz != "Todos":
        df_faz = df_faz[df_faz["estado"] == filtro_estado_faz]

    # Cidade
    cidades = ["Todos"] + \
        sorted(pd.Series(df_faz["cidade"]).dropna().astype(str).unique())
    with col4:
        filtro_cidade_faz = st.selectbox("Cidade", cidades, key="faz_cidade")
    if filtro_cidade_faz != "Todos":
        df_faz = df_faz[df_faz["cidade"] == filtro_cidade_faz]

    # Produtor
    produtores = [
        "Todos"] + sorted(pd.Series(df_faz["produtor"]).dropna().astype(str).unique())
    with col5:
        filtro_produtor_faz = st.selectbox(
            "Produtor", produtores, key="faz_produtor")
    if filtro_produtor_faz != "Todos":
        df_faz = df_faz[df_faz["produtor"] == filtro_produtor_faz]

    # Fazenda
    fazendas = ["Todos"] + \
        sorted(pd.Series(df_faz["fazenda"]).dropna().astype(str).unique())
    with col6:
        filtro_fazenda_faz = st.selectbox(
            "Fazenda", fazendas, key="faz_fazenda")
    if filtro_fazenda_faz != "Todos":
        df_faz = df_faz[df_faz["fazenda"] == filtro_fazenda_faz]
else:
    df_faz = df_fazenda_filtrado.copy()

# Exibir tabela filtrada

# Garantir que df_faz é sempre um DataFrame
if not isinstance(df_faz, pd.DataFrame):
    df_faz = pd.DataFrame(df_faz)

# Defina aqui as colunas e a ordem desejada para exibição na tabela Fazenda Filtrada
colunas_fazenda = [
    "fazenda_id",
    "fazenda",
    "produtor",
    "cidade",
    "estado",
    "regional",
    "responsavel",
    "latitude",
    "longitude",
    "altitude_m"

    # Adicione/remova colunas conforme desejar
]

# Todas as colunas disponíveis em df_fazenda_usuarios / df_fazenda_filtrado:
# colunas_fazenda_disponiveis = [
#    "fazenda_id",
#    "fazenda",
#    "produtor",
#    "cidade_id",
#    "cidade",
#    "estado_id",
#    "uf_estado",
#    "estado",
#    "latitude",
#    "longitude",
#    "altitude_m",
#    "textura_solo",
#    "fertilidade_solo",
#    "irrigado",
#    "tipo_GD",
#    "obs_fazenda",
#    "aut_imagem",
#    "fazenda_criado_em",
#    "fazenda_modificado_por",
#    "fazenda_modificado_em",
#    "usuario_id",
#    "usuario_criado_por",
#    "responsavel",
#    "email",
#    "time",
#    "gerente",
#    "regional",
#    "usuario_ativo",
#    "usuario_gerente",
#    "usuario_admin",
#    "usuario_foto",
#    "usuario_criado_em",
#    "key"
# ]

# Filtrar e reordenar o DataFrame antes de exibir
colunas_para_exibir = [col for col in colunas_fazenda if col in df_faz.columns]
df_faz_exibe = df_faz[colunas_para_exibir]

# Garantir que df_faz_exibe é sempre um DataFrame
if not isinstance(df_faz_exibe, pd.DataFrame):
    df_faz_exibe = pd.DataFrame(df_faz_exibe)

# Contador de fazendas distintas
if not isinstance(df_faz_exibe, pd.DataFrame):
    df_faz_exibe = pd.DataFrame(df_faz_exibe)
total_fazendas_filtradas = df_faz_exibe["fazenda_id"].nunique(
) if "fazenda_id" in df_faz_exibe.columns else 0

st.markdown(
    f"#### Fazenda/ Clientes  <span style='font-size:18px;color:#1f77b4;'>(Total de Fazendas: <b>{total_fazendas_filtradas}</b>)</span>", unsafe_allow_html=True)

# Filtros em linha para df_fazenda_filtrado
if not df_fazenda_filtrado.empty:
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    # ... (restante dos filtros)
else:
    df_faz = df_fazenda_filtrado.copy()

# Exibir tabela filtrada
gb_faz = GridOptionsBuilder.from_dataframe(df_faz_exibe)
for col in df_faz_exibe.columns:
    gb_faz.configure_column(col, resizable=True,
                            sortable=True, filter=True, rowGroup=True)
gb_faz.configure_pagination(paginationAutoPageSize=True)
gb_faz.configure_side_bar()
gridOptions_faz = gb_faz.build()

custom_css_faz = {
    ".ag-header-cell-label": {
        "font-weight": "bold !important",
        "color": "black !important"
    },
    ".ag-cell": {
        "color": "black !important"
    }
}

if not df_faz_exibe.empty:
    AgGrid(
        df_faz_exibe,
        gridOptions=gridOptions_faz,
        enable_enterprise_modules=False,
        allow_unsafe_jscode=True,
        theme='streamlit',
        fit_columns_on_grid_load=True,
        custom_css=custom_css_faz
    )
    # Botão para exportar para Excel
    import tempfile
    import pandas as pd
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        with pd.ExcelWriter(tmp.name, engine='openpyxl') as writer:
            df_faz_exibe.to_excel(writer, index=False)
        tmp.seek(0)
        st.download_button(
            label="📥 Exportar Fazenda_Clientes (Excel)",
            data=tmp.read(),
            file_name="fazenda_clientes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Nenhum dado disponível para os filtros selecionados.")
