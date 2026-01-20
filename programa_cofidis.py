import pandas as pd
import streamlit as st
import os
import numpy as np

# --- INTERFAZ DE USUARIO (Streamlit) ---
st.set_page_config(page_title="Cofidis Racing Analytics", page_icon="🚴")

st.title("🚴 Análisis de Dificultad - Cofidis")
st.markdown("Esta herramienta calcula la dificultad de una carrera basada en el ranking UCI del ganador del año anterior.")

def seleccionar_carrera_web(path_csv):
    """Interfaz web para seleccionar la carrera desde el CSV."""
    try:
        # Detecta automáticamente el separador
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
        """Genera notas basadas en el desempeño relativo a Cofidis."""
        if not os.path.exists(self.ranking_path):
            st.error(f"No existe el archivo {self.ranking_path}")
            return None
        
        df = pd.read_csv(self.ranking_path, sep=None, engine='python')
        
        df.columns = df.columns.str.strip()

        col_equipo = None
        if 'Team' in df.columns:
            col_equipo = 'Team'
        elif 'team' in df.columns:
            col_equipo = 'team'
        
        if not col_equipo:
            st.error(f"❌ No se encuentra la columna 'Team'. Columnas actuales: {list(df.columns)}")
            return None

        cofidis = df[df[col_equipo].str.strip() == 'Cofidis']
        
        if cofidis.empty:
            st.warning("⚠️ No se encontraron corredores de 'Cofidis'. Revisa que el nombre en el CSV sea exacto.")
            return None

        idx_mejor_cofidis = cofidis.index.min()
        idx_peor_cofidis = cofidis.index.max()
        rango = idx_peor_cofidis - idx_mejor_cofidis

        def asignar_nota(current_idx):
            if current_idx < idx_mejor_cofidis:
                return 10.0
            if current_idx > idx_peor_cofidis:
                return 0.0
            if rango == 0: 
                return 10.0
            
            nota = 10 * (1 - (current_idx - idx_mejor_cofidis) / rango)
            return round(nota, 2)

        df['nota'] = [asignar_nota(i) for i in range(len(df))]
        
        df.to_csv(self.output_path, index=False)
        st.success("✅ Ranking actualizado con éxito usando la columna 'Team'.")
        return df

    def añadir_nota_a_ganadores(self):
        """Cruza el calendario 2025 con las notas generadas."""
        if not os.path.exists(self.output_path) or not os.path.exists(self.calendario_2025_path):
            return None

        df_ranking = pd.read_csv(self.output_path)
        df_2025 = pd.read_csv(self.calendario_2025_path)
        
        df_2025.columns = df_2025.columns.str.strip()
        df_ranking.columns = df_ranking.columns.str.strip()

        # Unimos por el nombre del ganador (Winner) y el corredor del ranking (Rider)
        df_final = pd.merge(
            df_2025, 
            df_ranking[['Rider', 'nota']], 
            left_on='Winner',  
            right_on='Rider', 
            how='left'
        )

        if 'Rider' in df_final.columns:
            df_final = df_final.drop(columns=['Rider'])

        df_final.to_csv(self.output_final_path, index=False)
        return df_final

    def obtener_nota_carrera(self):
        """Busca la nota final en el archivo procesado."""
        if not os.path.exists(self.output_final_path):
            return "Archivo de resultados no generado."

        df = pd.read_csv(self.output_final_path)
        col_busqueda = 'Race' if 'Race' in df.columns else 'Name'

        termino_busqueda = self.carrera.strip().lower()
        coincidencias = df[df[col_busqueda].str.strip().str.lower().str.contains(termino_busqueda, na=False)]
        
        if coincidencias.empty:
            return "Carrera no encontrada en el histórico 2025."
            
        con_nota = coincidencias.dropna(subset=['nota'])
        
        if not con_nota.empty:
            # Seleccionamos la nota más alta si hay varias versiones de la carrera
            nota = con_nota.sort_values(by='nota', ascending=False)['nota'].values[0]
            return nota
        else:
            return "Carrera encontrada, pero el ganador no está en el ranking UCI (sin nota)."

# --- EJECUCIÓN PRINCIPAL ---
csv_carreras = 'data/upcoming_races_cofidis.csv'

# Asegurar que la carpeta data existe
if not os.path.exists('data'):
    os.makedirs('data')

if os.path.exists(csv_carreras):
    carrera_seleccionada = seleccionar_carrera_web(csv_carreras)

    if st.button("🚀 Calcular Nota de Dificultad"):
        if carrera_seleccionada:
            app = Cofidis(carrera_seleccionada)
            
            with st.spinner('Procesando ranking y calendario...'):
                app.csv_nota_cofidis()
                app.añadir_nota_a_ganadores()
                resultado_nota = app.obtener_nota_carrera()
            
            st.divider()
            st.subheader(f"Carrera: {carrera_seleccionada}")
            
            if isinstance(resultado_nota, (int, float, np.float64)):
                st.metric(label="Nota de Dificultad (Benchmark Cofidis)", value=f"{resultado_nota} / 10")
                
                # Feedback visual según la nota
                if resultado_nota > 8:
                    st.error("🔥 **Nivel Muy Alto:** Participación de élite mundial.")
                elif resultado_nota > 5:
                    st.warning("📈 **Nivel Medio:** Competencia exigente.")
                else:
                    st.success("🚴 **Nivel Accesible:** Gran oportunidad para el equipo.")
            else:
                st.info(resultado_nota)
        else:
            st.warning("Por favor, selecciona una carrera primero.")
else:
    st.error(f"Archivo no encontrado: {csv_carreras}. Verifica la carpeta 'data'.")