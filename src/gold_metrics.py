import duckdb
import pandas as pd
import os

def consolidar_camada_gold(input_path="data/silver/orders_processed.csv", 
                           output_rotas="data/gold/kpi_performance_rotas.csv",
                           output_origem="data/gold/kpi_SLA_origem.csv"):
    print("⏳ Iniciando consolidação analítica na Camada Gold (DuckDB)...")
    
    # 1. Validação de segurança da origem
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo Silver não encontrado em: {input_path}")
        
    # Conectamos ao DuckDB em memória de alta performance
    con = duckdb.connect(database=':memory:')
    
    # 2. Carrega a tabela Silver diretamente para o ecossistema DuckDB
    df_silver = pd.read_csv(input_path)
    con.register('tabela_silver', df_silver)
    
    # Certifica criação dos diretórios da camada Gold
    os.makedirs(os.path.dirname(output_rotas), exist_ok=True)
    os.makedirs(os.path.dirname(output_origem), exist_ok=True)
    
    # 📊 MATRIZ 1: KPIs consolidados por Rota/Região (Eixos dos Gráficos principais)
    # 🌟 BLINDAGEM APLICADA: CAST explícito para evitar falhas de VARCHAR
    query_rotas = """
        SELECT 
            route,
            COUNT(order_id) AS total_pedidos,
            ROUND(AVG(CAST(is_ontime AS INT)) * 100, 2) AS taxa_on_time_pct,
            ROUND(AVG(CAST(is_infull AS INT)) * 100, 2) AS taxa_in_full_pct,
            ROUND(AVG(CAST(is_otif AS INT)) * 100, 2) AS otif_geral_pct,
            ROUND(AVG(CAST(is_profitable AS INT)) * 100, 2) AS rotas_lucrativas_pct,
            ROUND(AVG(lead_time_picking), 2) AS lead_time_picking_horas,
            ROUND(AVG(lead_time_shipping), 2) AS lead_time_shipping_horas,
            ROUND(AVG(lead_time_delivery), 2) AS lead_time_last_mile_horas,
            ROUND(AVG(lead_time_total), 2) AS lead_time_medio_total_horas,
            SUM(freight_cost) AS custo_total_frete,
            SUM(product_margin) AS margem_total_acumulada
        FROM tabela_silver
        WHERE route IS NOT NULL
        GROUP BY route
        ORDER BY total_pedidos DESC
    """
    
    # 📊 MATRIZ 2: KPIs agregados por Maturidade Tecnológica (API vs Manual)
    query_origem = """
        SELECT 
            source_type,
            COUNT(order_id) AS total_pedidos,
            ROUND(AVG(CAST(is_otif AS INT)) * 100, 2) AS otif_geral_pct,
            ROUND(AVG(lead_time_total), 2) AS lead_time_medio_total_horas,
            ROUND(AVG(lead_time_delivery), 2) AS lead_time_last_mile_horas
        FROM tabela_silver
        GROUP BY source_type
    """
    
    # Executa as Queries e converte os cursores SQL direto para DataFrames do Pandas
    df_gold_rotas = con.execute(query_rotas).df()
    df_gold_origem = con.execute(query_origem).df()
    
    # 3. Gravação das matrizes em arquivos estáveis para o consumo do Streamlit
    df_gold_rotas.to_csv(output_rotas, index=False)
    df_gold_origem.to_csv(output_origem, index=False)
    
    # Fecha a conexão em memória de forma limpa
    con.close()
    print("✅ Camada Gold consolidada e atualizada com sucesso no DuckDB!")
    return df_gold_rotas, df_gold_origem

if __name__ == "__main__":
    consolidar_camada_gold()
