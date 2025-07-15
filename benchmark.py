import time
import json
import pandas as pd
from datetime import datetime
from collections import Counter
from classifier import classify_email
from subcategories import SUBCATEGORIA_TO_CLASE

# CONFIGURACIÓN
CONFIG = {
    'n_limit': 250,
    'max_requests_per_minute': 3,
    'excel_file': "Solicitudes 2025.xlsx",
    'sheet_name': "Data",
    'results_file': "benchmark_results.csv"
}

class RateLimiter:
    """Maneja el control de tasa de solicitudes a la API."""
    
    def __init__(self, max_requests_per_minute: int):
        self.max_requests_per_minute = max_requests_per_minute
        self.requests_made = 0
        self.start_time = time.time()
    
    def wait_if_needed(self):
        """Espera si se ha alcanzado el límite de solicitudes por minuto."""
        if self.requests_made >= self.max_requests_per_minute:
            elapsed = time.time() - self.start_time
            if elapsed < 60:
                sleep_time = 60 - elapsed + 2  # +2 segundos de buffer
                print(f"Esperando {sleep_time:.1f} segundos para reiniciar límite de tasa...")
                time.sleep(sleep_time)
            self._reset_counter()
    
    def increment(self):
        """Incrementa el contador de solicitudes."""
        self.requests_made += 1
    
    def _reset_counter(self):
        """Reinicia el contador de solicitudes."""
        self.requests_made = 0
        self.start_time = time.time()
    
    def get_remaining(self) -> int:
        """Retorna el número de solicitudes restantes en el minuto actual."""
        return max(0, self.max_requests_per_minute - self.requests_made)

