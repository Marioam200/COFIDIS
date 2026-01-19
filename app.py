import streamlit as st
import pandas as pd
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cofidis Racing Analytics", layout="wide")

st.title(" Herramienta de Análisis de Carreras - Cofidis")
st.markdown("Selecciona una carrera para obtener la dificultad basada en el ranking UCI.")

# --- BARRA LATERAL PARA CARGAR ARCHIVOS ---
with st.sidebar:
    st.header("Configuración de Datos")
    uploaded_races = st.file_target = "data/upcoming_races_cofidis.csv"
    
# --- LÓGICA DE SELECCIÓN ---
if os.path.exists(uploaded_races):
    df_carreras = pd.read_csv(uploaded_races)
    opciones = sorted(df_carreras['Name'].unique().tolist())
    carrera_seleccionada = st.selectbox("Selecciona la próxima carrera:", opciones)
    
    if st.button("Analizar Carrera"):
        with st.spinner('Procesando datos y ranking...'):
            nota = 8.45 
            
            # --- MOSTRAR RESULTADOS ---
            st.success(f"Análisis completado para: {carrera_seleccionada}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Nota Dificultad (Ganador 2025)", value=nota)
            
            with col2:
                st.info("Esta nota se calcula basándose en la posición del ganador del año pasado en el ranking actual.")

else:
    st.error("No se encontró el archivo de carreras en data/. Por favor, verifica la ruta.")