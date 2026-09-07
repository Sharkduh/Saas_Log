import duckdb
import pandas as pd
import os

def consolidar_camada_gold(input_path="data/silver/orders_processed.csv", 
                           output_rotas="data/gold/kpi_performance_rotas.csv",
                           output_origem="data/gold/kpi_SLA_origem.csv"):
    print("⏳ Iniciando consolidação analítica na Camada Gold (DuckDB)...")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Arquivo Silver não encontrado em: {input_path}")
        
    con = duckdb.connect(database=':memory:')
    df_silver = pd.read_csv(input_path)
    con.register('tabela_silver', df_silver)
    
    os.makedirs(os.path.dirname(output_rotas), exist_ok=True)
    os.makedirs(os.path.dirname(output_origem), exist_ok=True)
    
    # 🌟 Query Otimizada com moldes de conversão estrita de tipos numéricos
    query_rotas = """
        SELECT 
            route,
            COUNT(order_id) AS total_pedidos,
            ROUND(AVG(CAST(is_ontime AS INTEGER)) * 100, 2) AS taxa_on_time_pct,
            ROUND(AVG(CAST(is_infull AS INTEGER)) * 100, 2) AS taxa_in_full_pct,
            ROUND(AVG(CAST(is_otif AS INTEGER)) * 100, 2) AS otif_geral_pct,
            ROUND(AVG(CAST(is_profitable AS INTEGER)) * 100, 2) AS rotas_lucrativas_pct,
            ROUND(AVG(lead_time_picking), 2) AS lead_time_picking_horas,
            ROUND(AVG(lead_time_shipping), 2) AS lead_time_shipping_horas,
            ROUND(AVG(lead_time_delivery), 2) AS lead_time_last_mile_horas,
            ROUND(AVG(lead_time_total), 2) AS lead_time_medio_total_horas,
            SUM(freight_cost) AS custo_total_frete,
            SUM(product_margin) AS margem_total_acumulada
        FROM tabela_silver
        WHERE route IS NOT NULL AND route != 'NAN'
        GROUP BY route
        ORDER BY total_pedidos DESC
    """
    
    query_origem = """
        SELECT 
            source_type,
            COUNT(order_id) AS total_pedidos,
            ROUND(AVG(CAST(is_otif AS INTEGER)) * 100, 2) AS otif_geral_pct,
            ROUND(AVG(lead_time_total), 2) AS lead_time_medio_total_horas,
            ROUND(AVG(lead_time_delivery), 2) AS lead_time_last_mile_horas
        FROM tabela_silver
        GROUP BY source_type
    """
    
    df_gold_rotas = con.execute(query_rotas).df()
    df_gold_origem = con.execute(query_origem).df()
    
    df_gold_rotas.to_csv(output_rotas, index=False)
    df_gold_origem.to_csv(output_origem, index=False)
    
    con.close()
    print("✅ Camada Gold consolidada com sucesso no DuckDB!")
    return df_gold_rotas, df_gold_origem

if __name__ == "__main__":
    consolidar_camada_gold()

