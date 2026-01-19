import pandas as pd

def seleccionar_carrera_consola(path_csv):
    """Permite al usuario elegir una carrera usando la columna 'Name'."""
    try:
        # Usamos sep=None para que detecte si es coma o punto y coma automáticamente
        df = pd.read_csv(path_csv, sep=None, engine='python')
        
        # Como ya sabemos que se llama 'Name', la usamos directamente
        columna = 'Name'
        
        if columna not in df.columns:
            # Por si acaso hay espacios: " Name"
            df.columns = df.columns.str.strip()
        
        opciones = sorted(df['Name'].unique().tolist())
        
        print("\n--- PRÓXIMAS CARRERAS COFIDIS 2026 ---")
        for i, nombre in enumerate(opciones, 1):
            print(f"{i}. {nombre}")
        
        while True:
            try:
                seleccion = int(input(f"\nSelecciona el número (1-{len(opciones)}): "))
                if 1 <= seleccion <= len(opciones):
                    return opciones[seleccion - 1]
                else:
                    print(f"⚠️ Elige un número entre 1 y {len(opciones)}.")
            except ValueError:
                print("⚠️ Introduce un número válido.")
    except Exception as e:
        print(f"❌ Error al leer {path_csv}: {e}")
        exit()

class Cofidis:
    def __init__(self, carrera: str):
        self.carrera = carrera
        self.ranking_path = 'data/PCS_Ranking_Completo.csv'
        self.output_path = 'data/PCS_Ranking_Con_Nota.csv'
        self.calendario_2025_path = 'data/calendario_uci_2025.csv'
        self.output_final_path = 'data/calendario_uci_2025_con_notas.csv'

    def csv_nota(self):
        try:
            df_ranking = pd.read_csv(self.ranking_path)
            N = len(df_ranking)
            df_ranking['nota'] = ((N - (df_ranking.index + 1)) / (N - 1) * 10).round(2)
            df_ranking.to_csv(self.output_path, index=False)
            return df_ranking
        except Exception as e:
            print(f"❌ Error en csv_nota: {e}")

    def añadir_nota_a_ganadores(self):
        try:
            df_ranking = pd.read_csv(self.output_path)
            df_2025 = pd.read_csv(self.calendario_2025_path)
            
            # Limpiamos nombres de columnas por si acaso
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
        except Exception as e:
            print(f"❌ Error en añadir_nota_a_ganadores: {e}")

    def obtener_nota_carrera(self):
        
        try:
            df = pd.read_csv(self.output_final_path)
            col_busqueda = 'Race' if 'Race' in df.columns else 'Name'

            termino_busqueda = self.carrera.strip().lower()
            coincidencias = df[df[col_busqueda].str.strip().str.lower().str.contains(termino_busqueda, na=False)]
            
            if coincidencias.empty:
                return "Carrera no encontrada en el histórico 2025"
            con_nota = coincidencias.dropna(subset=['nota'])
            
            if not con_nota.empty:
                nota = con_nota.sort_values(by='nota', ascending=False)['nota'].values[0]
                return nota
            else:
                return "Carrera encontrada, pero ninguna versión tiene nota en el ranking."
        except Exception as e:
            return f"Error al procesar redundancia: {e}"

if __name__ == "__main__":
    # 1. Selección
    carrera_elegida = seleccionar_carrera_consola('data/upcoming_races_cofidis.csv')
    
    # 2. Proceso
    app = Cofidis(carrera_elegida)
    app.csv_nota()
    app.añadir_nota_a_ganadores()
    
    # 3. Resultado
    nota = app.obtener_nota_carrera()
    
    print("\n" + "="*40)
    print(f"CARRERA: {carrera_elegida}")
    print(f"NOTA DIFICULTAD: {nota}")
    print("="*40)