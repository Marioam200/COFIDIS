import pandas as pd
import streamlit as st
import os

# --- INTERFAZ DE USUARIO (Streamlit) ---
st.set_page_config(page_title="Cofidis Racing Analytics", page_icon="🚴")

st.title("🚴 Análisis de Dificultad - Cofidis")
st.markdown("Esta herramienta calcula la dificultad de una carrera basada en el ranking UCI del ganador del año anterior.")

def seleccionar_carrera_web(path_csv):
    """Interfaz web para seleccionar la carrera desde el CSV."""
    try:
        # Detecta automáticamente el separador (coma o punto y coma)
        df = pd.read_csv(path_csv, sep=None, engine='python')
        
        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip()
        
        if 'Name' not in df.columns:
            st.error(f"No se encontró la columna 'Name' en {path_csv}")
            return None
            
        opciones = sorted(df['Name'].unique().tolist())
        
        # El selector visual de Streamlit
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

    def csv_nota(self):
        """Genera notas del 0 al 10 basadas en la posición del ranking."""
        df_ranking = pd.read_csv(self.ranking_path)
        N = len(df_ranking)
        df_ranking['nota'] = ((N - (df_ranking.index + 1)) / (N - 1) * 10).round(2)
        df_ranking.to_csv(self.output_path, index=False)
        return df_ranking

    def añadir_nota_a_ganadores(self):
        """Cruza el calendario 2025 con las notas del ranking."""
        df_ranking = pd.read_csv(self.output_path)
        df_2025 = pd.read_csv(self.calendario_2025_path)
        
        df_2025.columns = df_2025.columns.str.strip()
        df_ranking.columns = df_ranking.columns.str.strip()

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
        """Busca la carrera en el histórico 2025 y devuelve la nota del ganador."""
        df = pd.read_csv(self.output_final_path)
        col_busqueda = 'Race' if 'Race' in df.columns else 'Name'

        termino_busqueda = self.carrera.strip().lower()
        coincidencias = df[df[col_busqueda].str.strip().str.lower().str.contains(termino_busqueda, na=False)]
        
        if coincidencias.empty:
            return "Carrera no encontrada en el histórico 2025"
            
        con_nota = coincidencias.dropna(subset=['nota'])
        
        if not con_nota.empty:
            # Prioriza la carrera con la nota más alta (masculina/profesional suele ser mayor)
            nota = con_nota.sort_values(by='nota', ascending=False)['nota'].values[0]
            return nota
        else:
            return "Carrera encontrada, pero el ganador no está en el ranking UCI."

# --- EJECUCIÓN PRINCIPAL ---
csv_carreras = 'data/upcoming_races_cofidis.csv'

if os.path.exists(csv_carreras):
    carrera_seleccionada = seleccionar_carrera_web(csv_carreras)

    if st.button("🚀 Calcular Nota de Dificultad"):
        app = Cofidis(carrera_seleccionada)
        
        with st.spinner('Procesando datos...'):
            app.csv_nota()
            app.añadir_nota_a_ganadores()
            resultado_nota = app.obtener_nota_carrera()
        
        # Mostrar resultado visual
        st.divider()
        st.subheader(f"Resultado: {carrera_seleccionada}")
        
        if isinstance(resultado_nota, (int, float)):
            # Usamos una métrica visual de Streamlit
            st.metric(label="Nota de Dificultad (basada en ganador 2025)", value=f"{resultado_nota} / 10")
            if resultado_nota > 8:
                st.write("🔥 **Nivel Muy Alto:** Carrera con participación de élite.")
            elif resultado_nota > 5:
                st.write("📈 **Nivel Medio:** Competencia estándar UCI.")
            else:
                st.write("🚴 **Nivel Accesible:** Oportunidad para sumar puntos.")
        else:
            st.warning(resultado_nota)
else:
    st.error(f"No se encuentra el archivo {csv_carreras}. Asegúrate de que esté en la carpeta 'data'.")