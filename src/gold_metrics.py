import duckdb
import os
import pandas as pd

def consolidar_camada_gold(input_silver="data/silver/orders_processed.csv", output_dir="data/gold"):
    print("⏳ Iniciando consolidação analítica na Camada Gold (DuckDB)...")
    
    if not os.path.exists(input_silver):
        raise FileNotFoundError(f"Arquivo Silver não encontrado em: {input_silver}")
        
    os.makedirs(output_dir, exist_ok=True)
    
    # Inicializa a conexão do DuckDB em memória (super leve e rápido)
    con = duckdb.connect(database=':memory:')
    
    # Criamos uma view diretamente em cima do arquivo CSV processado da Silver
    con.execute(f"CREATE VIEW view_silver AS SELECT * FROM read_csv_auto('{input_silver}')")
    
    # KPI 1: Consolidação por Rota (O que os Coordenadores de Tráfego olham)
    print("📊 Agregando métricas de performance por rota...")
    query_rotas = """
        SELECT 
            route,
            COUNT(order_id) AS total_pedidos,
            ROUND(AVG(is_ontime) * 100, 2) AS taxa_on_time_pct,
            ROUND(AVG(is_infull) * 100, 2) AS taxa_in_full_pct,
            ROUND(AVG(is_otif) * 100, 2) AS otif_geral_pct,
            ROUND(AVG(lead_time_total), 2) AS lead_time_medio_total_horas,
            ROUND(AVG(lead_time_delivery), 2) AS lead_time_last_mile_horas,
            ROUND(SUM(freight_cost), 2) AS custo_total_frete,
            ROUND(AVG(is_profitable) * 100, 2) AS rotas_lucrativas_pct
        FROM view_silver
        GROUP BY route
        ORDER BY otif_geral_pct DESC
    """
    df_rotas = con.execute(query_rotas).df()
    df_rotas.to_csv(os.path.join(output_dir, "kpi_performance_rotas.csv"), index=False)
    
    # KPI 2: SLA de Tecnologia vs Processo Manual (Para vender o ROI do SaaS)
    print("📊 Comparando eficiência: Automação vs Planilhas Manuais...")
    query_origem = """
        SELECT 
            source_type,
            COUNT(order_id) AS total_pedidos,
            ROUND(AVG(is_otif) * 100, 2) AS otif_medio_pct,
            ROUND(AVG(lead_time_picking), 2) AS tempo_medio_separacao_horas,
            ROUND(AVG(lead_time_shipping), 2) AS tempo_medio_expedicao_horas,
            ROUND(COUNT(CASE WHEN delivered_at IS NULL THEN 1 END) * 100.0 / COUNT(order_id), 2) AS taxa_extravio_ou_pendente_pct
        FROM view_silver
        GROUP BY source_type
    """
    df_origem = con.execute(query_origem).df()
    df_origem.to_csv(os.path.join(output_dir, "kpi_SLA_origem.csv"), index=False)
    
    print(f"✅ Camada Gold gerada com sucesso pelo DuckDB! Arquivos salvos em: {output_dir}/")
    con.close()

if __name__ == "__main__":
    consolidar_camada_gold()
