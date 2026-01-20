import pandas as pd
import streamlit as st
import os
import numpy as np

# --- INTERFAZ DE USUARIO (Streamlit) ---
st.set_page_config(page_title="Cofidis Racing Analytics", page_icon="🚴")

st.title("🚴 Análisis de Dificultad - Cofidis")
st.markdown("Esta herramienta calcula la dificultad ponderada basada en el ranking de los ganadores de 2025.")

def seleccionar_carrera_web(path_csv):
    try:
        df = pd.read_csv(path_csv, sep=None, engine='python')
        df.columns = df.columns.str.strip()
        if 'Name' not in df.columns:
            st.error(f"No se encontró la columna 'Name' en {path_csv}")
            return None
        opciones = sorted(df['Name'].unique().tolist())
        seleccion = st.selectbox("Selecciona la próxima carrera Cofidis 2026:", opciones)
        return seleccion
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo de carreras: {e}")
        return None

class Cofidis:
    def __init__(self, carrera: str):
        self.carrera = carrera
        self.ranking_path = 'data/PCS_Ranking_Completo.csv'
        self.output_path = 'data/PCS_Ranking_Con_Nota.csv'
        self.calendario_2025_path = 'data/calendario_uci_2025.csv'
        self.output_final_path = 'data/calendario_uci_2025_con_notas.csv'

    def csv_nota_cofidis(self):
        if not os.path.exists(self.ranking_path): return None
        df = pd.read_csv(self.ranking_path, sep=None, engine='python')
        df.columns = df.columns.str.strip()

        col_equipo = 'Team' if 'Team' in df.columns else 'team'
        cofidis = df[df[col_equipo].str.strip() == 'Cofidis']
        
        if cofidis.empty: return None

        idx_mejor = cofidis.index.min()
        idx_peor = cofidis.index.max()
        rango = idx_peor - idx_mejor

        def asignar_nota(current_idx):
            if current_idx < idx_mejor: return 10.0
            if current_idx > idx_peor: return 0.0
            if rango == 0: return 10.0
            nota = 10 * (1 - (current_idx - idx_mejor) / rango)
            return round(nota, 2)

        df['nota'] = [asignar_nota(i) for i in range(len(df))]
        df.to_csv(self.output_path, index=False)
        return df

    def añadir_nota_a_ganadores(self):
        if not os.path.exists(self.output_path): return None
        df_ranking = pd.read_csv(self.output_path)
        df_2025 = pd.read_csv(self.calendario_2025_path)
        df_2025.columns = df_2025.columns.str.strip()
        
        df_final = pd.merge(df_2025, df_ranking[['Rider', 'nota']], 
                           left_on='Winner', right_on='Rider', how='left')
        
        # --- NUEVA LÓGICA: RE-CALIBRACIÓN (Normalización Min-Max) ---
        # Cogemos todas las notas de los ganadores que NO sean nulas
        notas_validas = df_final['nota'].dropna()
        if not notas_validas.empty:
            n_min = notas_validas.min()
            n_max = notas_validas.max()
            rango_n = n_max - n_min
            
            if rango_n > 0:
                # Aplicamos la fórmula para que el peor ganador sea 0 y el mejor 10
                df_final['nota_recalibrada'] = ((df_final['nota'] - n_min) / rango_n) * 10
                df_final['nota_recalibrada'] = df_final['nota_recalibrada'].round(2)
            else:
                df_final['nota_recalibrada'] = 10.0
        
        if 'Rider' in df_final.columns: df_final = df_final.drop(columns=['Rider'])
        df_final.to_csv(self.output_final_path, index=False)
        return df_final

    def obtener_nota_carrera(self):
        if not os.path.exists(self.output_final_path): return "Error de datos"
        df = pd.read_csv(self.output_final_path)
        col_busqueda = 'Race' if 'Race' in df.columns else 'Name'
        
        termino = self.carrera.strip().lower()
        coincidencias = df[df[col_busqueda].str.strip().str.lower().str.contains(termino, na=False)]
        
        if coincidencias.empty: return "Carrera no encontrada"
        
        # Buscamos la nota recalibrada
        con_nota = coincidencias.dropna(subset=['nota_recalibrada'])
        if not con_nota.empty:
            return con_nota.sort_values(by='nota_recalibrada', ascending=False)['nota_recalibrada'].values[0]
        return "Ganador no rankeado"

# --- EJECUCIÓN ---
csv_carreras = 'data/upcoming_races_cofidis.csv'
if not os.path.exists('data'): os.makedirs('data')

if os.path.exists(csv_carreras):
    carrera_seleccionada = seleccionar_carrera_web(csv_carreras)

    if st.button("🚀 Calcular Nota de Dificultad"):
        app = Cofidis(carrera_seleccionada)
        with st.spinner('Analizando competitividad...'):
            app.csv_nota_cofidis()
            app.añadir_nota_a_ganadores()
            resultado = app.obtener_nota_carrera()
        
        st.divider()
        if isinstance(resultado, (int, float, np.float64)):
            st.metric(label=f"Dificultad Re-escalada para {carrera_seleccionada}", value=f"{resultado} / 10")
            
            # Gráfico de contexto para el usuario
            st.info(f"Nota original estirada: El ganador más débil de 2025 ahora marca el 0 y el mejor el 10.")
            
            if resultado > 7.5:
                st.error("Nivel Top: Los mejores del mundo ganan aquí.")
            elif resultado > 4:
                st.warning("Nivel Pro: Competencia muy equilibrada.")
            else:
                st.success("Oportunidad: Nivel por debajo de la media de ganadores UCI.")
        else:
            st.info(resultado)