
import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

st.set_page_config(page_title="Conversor de Localização de Árvores", layout="centered")
st.title("🌳 Conversor de Coordenadas Relativas para UTM")
st.write("Este app converte localizações relativas de árvores (X, Y) em coordenadas UTM georreferenciadas com base nas faixas de amostragem.")

# Upload das planilhas
arvores_file = st.file_uploader("📄 Envie a planilha com as árvores (ID, X, Y, ID_faixa):", type="csv")
faixas_file = st.file_uploader("📄 Envie a planilha com as faixas (ID_faixa, X0, Y0, X1, Y1):", type="csv")

if arvores_file and faixas_file:
    df_arv = pd.read_csv(arvores_file, sep=';', encoding='latin1')
    df_faixas = pd.read_csv(faixas_file, sep=';', encoding='latin1')

    # Converter colunas com vírgula para ponto
    for col in ['X0', 'Y0', 'X1', 'Y1']:
        df_faixas[col] = df_faixas[col].astype(str).str.replace(',', '.').astype(float)

    # Função para converter ponto (x, y) para UTM absoluto
    def converter_para_utm(row):
        faixa = df_faixas[df_faixas['ID_faixa'] == row['ID_faixa']].iloc[0]
        p0 = np.array([faixa['X0'], faixa['Y0']])
        p1 = np.array([faixa['X1'], faixa['Y1']])
        direcao = p1 - p0
        comprimento = np.linalg.norm(direcao)
        direcao_unit = direcao / comprimento
        perpendicular = np.array([-direcao_unit[1], direcao_unit[0]])
        base = p0 + direcao_unit * row['Y']
        ponto = base + perpendicular * (row['X'] - 25)  # centraliza X=25 no centro da faixa
        return pd.Series({'X_UTM': ponto[0], 'Y_UTM': ponto[1]})

    # Aplicar conversão
    coordenadas = df_arv.apply(converter_para_utm, axis=1)
    df_resultado = pd.concat([df_arv, coordenadas], axis=1)

    # Mostrar resultado
    st.subheader("Prévia dos Pontos Georreferenciados")
    st.dataframe(df_resultado)

    # Exportar CSV
    csv = df_resultado.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Baixar CSV com Coordenadas UTM", csv, "arvores_georreferenciadas.csv", "text/csv")

    # Criar GeoDataFrame e exportar shapefile compactado
    gdf = gpd.GeoDataFrame(df_resultado, geometry=gpd.points_from_xy(df_resultado.X_UTM, df_resultado.Y_UTM), crs="EPSG:32721")
    gdf.to_file("/tmp/arvores_georreferenciadas.shp", driver="ESRI Shapefile")
    with open("/tmp/arvores_georreferenciadas.shp", "rb") as f:
        st.download_button("📥 Baixar Shapefile (.shp)", f, "arvores_georreferenciadas.shp")
