import pandas as pd
import streamlit as st
import os
import numpy as np

# --- INTERFAZ DE USUARIO (Streamlit) ---
st.set_page_config(page_title="Cofidis Racing Analytics", page_icon="🚴")

st.title("🚴 Análisis de Dificultad - Cofidis")
st.markdown("Cálculo de competitividad real basado en el histórico de ganadores 2025.")

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
        """Genera notas base comparando a todo el mundo con el rango de Cofidis."""
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
        """Recalibra la escala ignorando carreras sin datos o con nota 0."""
        if not os.path.exists(self.output_path) or not os.path.exists(self.calendario_2025_path):
            return None

        df_ranking = pd.read_csv(self.output_path)
        df_2025 = pd.read_csv(self.calendario_2025_path)
        df_2025.columns = df_2025.columns.str.strip()
        
        df_final = pd.merge(df_2025, df_ranking[['Rider', 'nota']], 
                           left_on='Winner', right_on='Rider', how='left')

        # --- FILTRO CRÍTICO ---
        # Solo usamos para el cálculo de Max/Min las carreras que tengan nota > 0
        carreras_validas = df_final[df_final['nota'] > 0].copy()

        if not carreras_validas.empty:
            n_min = carreras_validas['nota'].min()
            n_max = carreras_validas['nota'].max()
            rango_reales = n_max - n_min
            
            def recalibrar(valor):
                # Si no hay nota o es 0, no entra en la escala (queda nulo)
                if pd.isna(valor) or valor <= 0:
                    return np.nan 
                
                if rango_reales > 0:
                    nueva_nota = ((valor - n_min) / rango_reales) * 10
                    return round(nueva_nota, 2)
                return 10.0 # Caso donde todos los ganadores tengan la misma nota

            df_final['nota_recalibrada'] = df_final['nota'].apply(recalibrar)
        else:
            df_final['nota_recalibrada'] = np.nan

        if 'Rider' in df_final.columns: df_final = df_final.drop(columns=['Rider'])
        df_final.to_csv(self.output_final_path, index=False)
        return df_final

    def obtener_nota_carrera(self):
        if not os.path.exists(self.output_final_path): return "Error de base de datos"
        df = pd.read_csv(self.output_final_path)
        col_busqueda = 'Race' if 'Race' in df.columns else 'Name'
        
        termino = self.carrera.strip().lower()
        coincidencias = df[df[col_busqueda].str.strip().str.lower().str.contains(termino, na=False)]
        
        if coincidencias.empty: return "Carrera no encontrada en el histórico"
        
        # Cogemos la nota recalibrada más alta de las coincidencias
        con_nota = coincidencias.dropna(subset=['nota_recalibrada'])
        if not con_nota.empty:
            return con_nota.sort_values(by='nota_recalibrada', ascending=False)['nota_recalibrada'].values[0]
        
        return "Sin datos suficientes (Ganador fuera de ranking)"

# --- LÓGICA DE STREAMLIT ---
csv_carreras = 'data/upcoming_races_cofidis.csv'
if not os.path.exists('data'): os.makedirs('data')

if os.path.exists(csv_carreras):
    carrera_seleccionada = seleccionar_carrera_web(csv_carreras)

    if st.button("🚀 Calcular Dificultad"):
        if carrera_seleccionada:
            app = Cofidis(carrera_seleccionada)
            with st.spinner('Filtrando datos nulos y ajustando escala...'):
                app.csv_nota_cofidis()
                app.añadir_nota_a_ganadores()
                resultado = app.obtener_nota_carrera()
            
            st.divider()
            if isinstance(resultado, (float, int, np.float64)):
                st.metric(label=f"Nivel de la prueba: {carrera_seleccionada}", value=f"{resultado} / 10")
                st.caption("Nota ajustada omitiendo carreras sin información UCI.")
                
                if resultado > 8: st.error("Dificultad Extrema")
                elif resultado > 5: st.warning("Dificultad Alta")
                else: st.success("Oportunidad de victoria")
            else:
                st.info(resultado)