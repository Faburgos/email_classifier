# import pandas as pd

# # Configuración del archivo
# EXCEL_FILE = "Solicitudes 2025.xlsx"
# SHEET_NAME = "Data"
# COLUMNA_SUBCATEGORIA = "Subcategoria"

# def extraer_subcategorias_unicas(excel_file: str, sheet_name: str, columna: str):
#     try:
#         # Leer archivo
#         df = pd.read_excel(excel_file, sheet_name=sheet_name)
        
#         # Filtrar subcategorías únicas no nulas
#         subcategorias = df[columna].dropna().unique()
        
#         # Ordenar alfabéticamente
#         subcategorias_ordenadas = sorted([s.strip() for s in subcategorias])
        
#         print(f"Subcategorías únicas encontradas ({len(subcategorias_ordenadas)}):\n")
#         for sub in subcategorias_ordenadas:
#             print(f"- {sub}")
    
#     except Exception as e:
#         print(f"Error al leer el archivo: {e}")

# if __name__ == "__main__":
#     extraer_subcategorias_unicas(EXCEL_FILE, SHEET_NAME, COLUMNA_SUBCATEGORIA)

# import pandas as pd
# import json

# # Cargar el Excel
# file_path = "Solicitudes 2025.xlsx"
# sheet_name = "Data"

# # Leer datos
# df = pd.read_excel(file_path, sheet_name=sheet_name)

# # Extraer subcategorías únicas
# subcategorias = df["Subcategoria"].dropna().unique()
# subcategorias = sorted(subcategorias)

# # Crear diccionario base
# SUBCATEGORIA_TO_CLASE = {sub: "POR CLASIFICAR" for sub in subcategorias}

# # Guardar como JSON
# output_file = "subcategorias_dict.json"
# with open(output_file, "w", encoding="utf-8") as f:
#     json.dump(SUBCATEGORIA_TO_CLASE, f, indent=4, ensure_ascii=False)

# print(f"Diccionario generado con {len(SUBCATEGORIA_TO_CLASE)} subcategorías.")
# print(f"Archivo guardado como: {output_file}")

# import pandas as pd

# # Cargar el archivo y hoja
# file_path = "Solicitudes 2025.xlsx"
# sheet_name = "Data"

# # Leer el Excel
# df = pd.read_excel(file_path, sheet_name=sheet_name)

# # Eliminar subcategorías nulas
# df = df.dropna(subset=["Subcategoria"])

# # Contar ocurrencias por subcategoría
# counts = df["Subcategoria"].value_counts().sort_values(ascending=False)

# # Mostrar el total general y top 10
# print(f"\nTotal de filas con subcategoría definida: {len(df)}")
# print(f"\nSubcategorías más frecuentes:")
# print(counts.head(10))

# # Guardar resultado completo
# counts.to_csv("conteo_subcategorias.csv", encoding="utf-8")
# print("\nArchivo 'conteo_subcategorias.csv' generado con el conteo completo.")
























# import time
# import asyncio
# import json
# import statistics
# from datetime import datetime
# from typing import List, Dict, Any
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import csv
# from classifier import classify_email
# from prompt_examples import EXAMPLES

# class EmailClassifierBenchmark:
#     def __init__(self):
#         self.results = []
#         self.errors = []
#         self.start_time = None
#         self.end_time = None
        
#     def prepare_test_data(self, num_samples: int = 100) -> List[str]:
#         """Prepara datos de prueba usando los ejemplos y variaciones"""
#         test_emails = []
        
#         # Usar ejemplos existentes
#         base_emails = [example['Descripción'] for example in EXAMPLES]
        
#         # Replicar ejemplos hasta llegar al número deseado
#         while len(test_emails) < num_samples:
#             test_emails.extend(base_emails)
        
#         return test_emails[:num_samples]
    
#     def single_classification_test(self, email_body: str, test_id: int) -> Dict[str, Any]:
#         """Ejecuta una sola clasificación y mide métricas"""
#         start_time = time.time()
        
#         try:
#             classification = classify_email(email_body)
#             end_time = time.time()
            
#             result = {
#                 'test_id': test_id,
#                 'email_body': email_body[:100] + '...' if len(email_body) > 100 else email_body,
#                 'classification': classification,
#                 'response_time': end_time - start_time,
#                 'success': True,
#                 'timestamp': datetime.now().isoformat(),
#                 'error': None
#             }
            
#         except Exception as e:
#             end_time = time.time()
#             result = {
#                 'test_id': test_id,
#                 'email_body': email_body[:100] + '...' if len(email_body) > 100 else email_body,
#                 'classification': None,
#                 'response_time': end_time - start_time,
#                 'success': False,
#                 'timestamp': datetime.now().isoformat(),
#                 'error': str(e)
#             }
#             self.errors.append(result)
        
#         return result
    
