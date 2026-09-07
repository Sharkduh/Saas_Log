from airflow.models.dag import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os
import pandas as pd
import numpy as np

# Garante que o Airflow consiga enxergar a pasta 'src' na raiz do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importando apenas as camadas que vêm de fora deste script
from src.silver_processing import processar_camada_silver
from src.gold_metrics import consolidar_camada_gold

def gerar_dados_logistica_hibrida(num_pedidos=60000):
    np.random.seed(42)
    tipos_origem = ["API_SISTEMA", "PLANILHA_MANUAL"]
    pesos_origem = [0.75, 0.25]
    rotas = ["SP-CAPITAL", "SP-INTERIOR", "RJ-CAPITAL", "MG-BH", "PR-CURITIBA", "NE-RECIFE"]
    dados = []
    data_base = datetime(2026, 8, 1)
    
    print(f"⏳ Gerando {num_pedidos} registros de logística híbrida...")
    
    for i in range(num_pedidos):
        origem = np.random.choice(tipos_origem, p=pesos_origem)
        order_id = f"LOGX-{100000 + i}" if origem == "API_SISTEMA" else f"PED-{5000 + i}"
        
        criado_em = data_base + timedelta(
            days=int(np.random.randint(0, 30)), 
            hours=int(np.random.randint(7, 22)),
            minutes=int(np.random.randint(0, 59))
        )
        
        horas_picking = np.random.randint(1, 4) if origem == "API_SISTEMA" else np.random.randint(4, 24)
        separado_em = criado_em + timedelta(hours=int(horas_picking), minutes=int(np.random.randint(0, 59)))
        
        hours_shipping = np.random.randint(2, 8) if origem == "API_SISTEMA" else np.random.randint(6, 48)
        expedido_em = separado_em + timedelta(hours=int(hours_shipping), minutes=int(np.random.randint(0, 59)))
        
        prazo_dias = np.random.choice([1, 2, 5], p=[0.5, 0.4, 0.1])
        prometido_para = (criado_em + timedelta(days=int(prazo_dias))).replace(hour=20, minute=0, second=0)
        
        taxa_atraso = 0.15 if origem == "PLANILHA_MANUAL" else 0.05
        com_atraso = np.random.rand() < taxa_atraso
        
        if com_atraso:
            entregue_em = prometido_para + timedelta(days=int(np.random.randint(1, 4)), hours=int(np.random.randint(1, 8)))
        else:
            entregue_em = expedido_em + timedelta(days=int(np.random.randint(0, max(1, prazo_dias-1))), hours=int(np.random.randint(1, 12)))
            if entregue_em > prometido_para:
                entregue_em = prometido_para - timedelta(hours=int(np.random.randint(1, 4)))
        
        taxa_erro_item = 0.08 if origem == "PLANILHA_MANUAL" else 0.02
        in_full = int(np.random.rand() > taxa_erro_item)
        
        if origem == "PLANILHA_MANUAL":
            rand_erro = np.random.rand()
            if rand_erro < 0.02: 
                entregue_em = None
            elif rand_erro < 0.04: 
                entregue_em = criado_em - timedelta(days=2)
        else:
            if np.random.rand() < 0.01: 
                entregue_em = None
            
        dados.append({
            "order_id": order_id, "source_type": origem, "route": np.random.choice(rotas),
            "created_at": criado_em, "picked_at": separado_em, "shipped_at": expedido_em,
            "promised_date": prometido_para, "delivered_at": entregue_em, "is_infull": in_full,
            "freight_cost": round(float(np.random.uniform(18.0, 75.0)), 2), 
            "product_margin": round(float(np.random.uniform(40.0, 250.0)), 2)
        })
        
    df = pd.DataFrame(dados)
    os.makedirs("data/bronze", exist_ok=True)
    df.to_csv("data/bronze/orders_raw.csv", index=False)
    print(f"✅ Camada Bronze populada com sucesso!")

# Wrappers oficiais das tarefas do Airflow
def run_bronze():
    gerar_dados_logistica_hibrida(num_pedidos=60000)

def run_silver():
    processar_camada_silver()

def run_gold():
    consolidar_camada_gold()

default_args = {
    'owner': 'lion92185',
    'depends_on_past': False,
    'start_date': datetime(2026, 9, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'fulfillment_last_mile_pipeline',
    default_args=default_args,
    description='Pipeline de dados ponta a ponta',
    schedule='0 2 * * *',  # Padrão correto do Airflow 3 (sem o _interval)
    catchup=False,
) as dag:

    task_bronze = PythonOperator(task_id='ingestao_bronze_simulada', python_callable=run_bronze)
    task_silver = PythonOperator(task_id='processamento_kpis_silver', python_callable=run_silver)
    task_gold = PythonOperator(task_id='consolidacao_analytics_gold', python_callable=run_gold)

    task_bronze >> task_silver >> task_gold

if __name__ == "__main__":
    gerar_dados_logistica_hibrida()
