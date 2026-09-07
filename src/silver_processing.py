import pandas as pd
import numpy as np
import os

def processar_camada_silver(input_path="data/bronze/orders_raw.csv", output_path="data/silver/orders_processed.csv"):
    print("⏳ Iniciando processamento da Camada Silver (Pandas)...")
    
    # 1. Carregar os dados da Bronze
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo Bronze não encontrado em: {input_path}")
        
    df = pd.read_csv(input_path)
    
    # 🌟 Garante que a coluna source_type seja sempre propagada de forma segura para o DuckDB
    if 'source_type' not in df.columns:
        df['source_type'] = 'UPLOAD_MANUAL'
    
    # 2. Conversão forçada absoluta de dados textuais para Datetime
    colunas_data = ["created_at", "picked_at", "shipped_at", "promised_date", "delivered_at"]
    for col in colunas_data:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        
    # 3. Limpeza de Dados à prova de falhas (Data Cleansing)
    # Usamos o método nativo .lt() (Less Than) para evitar quebras de str vs ndarray
    try:
        dados_corrompidos = df['delivered_at'].lt(df['created_at'])
        if dados_corrompidos.any():
            print(f"⚠️ Detectados {dados_corrompidos.sum()} registros com datas corrompidas (Viagem no tempo). Tratando dados...")
            df.loc[dados_corrompidos, 'delivered_at'] = pd.NaT
    except Exception as e:
        print(f"⚠️ Aviso na limpeza de datas: {e}. Prosseguindo com fallback.")

    # 4. Cálculo de Lead Times (em horas)
    df['lead_time_picking'] = (df['picked_at'] - df['created_at']).dt.total_seconds() / 3600
    df['lead_time_shipping'] = (df['shipped_at'] - df['picked_at']).dt.total_seconds() / 3600
    df['lead_time_delivery'] = (df['delivered_at'] - df['shipped_at']).dt.total_seconds() / 3600
    df['lead_time_total'] = (df['delivered_at'] - df['created_at']).dt.total_seconds() / 3600

    # Arredonda e limpa nulos de pedidos que ainda estão pendentes
    for col in ['lead_time_picking', 'lead_time_shipping', 'lead_time_delivery', 'lead_time_total']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).round(2)

    # 5. Regras de Negócio para Métricas (On-Time e OTIF)
    df['is_ontime'] = np.where(
        df['delivered_at'].notna() & (df['delivered_at'] <= df['promised_date']), 
        1, 
        0
    )
    
    df['is_otif'] = np.where(
        (df['is_ontime'] == 1) & (df['is_infull'] == 1), 
        1, 
        0
    )
    
    # Tratamento de segurança para colunas financeiras
    for col in ['product_margin', 'freight_cost']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
    df['is_profitable'] = np.where(df['product_margin'] > df['freight_cost'], 1, 0)
    
    # 6. Salvar na Camada Silver
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Camada Silver processada com sucesso! Salva em: {output_path}")
    return df

if __name__ == "__main__":
    processar_camada_silver()