def load_data(file_path: str, sheet_name: str, n_limit: int) -> pd.DataFrame:
    """
    Carga y prepara los datos del archivo Excel.
    
    Args:
        file_path (str): Ruta al archivo Excel
        sheet_name (str): Nombre de la hoja
        n_limit (int): Límite de filas a procesar
        
    Returns:
        pd.DataFrame: DataFrame con los datos preparados
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        df = df[["Descripcion", "Subcategoria"]].dropna()

        # Mapear a clases usando el diccionario
        df["Clase"] = df["Subcategoria"].map(lambda x: SUBCATEGORIA_TO_CLASE.get(x.strip(), "NO CLASIFICABLE"))

        # Dividir en clasificables y no clasificables
        clasificables = df[df["Clase"] == "ALTA/BAJA"]
        no_clasificables = df[df["Clase"] == "NO CLASIFICABLE"]

        # Tomar n/2 de cada uno (ej: 5 + 5)
        half = n_limit // 2
        df_final = pd.concat([
            clasificables.sample(n = half, random_state = 42),
            no_clasificables.sample(n = half, random_state = 42)
        ], ignore_index = True)

        print(f"Datos cargados: {len(df_final)} registros (balanceados 50/50)")
        return df_final

    except Exception as e:
        print(f"Error cargando datos balanceados: {e}")
        raise

def map_subcategory_to_class(subcategory: str) -> str:
    """
    Mapea la subcategoría real a la clase esperada.
    
    Args:
        subcategory (str): Subcategoría del archivo Excel
        
    Returns:
        str: Clase esperada ('ALTA/BAJA', o 'NO CLASIFICABLE')
    """
    sub = subcategory.strip()

    return SUBCATEGORIA_TO_CLASE.get(sub, "NO CLASIFICABLE")

def process_emails(df: pd.DataFrame, rate_limiter: RateLimiter) -> list:
    """
    Procesa todos los emails y retorna los resultados.
    
    Args:
        df (pd.DataFrame): DataFrame con los emails a procesar
        rate_limiter (RateLimiter): Controlador de tasa
        
    Returns:
        list: Lista con los resultados de clasificación
    """
    results = []
    total_emails = len(df)
    
    print(f"\nIniciando procesamiento de {total_emails} emails...")
    print("=" * 60)
    
    for i, row in df.iterrows():
        rate_limiter.wait_if_needed()
        
        email_text = str(row["Descripcion"])
        real_subcategory = str(row["Subcategoria"])
        
        try:
            print(f"\nProcesando {i+1}/{total_emails}")
            print(f"Texto: {email_text[:80]}{'...' if len(email_text) > 80 else ''}")
            
            # Clasificar email
            prediction = classify_email(email_text)
            rate_limiter.increment()
            
            # Obtener clasificación esperada
            expected = map_subcategory_to_class(real_subcategory)
            
            # Evaluar si es correcto
            is_correct = prediction == expected
            
            # Crear registro de resultado
            result = {
                'index': i,
                'descripcion': email_text,
                'subcategoria_original': real_subcategory,
                'clasificacion_esperada': expected,
                'clasificacion_predicha': prediction,
                'correcto': is_correct,
                'timestamp': datetime.now().isoformat()
            }
            
            results.append(result)
            
            # Mostrar resultado
            status_icon = "OK" if is_correct else "ERROR"
            print(f"Predicción: {prediction}")
            print(f"Esperado: {expected}")
            print(f"{status_icon} Resultado: {'CORRECTO' if is_correct else 'INCORRECTO'}")
            print(f"Solicitudes restantes: {rate_limiter.get_remaining()}")
            
        except Exception as e:
            print(f"Error procesando email {i+1}: {e}")
            
            # Manejo de errores específicos
            if any(keyword in str(e).lower() for keyword in ["rate_limit", "quota", "limit", "429"]):
                print("Rate limit detectado. Esperando 65 segundos...")
                time.sleep(65)
                rate_limiter._reset_counter()
                
                # Reintentar la clasificación
                try:
                    prediction = classify_email(email_text)
                    expected = map_subcategory_to_class(real_subcategory)
                    is_correct = prediction == expected
                    
                    result = {
                        'index': i,
                        'descripcion': email_text,
                        'subcategoria_original': real_subcategory,
                        'clasificacion_esperada': expected,
                        'clasificacion_predicha': prediction,
                        'correcto': is_correct,
                        'timestamp': datetime.now().isoformat()
                    }
                    results.append(result)
                    
                except Exception as retry_error:
                    print(f"Error en reintento: {retry_error}")
                    # Agregar resultado de error
                    result = {
                        'index': i,
                        'descripcion': email_text,
                        'subcategoria_original': real_subcategory,
                        'clasificacion_esperada': map_subcategory_to_class(real_subcategory),
                        'clasificacion_predicha': 'NO CLASIFICABLE',
                        'correcto': map_subcategory_to_class(real_subcategory) == 'NO CLASIFICABLE',
                        'timestamp': datetime.now().isoformat()
                    }
                    results.append(result)
            else:
                # Error no relacionado con rate limit
                result = {
                    'index': i,
                    'descripcion': email_text,
                    'subcategoria_original': real_subcategory,
                    'clasificacion_esperada': map_subcategory_to_class(real_subcategory),
                    'clasificacion_predicha': 'NO CLASIFICABLE',  
                    'correcto': map_subcategory_to_class(real_subcategory) == 'NO CLASIFICABLE',
                    'timestamp': datetime.now().isoformat()
                }
                results.append(result)
    
    return results

def save_results(results: list, filename: str):
    """
    Guarda los resultados en un archivo CSV.

    Args:
        results (list): Lista de resultados.
        filename (str): Nombre del archivo CSV.
    """
    if not results:
        print("No hat resultados para guardar.")

    df_results = pd.DataFrame(results)
    df_results.to_csv(filename, index = False, encoding = 'utf-8')
    print(f"Resultados guardados en {filename}")

def generate_report(results: list) -> dict:
    """
    Genera un reporte detallado de los resultados.
    
    Args:
        results (list): Lista de resultados
        
    Returns:
        dict: Diccionario con métricas del reporte
    """
    if not results:
        print("No hay resultados para generar reporte")
        return {}
    
    # Filtrar errores para métricas de precisión (NO CLASIFICABLE no es error)
    valid_results = [r for r in results if r['clasificacion_predicha'] in ['ALTA/BAJA', 'NO CLASIFICABLE']]
    
    # Métricas básicas
    total_processed = len(results)
    total_valid = len(valid_results)
    correct_predictions = sum(1 for r in valid_results if r['correcto'])
    errors = total_processed - total_valid
    
    # Calcular precisión
    accuracy = (correct_predictions / total_valid) if total_valid > 0 else 0
    
    # Contar predicciones por categoría
    predictions_counter = Counter(r['clasificacion_predicha'] for r in valid_results)
    expected_counter = Counter(r['clasificacion_esperada'] for r in valid_results)
    
    # Análisis de errores por categoría
    error_analysis = {}
    confusion_matrix = {}
    
    for result in valid_results:
        expected = result['clasificacion_esperada']
        predicted = result['clasificacion_predicha']
        
        # Matriz de confusión
        key = f"{expected} → {predicted}"
        confusion_matrix[key] = confusion_matrix.get(key, 0) + 1
        
        # Análisis de errores (solo casos incorrectos)
        if not result['correcto']:
            error_analysis[key] = error_analysis.get(key, 0) + 1
    
    # Métricas por categoría (incluyendo NO CLASIFICABLE)
    category_metrics = {}
    categories = ['ALTA/BAJA', 'NO CLASIFICABLE']
    
    for category in categories:
        category_results = [r for r in valid_results if r['clasificacion_esperada'] == category]
        if category_results:
            category_correct = sum(1 for r in category_results if r['correcto'])
            category_metrics[category] = {
                'total': len(category_results),
                'correct': category_correct,
                'accuracy': category_correct / len(category_results)
            }
    
    # Análisis de casos NO CLASIFICABLE
    no_clasificable_analysis = {
        'predicted_as_no_clasificable': len([r for r in valid_results if r['clasificacion_predicha'] == 'NO CLASIFICABLE']),
        'expected_as_no_clasificable': len([r for r in valid_results if r['clasificacion_esperada'] == 'NO CLASIFICABLE']),
        'correctly_identified_uncertain': len([r for r in valid_results if r['clasificacion_esperada'] == 'NO CLASIFICABLE' and r['correcto']])
    }
    
    report_data = {
        'total_processed': total_processed,
        'total_valid': total_valid,
        'errors': errors,
        'correct_predictions': correct_predictions,
        'accuracy': accuracy,
        'predictions_counter': predictions_counter,
        'expected_counter': expected_counter,
        'error_analysis': error_analysis,
        'confusion_matrix': confusion_matrix,
        'category_metrics': category_metrics,
        'no_clasificable_analysis': no_clasificable_analysis
    }
    
    return report_data

def print_report(report_data: dict):
    """
    Imprime el reporte final de manera organizada.
    
    Args:
        report_data (dict): Datos del reporte
    """
    print("\n" + "="*60)
    print("REPORTE FINAL DE BENCHMARK")
    print("="*60)
    
    # Métricas principales
    print(f"Total procesados: {report_data['total_processed']}")
    print(f"Procesados válidos: {report_data['total_valid']}")
    print(f"Errores: {report_data['errors']}")
    print(f"Predicciones correctas: {report_data['correct_predictions']}")
    print(f"PRECISIÓN GENERAL: {report_data['accuracy']:.2%}")
    
    # Distribución de predicciones
    print(f"\nDistribución de predicciones:")
    for category, count in report_data['predictions_counter'].items():
        print(f"  • {category}: {count}")
    
    # Distribución esperada
    print(f"\nDistribución esperada:")
    for category, count in report_data['expected_counter'].items():
        print(f"  • {category}: {count}")
    
    # Métricas por categoría
    if report_data['category_metrics']:
        print(f"\nPrecisión por categoría:")
        for category, metrics in report_data['category_metrics'].items():
            print(f"  • {category}: {metrics['correct']}/{metrics['total']} ({metrics['accuracy']:.2%})")
    
    # Análisis de NO CLASIFICABLE
    if report_data['no_clasificable_analysis']:
        no_class = report_data['no_clasificable_analysis']
        print(f"\nAnálisis de casos NO CLASIFICABLE:")
        print(f"  • Predichos como NO CLASIFICABLE: {no_class['predicted_as_no_clasificable']}")
        print(f"  • Esperados como NO CLASIFICABLE: {no_class['expected_as_no_clasificable']}")
        print(f"  • Correctamente identificados como inciertos: {no_class['correctly_identified_uncertain']}")
    
    # Matriz de confusión
    if report_data['confusion_matrix']:
        print(f"\nMatriz de confusión (todos los casos):")
        for transition, count in report_data['confusion_matrix'].items():
            print(f"  • {transition}: {count}")
    
    # Análisis de errores (solo casos incorrectos)
    if report_data['error_analysis']:
        print(f"\nAnálisis de errores:")
        for error_type, count in report_data['error_analysis'].items():
            print(f"  • {error_type}: {count}")
    
    # Recomendaciones
    print(f"\nRECOMENDACIONES:")
    accuracy = report_data['accuracy']
    no_class = report_data['no_clasificable_analysis']
    
    if accuracy >= 0.9:
        print("  Excelente precisión! El modelo está funcionando muy bien.")
    elif accuracy >= 0.8:
        print("  Buena precisión. Considerar revisar los casos de error más comunes.")
    elif accuracy >= 0.7:
        print("  Precisión moderada. Revisar y mejorar el prompt de clasificación.")
    else:
        print("  Precisión baja. Requiere revisión completa del prompt y ejemplos.")
    
    # Recomendaciones específicas sobre NO CLASIFICABLE
    if no_class['predicted_as_no_clasificable'] > no_class['expected_as_no_clasificable'] * 1.5:
        print("El modelo está siendo muy conservador - muchos casos marcados como NO CLASIFICABLE")
        print("Considera hacer el prompt más específico para reducir la incertidumbre")
    elif no_class['predicted_as_no_clasificable'] < no_class['expected_as_no_clasificable'] * 0.5:
        print("El modelo está siendo muy agresivo - pocos casos marcados como NO CLASIFICABLE")
        print("Considera permitir más casos de incertidumbre para mejorar la precisión")
    
    # Análisis de distribución balanceada
    total_predictions = sum(report_data['predictions_counter'].values())
    if total_predictions > 0:
        alta_baja_pct = report_data['predictions_counter'].get('ALTA/BAJA', 0) / total_predictions
        no_class_pct = report_data['predictions_counter'].get('NO CLASIFICABLE', 0) / total_predictions
        
        if alta_baja_pct > 0.8:
            print("Distribución muy desbalanceada - revisar si hay sesgo en las predicciones")
    
    print("\n" + "="*60)

def main():
    """Función principal que ejecuta el benchmark completo."""
    print("Iniciando Benchmark de Clasificación de Emails")
    print("="*60)

    try:
        # Cargar datos
        df = load_data(CONFIG['excel_file'], CONFIG['sheet_name'], CONFIG['n_limit'])

        # Inicializar controlador de tasa
        rate_limiter = RateLimiter(CONFIG['max_requests_per_minute'])
        
        # Procesar emails
        results = process_emails(df, rate_limiter)
        
        # Guardar resultados
        save_results(results, CONFIG['results_file'])
        
        # Generar y mostrar reporte
        report_data = generate_report(results)
        print_report(report_data)
        
        # Estimación de tiempo
        total_time_minutes = CONFIG['n_limit'] * 20 / 60
        print(f"\nTiempo total estimado para {CONFIG['n_limit']} elementos: {total_time_minutes:.1f} minutos")
        
    except Exception as e:
        print(f"Error fatal en la ejecución: {e}")
        raise

if __name__ == "__main__":
    main()