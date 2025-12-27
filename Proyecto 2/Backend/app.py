# backend/app.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import numpy as np
from datetime import datetime
import os

from models.preprocessing import DataPreprocessor
from models.kmeans import KMeans

app = FastAPI(
    title="InsightCluster API",
    description="API para clustering de clientes con K-Means",
    version="1.0.0"
)

# Configurar CORS (permite conexión desde frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Almacenamiento temporal
storage = {}

@app.get("/")
def root():
    """Endpoint de bienvenida"""
    return {
        "message": "Bienvenido a InsightCluster API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "upload": "/upload",
            "train": "/train",
            "results": "/results/{file_id}",
            "download": "/download/{file_id}"
        }
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Subir archivo CSV o Excel para análisis
    """
    try:
        # Validar formato
        filename = file.filename
        if not (filename.endswith('.csv') or filename.endswith(('.xlsx', '.xls'))):
            raise HTTPException(
                status_code=400,
                detail="Formato no soportado. Use CSV o Excel (.xlsx, .xls)"
            )
        
        # Leer archivo
        if filename.endswith('.csv'):
            df = pd.read_csv(file.file)
        else:
            df = pd.read_excel(file.file)
        
        # Validar columnas requeridas
        required_cols = [
            'cliente_id', 'frecuencia_compra', 'monto_total_gastado',
            'canal_principal'
        ]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(
                status_code=400,
                detail=f"Faltan columnas requeridas: {missing_cols}"
            )
        
        # Generar ID único
        file_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar archivo
        filepath = f"data/uploads/{file_id}.csv"
        df.to_csv(filepath, index=False)
        
        # Almacenar información
        storage[file_id] = {
            "filename": filename,
            "filepath": filepath,
            "rows": len(df),
            "columns": list(df.columns),
            "uploaded_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "message": "Archivo cargado correctamente",
            "file_id": file_id,
            "rows": len(df),
            "columns": list(df.columns)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info/{file_id}")
def get_file_info(file_id: str):
    """Obtener información de un archivo cargado"""
    if file_id not in storage:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    return storage[file_id]

@app.post("/train")
def train_model(
    file_id: str,
    n_clusters: int = 3,
    max_iterations: int = 100,
    random_state: int = 42
):
    """
    Entrenar modelo K-Means
    
    Parámetros:
    - file_id: ID del archivo cargado
    - n_clusters: Número de clusters (2-10)
    - max_iterations: Máximo de iteraciones (50-500)
    - random_state: Semilla para reproducibilidad
    """
    try:
        # Validar archivo
        if file_id not in storage:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        # Validar parámetros
        if not 2 <= n_clusters <= 10:
            raise HTTPException(400, "n_clusters debe estar entre 2 y 10")
        
        if not 50 <= max_iterations <= 500:
            raise HTTPException(400, "max_iterations debe estar entre 50 y 500")
        
        # Cargar y preprocesar
        filepath = storage[file_id]["filepath"]
        preprocessor = DataPreprocessor()
        X_scaled, df, feature_names = preprocessor.load_and_clean(filepath)
        
        # Entrenar K-Means
        print(f"\n Entrenando K-Means con {n_clusters} clusters...")
        kmeans = KMeans(
            n_clusters=n_clusters,
            max_iterations=max_iterations,
            random_state=random_state
        )
        labels = kmeans.fit_predict(X_scaled)
        
        # Agregar clusters
        df['cluster'] = labels
        
        # Calcular estadísticas por cluster
        cluster_stats = []
        for cluster_id in range(n_clusters):
            cluster_data = df[df['cluster'] == cluster_id]
            
            stats = {
                "cluster_id": int(cluster_id),
                "size": len(cluster_data),
                "percentage": round(len(cluster_data) / len(df) * 100, 2),
                "characteristics": {}
            }
            
            # Características numéricas
            numeric_features = [
                'frecuencia_compra', 'monto_total_gastado',
                'monto_promedio_compra', 'dias_desde_ultima_compra'
            ]
            
            for feat in numeric_features:
                if feat in cluster_data.columns:
                    stats["characteristics"][feat] = round(cluster_data[feat].mean(), 2)
            
            # Canal principal
            if 'canal_principal' in cluster_data.columns:
                top_channel = cluster_data['canal_principal'].mode()
                if len(top_channel) > 0:
                    stats["canal_principal"] = top_channel.iloc[0]
            
            cluster_stats.append(stats)
        
        # Guardar resultados
        output_path = f"data/exports/{file_id}_clustered.csv"
        df.to_csv(output_path, index=False)
        
        storage[file_id]["results"] = {
            "n_clusters": n_clusters,
            "inertia": float(kmeans.inertia_),
            "labels": labels.tolist(),
            "cluster_stats": cluster_stats,
            "feature_names": feature_names,
            "output_path": output_path,
            "trained_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "message": "Modelo entrenado correctamente",
            "file_id": file_id,
            "n_clusters": n_clusters,
            "inertia": float(kmeans.inertia_),
            "cluster_stats": cluster_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{file_id}")
def get_results(file_id: str):
    """Obtener resultados del clustering"""
    if file_id not in storage:
        raise HTTPException(404, "Archivo no encontrado")
    
    if "results" not in storage[file_id]:
        raise HTTPException(404, "Este archivo no ha sido procesado. Entrene el modelo primero.")
    
    return storage[file_id]["results"]

@app.get("/download/{file_id}")
def download_results(file_id: str):
    """Descargar CSV con resultados"""
    if file_id not in storage:
        raise HTTPException(404, "Archivo no encontrado")
    
    if "results" not in storage[file_id]:
        raise HTTPException(404, "Este archivo no ha sido procesado")
    
    filepath = storage[file_id]["results"]["output_path"]
    
    if not os.path.exists(filepath):
        raise HTTPException(404, "Archivo de resultados no encontrado")
    
    return FileResponse(
        filepath,
        media_type='text/csv',
        filename=f"resultados_{file_id}.csv"
    )

@app.get("/health")
def health_check():
    """Verificar estado de la API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "files_uploaded": len(storage),
        "models_trained": len([f for f in storage.values() if "results" in f])
    }