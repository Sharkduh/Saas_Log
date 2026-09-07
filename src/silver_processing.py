import pandas as pd
import numpy as np
import os

def processar_camada_silver(input_path="data/bronze/orders_raw.csv", output_path="data/silver/orders_processed.csv"):
    print("⏳ Iniciando processamento da Camada Silver (Pandas)...")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo Bronze não encontrado em: {input_path}")
        
    df = pd.read_csv(input_path)
    
    # 🌟 Garante a existência e tipagem limpa da coluna de controle de auditoria
    if 'source_type' not in df.columns:
        df['source_type'] = 'UPLOAD_MANUAL'
    df['source_type'] = df['source_type'].astype(str)
    
    # 🌟 Converte datas forçadamente com tratamento de anomalias textuais
    colunas_data = ["created_at", "picked_at", "shipped_at", "promised_date", "delivered_at"]
    for col in colunas_data:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        
    # Limpeza de registros corrompidos (Viagem no tempo)
    try:
        dados_corrompidos = df['delivered_at'].lt(df['created_at'])
        if dados_corrompidos.any():
            df.loc[dados_corrompidos, 'delivered_at'] = pd.NaT
    except Exception as e:
        print(f"⚠️ Aviso na limpeza de datas: {e}")

    # Cálculos granulares de Lead Times em horas
    df['lead_time_picking'] = (df['picked_at'] - df['created_at']).dt.total_seconds() / 3600
    df['lead_time_shipping'] = (df['shipped_at'] - df['picked_at']).dt.total_seconds() / 3600
    df['lead_time_delivery'] = (df['delivered_at'] - df['shipped_at']).dt.total_seconds() / 3600
    df['lead_time_total'] = (df['delivered_at'] - df['created_at']).dt.total_seconds() / 3600

    # Arredonda e remove valores nulos gerados por pedidos ainda em trânsito
    for col in ['lead_time_picking', 'lead_time_shipping', 'lead_time_delivery', 'lead_time_total']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).round(2)

    # 🌟 Regras de Negócio de Supply Chain Convertidas Explicitamente para Inteiros
    df['is_ontime'] = np.where(df['delivered_at'].notna() & (df['delivered_at'] <= df['promised_date']), 1, 0)
    
    if 'is_infull' in df.columns:
        df['is_infull'] = pd.to_numeric(df['is_infull'], errors='coerce').fillna(1).astype(int)
    else:
        df['is_infull'] = 1
        
    df['is_otif'] = np.where((df['is_ontime'] == 1) & (df['is_infull'] == 1), 1, 0)
    
    for col in ['product_margin', 'freight_cost']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
    df['is_profitable'] = np.where(df['product_margin'] > df['freight_cost'], 1, 0)
    
    # 🌟 GARANTIA ABSOLUTA DE TIPOS PARA O DUCKDB
    df['is_ontime'] = df['is_ontime'].astype(int)
    df['is_infull'] = df['is_infull'].astype(int)
    df['is_otif'] = df['is_otif'].astype(int)
    df['is_profitable'] = df['is_profitable'].astype(int)
    df['route'] = df['route'].astype(str).str.strip().str.upper()
    
    # Gravação física do arquivo processado
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Camada Silver está blindada e salva com sucesso!")
    return df

if __name__ == "__main__":
    processar_camada_silver()
