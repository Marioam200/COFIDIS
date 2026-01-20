import pandas as pd
import streamlit as st
import os
import numpy as np

# --- INTERFAZ DE USUARIO (Streamlit) ---
st.set_page_config(page_title="Cofidis Racing Analytics", page_icon="🚴")

st.title("🚴 Análisis de Dificultad - Cofidis")
st.markdown("Cálculo de competitividad real basado solo en el calendario de Cofidis.")

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
        self.proximas_carreras_path = 'data/upcoming_races_cofidis.csv' # Archivo de vuestras carreras
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
        """Recalibra basándose SOLO en las carreras que va a correr Cofidis."""
        if not (os.path.exists(self.output_path) and os.path.exists(self.calendario_2025_path) and os.path.exists(self.proximas_carreras_path)):
            return None

        df_ranking = pd.read_csv(self.output_path)
        df_2025 = pd.read_csv(self.calendario_2025_path)
        df_cofidis_list = pd.read_csv(self.proximas_carreras_path, sep=None, engine='python')
        
        df_2025.columns = df_2025.columns.str.strip()
        df_ranking.columns = df_ranking.columns.str.strip()
        df_cofidis_list.columns = df_cofidis_list.str.strip() if hasattr(df_cofidis_list, 'str') else df_cofidis_list.columns.str.strip()

        # 1. Cruzar calendario global con ranking
        df_final = pd.merge(df_2025, df_ranking[['Rider', 'nota']], 
                           left_on='Winner', right_on='Rider', how='left')

        # 2. FILTRO CLAVE: Solo tener en cuenta las carreras que están en vuestro archivo 'upcoming'
        nombres_carreras_cofidis = df_cofidis_list['Name'].unique().tolist()
        
        # Filtramos el dataframe para que el re-escalado solo use vuestras carreras
        carreras_seleccion_cofidis = df_final[df_final['Race'].isin(nombres_carreras_cofidis)].copy()
        
        # Quitamos nulos y ceros de esa selección para hallar los límites reales de vuestro calendario
        carreras_validas = carreras_seleccion_cofidis[carreras_seleccion_cofidis['nota'] > 0]

        if not carreras_validas.empty:
            n_min = carreras_validas['nota'].min()
            n_max = carreras_validas['nota'].max()
            rango_reales = n_max - n_min
            
            # Guardamos los extremos para el test o para mostrar en la app
            st.session_state['extremo_min'] = n_min
            st.session_state['extremo_max'] = n_max

            def recalibrar(valor):
                if pd.isna(valor) or valor <= 0: return np.nan 
                if rango_reales > 0:
                    # El 10 es la carrera más difícil de Cofidis, el 0 la más fácil de Cofidis
                    nueva_nota = ((valor - n_min) / rango_reales) * 10
                    return round(nueva_nota, 2)
                return 10.0

            df_final['nota_recalibrada'] = df_final['nota'].apply(recalibrar)
        else:
            df_final['nota_recalibrada'] = np.nan

        if 'Rider' in df_final.columns: df_final = df_final.drop(columns=['Rider'])
        df_final.to_csv(self.output_final_path, index=False)
        return df_final

    def obtener_nota_carrera(self):
        if not os.path.exists(self.output_final_path): return "Error"
        df = pd.read_csv(self.output_final_path)
        col_busqueda = 'Race' if 'Race' in df.columns else 'Name'
        termino = self.carrera.strip().lower()
        coincidencias = df[df[col_busqueda].str.strip().str.lower().str.contains(termino, na=False)]
        
        if coincidencias.empty: return "Carrera no encontrada en el histórico"
        
        con_nota = coincidencias.dropna(subset=['nota_recalibrada'])
        if not con_nota.empty:
            return con_nota.sort_values(by='nota_recalibrada', ascending=False)['nota_recalibrada'].values[0]
        return "Sin datos (Ganador fuera de ranking)"

# --- EJECUCIÓN ---
csv_carreras = 'data/upcoming_races_cofidis.csv'
if os.path.exists(csv_carreras):
    carrera_seleccionada = seleccionar_carrera_web(csv_carreras)

    if st.button("🚀 Calcular Dificultad"):
        app = Cofidis(carrera_seleccionada)
        with st.spinner('Ajustando escala a vuestro calendario...'):
            app.csv_nota_cofidis()
            app.añadir_nota_a_ganadores()
            resultado = app.obtener_nota_carrera()
        
        st.divider()
        if isinstance(resultado, (float, int, np.float64)):
            st.metric(label=f"Nivel para obetener puntos: {carrera_seleccionada}", value=f"{resultado} / 10")
        else:
            st.info(resultado)