#     def concurrent_benchmark(self, test_emails: List[str], max_workers: int = 5) -> Dict[str, Any]:
#         """Ejecuta pruebas concurrentes para medir throughput"""
#         print(f"Iniciando benchmark concurrente con {len(test_emails)} emails y {max_workers} workers...")
        
#         self.start_time = time.time()
        
#         with ThreadPoolExecutor(max_workers=max_workers) as executor:
#             # Enviar todas las tareas
#             future_to_id = {
#                 executor.submit(self.single_classification_test, email, i): i 
#                 for i, email in enumerate(test_emails)
#             }
            
#             # Recoger resultados
#             for future in as_completed(future_to_id):
#                 result = future.result()
#                 self.results.append(result)
                
#                 # Mostrar progreso
#                 if len(self.results) % 10 == 0:
#                     print(f"Completado: {len(self.results)}/{len(test_emails)}")
        
#         self.end_time = time.time()
        
#         return self.calculate_metrics()
    
#     def sequential_benchmark(self, test_emails: List[str]) -> Dict[str, Any]:
#         """Ejecuta pruebas secuenciales para medir precisión"""
#         print(f"Iniciando benchmark secuencial con {len(test_emails)} emails...")
        
#         self.start_time = time.time()
        
#         for i, email in enumerate(test_emails):
#             result = self.single_classification_test(email, i)
#             self.results.append(result)
            
#             if (i + 1) % 10 == 0:
#                 print(f"Completado: {i + 1}/{len(test_emails)}")
        
#         self.end_time = time.time()
        
#         return self.calculate_metrics()
    
#     def calculate_metrics(self) -> Dict[str, Any]:
#         """Calcula métricas de rendimiento"""
#         if not self.results:
#             return {"error": "No hay resultados para calcular métricas"}
        
#         # Filtrar resultados exitosos
#         successful_results = [r for r in self.results if r['success']]
#         response_times = [r['response_time'] for r in successful_results]
        
#         total_duration = self.end_time - self.start_time
        
#         # Calcular métricas de precisión
#         accuracy_metrics = self.calculate_accuracy()
        
#         metrics = {
#             'test_summary': {
#                 'total_requests': len(self.results),
#                 'successful_requests': len(successful_results),
#                 'failed_requests': len(self.errors),
#                 'success_rate': len(successful_results) / len(self.results) * 100,
#                 'total_duration_seconds': total_duration,
#             },
#             'performance_metrics': {
#                 'requests_per_second': len(self.results) / total_duration,
#                 'requests_per_minute': (len(self.results) / total_duration) * 60,
#                 'avg_response_time': statistics.mean(response_times) if response_times else 0,
#                 'median_response_time': statistics.median(response_times) if response_times else 0,
#                 'min_response_time': min(response_times) if response_times else 0,
#                 'max_response_time': max(response_times) if response_times else 0,
#                 'std_response_time': statistics.stdev(response_times) if len(response_times) > 1 else 0,
#             },
#             'accuracy_metrics': accuracy_metrics,
#             'error_analysis': {
#                 'error_count': len(self.errors),
#                 'error_types': self.categorize_errors(),
#                 'error_rate': len(self.errors) / len(self.results) * 100
#             }
#         }
        
#         return metrics
    
#     def calculate_accuracy(self) -> Dict[str, Any]:
#         """Calcula métricas de precisión basadas en ejemplos conocidos"""
#         if not self.results:
#             return {}
        
#         # Crear mapeo de emails a clasificaciones esperadas
#         expected_classifications = {
#             example['Descripción']: example['Clasificación'] 
#             for example in EXAMPLES
#         }
        
#         correct_predictions = 0
#         total_predictions = 0
#         classification_distribution = {}
        
#         for result in self.results:
#             if result['success'] and result['classification']:
#                 total_predictions += 1
                
#                 # Contar distribución de clasificaciones
#                 classification = result['classification']
#                 classification_distribution[classification] = classification_distribution.get(classification, 0) + 1
                
#                 # Verificar si la predicción es correcta (solo para ejemplos conocidos)
#                 original_email = next(
#                     (email for email in expected_classifications.keys() 
#                      if email in result['email_body']), 
#                     None
#                 )
                
#                 if original_email:
#                     expected = expected_classifications[original_email]
#                     if classification == expected:
#                         correct_predictions += 1
        
#         accuracy = (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0
        
#         return {
#             'accuracy_percentage': accuracy,
#             'correct_predictions': correct_predictions,
#             'total_predictions': total_predictions,
#             'classification_distribution': classification_distribution
#         }
    
#     def categorize_errors(self) -> Dict[str, int]:
#         """Categoriza los tipos de errores"""
#         error_types = {}
        
#         for error in self.errors:
#             error_msg = error['error']
            
#             if 'rate limit' in error_msg.lower():
#                 error_types['rate_limit'] = error_types.get('rate_limit', 0) + 1
#             elif 'timeout' in error_msg.lower():
#                 error_types['timeout'] = error_types.get('timeout', 0) + 1
#             elif 'connection' in error_msg.lower():
#                 error_types['connection'] = error_types.get('connection', 0) + 1
#             else:
#                 error_types['other'] = error_types.get('other', 0) + 1
        
#         return error_types
    
#     def save_results(self, filename: str = None):
#         """Guarda los resultados en archivos"""
#         if not filename:
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             filename = f"benchmark_results_{timestamp}"
        
#         # Guardar resultados detallados en JSON
#         with open(f"{filename}.json", 'w', encoding='utf-8') as f:
#             json.dump({
#                 'results': self.results,
#                 'errors': self.errors,
#                 'metrics': self.calculate_metrics()
#             }, f, indent=2, ensure_ascii=False)
        
#         # Guardar resumen en CSV
#         with open(f"{filename}_summary.csv", 'w', newline='', encoding='utf-8') as f:
#             writer = csv.DictWriter(f, fieldnames=['test_id', 'email_body', 'classification', 'response_time', 'success', 'timestamp', 'error'])
#             writer.writeheader()
#             writer.writerows(self.results)
        
#         print(f"Resultados guardados en {filename}.json y {filename}_summary.csv")
    
#     def print_summary(self):
#         """Imprime un resumen de las métricas"""
#         metrics = self.calculate_metrics()
        
#         print("\n" + "="*60)
#         print("RESUMEN DEL BENCHMARK")
#         print("="*60)
        
#         print(f"\n📊 RESUMEN GENERAL:")
#         print(f"  • Total de requests: {metrics['test_summary']['total_requests']}")
#         print(f"  • Requests exitosos: {metrics['test_summary']['successful_requests']}")
#         print(f"  • Requests fallidos: {metrics['test_summary']['failed_requests']}")
#         print(f"  • Tasa de éxito: {metrics['test_summary']['success_rate']:.2f}%")
#         print(f"  • Duración total: {metrics['test_summary']['total_duration_seconds']:.2f} segundos")
        
#         print(f"\n⚡ MÉTRICAS DE RENDIMIENTO:")
#         print(f"  • Requests por segundo: {metrics['performance_metrics']['requests_per_second']:.2f}")
#         print(f"  • Requests por minuto: {metrics['performance_metrics']['requests_per_minute']:.2f}")
#         print(f"  • Tiempo de respuesta promedio: {metrics['performance_metrics']['avg_response_time']:.3f}s")
#         print(f"  • Tiempo de respuesta mediano: {metrics['performance_metrics']['median_response_time']:.3f}s")
#         print(f"  • Tiempo mínimo: {metrics['performance_metrics']['min_response_time']:.3f}s")
#         print(f"  • Tiempo máximo: {metrics['performance_metrics']['max_response_time']:.3f}s")
        
#         print(f"\n🎯 MÉTRICAS DE PRECISIÓN:")
#         print(f"  • Precisión: {metrics['accuracy_metrics']['accuracy_percentage']:.2f}%")
#         print(f"  • Predicciones correctas: {metrics['accuracy_metrics']['correct_predictions']}")
#         print(f"  • Total predicciones: {metrics['accuracy_metrics']['total_predictions']}")
        
#         print(f"\n📈 DISTRIBUCIÓN DE CLASIFICACIONES:")
#         for classification, count in metrics['accuracy_metrics']['classification_distribution'].items():
#             print(f"  • {classification}: {count}")
        
#         if metrics['error_analysis']['error_count'] > 0:
#             print(f"\n❌ ANÁLISIS DE ERRORES:")
#             print(f"  • Total errores: {metrics['error_analysis']['error_count']}")
#             print(f"  • Tasa de error: {metrics['error_analysis']['error_rate']:.2f}%")
#             for error_type, count in metrics['error_analysis']['error_types'].items():
#                 print(f"  • {error_type}: {count}")


# def main():
#     """Función principal para ejecutar el benchmark"""
#     benchmark = EmailClassifierBenchmark()
    
#     print("🚀 BENCHMARK DE CLASIFICADOR DE EMAILS")
#     print("="*50)
    
#     # Configuración del test
#     num_samples = 20  # Ajusta según necesites
#     max_workers = 2   # Ajusta según tu rate limit actual
    
#     # Preparar datos de prueba
#     test_emails = benchmark.prepare_test_data(num_samples)
    
#     # Ejecutar benchmark concurrente
#     print(f"\n1. Ejecutando benchmark concurrente...")
#     concurrent_metrics = benchmark.concurrent_benchmark(test_emails, max_workers)
    
#     # Imprimir resumen
#     benchmark.print_summary()
    
#     # Guardar resultados
#     benchmark.save_results()
    
#     return benchmark

# if __name__ == "__main__":
#     # Ejecutar el benchmark
#     benchmark_instance = main()
    
#     print("\n✅ Benchmark completado!")
#     print("Los resultados han sido guardados en archivos JSON y CSV.")