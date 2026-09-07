import pytest
import pandas as pd
import numpy as np
import os
from src.silver_processing import processar_camada_silver

# Fixture para criar um cenário de dados simulado com os erros típicos
@pytest.fixture
def base_test_csv(tmp_path):
    csv_file = tmp_path / "orders_test_raw.csv"
    
    # Criando 4 cenários críticos que testam os limites da nossa regra de negócio
    dados_teste = [
        {
            "order_id": "LOGX-101", # 1. Pedido perfeito e no prazo
            "source_type": "API_SISTEMA",
            "route": "SP-CAPITAL",
            "created_at": "2026-09-01 10:00:00",
            "picked_at": "2026-09-01 11:00:00",
            "shipped_at": "2026-09-01 13:00:00",
            "promised_date": "2026-09-02 20:00:00",
            "delivered_at": "2026-09-01 18:00:00",
            "is_infull": 1,
            "freight_cost": 20.0,
            "product_margin": 50.0
        },
        {
            "order_id": "PED-502", # 2. Pedido de Planilha com Erro de Digitação (Viajou no tempo)
            "source_type": "PLANILHA_MANUAL",
            "route": "RJ-CAPITAL",
            "created_at": "2026-09-01 10:00:00",
            "picked_at": "2026-09-01 12:00:00",
            "shipped_at": "2026-09-01 15:00:00",
            "promised_date": "2026-09-03 20:00:00",
            "delivered_at": "2026-08-30 08:00:00", # Erro: entregue ANTES de ser criado
            "is_infull": 1,
            "freight_cost": 25.0,
            "product_margin": 60.0
        },
        {
            "order_id": "LOGX-103", # 3. Pedido com atraso (Não é On-Time, logo não é OTIF)
            "source_type": "API_SISTEMA",
            "route": "SP-INTERIOR",
            "created_at": "2026-09-01 10:00:00",
            "picked_at": "2026-09-01 11:00:00",
            "shipped_at": "2026-09-01 14:00:00",
            "promised_date": "2026-09-02 20:00:00",
            "delivered_at": "2026-09-03 10:00:00", # Atrasou quase um dia inteiro
            "is_infull": 1,
            "freight_cost": 30.0,
            "product_margin": 45.0
        },
        {
            "order_id": "PED-504", # 4. Pedido Pendente/Extraviado (Data de entrega nula)
            "source_type": "PLANILHA_MANUAL",
            "route": "MG-BH",
            "created_at": "2026-09-01 10:00:00",
            "picked_at": "2026-09-01 15:00:00",
            "shipped_at": "2026-09-02 09:00:00",
            "promised_date": "2026-09-04 20:00:00",
            "delivered_at": None, # Em trânsito ou perdido
            "is_infull": 0,
            "freight_cost": 40.0,
            "product_margin": 35.0 # Margem menor que frete (Prejuízo)
        }
    ]
    
    df = pd.DataFrame(dados_teste)
    df.to_csv(csv_file, index=False)
    return csv_file, tmp_path / "orders_test_processed.csv"

# TESTE 1: Garantir que datas corrompidas de planilhas são limpas e viram nulas (NaT)
def test_limpeza_datas_corrompidas(base_test_csv):
    input_path, output_path = base_test_csv
    df_silver = processar_camada_silver(input_path, output_path)
    
    # O pedido PED-502 viajou no tempo, o entregue_em precisa virar nulo (NaT)
    pedido_erro = df_silver[df_silver['order_id'] == 'PED-502'].iloc[0]
    assert pd.isna(pedido_erro['delivered_at']), "❌ Falha: A data corrompida deveria ter sido convertida para NaT!"

# TESTE 2: Validar o cálculo preciso do OTIF
def test_calculo_otif(base_test_csv):
    input_path, output_path = base_test_csv
    df_silver = processar_camada_silver(input_path, output_path)
    
    # LOGX-101: No prazo e completo -> Deve ser OTIF (1)
    p_perfeito = df_silver[df_silver['order_id'] == 'LOGX-101'].iloc[0]
    assert p_perfeito['is_otif'] == 1, "❌ Falha: Pedido perfeito deveria ser considerado OTIF=1"
    
    # LOGX-103: Atrasado -> Não pode ser OTIF (0)
    p_atrasado = df_silver[df_silver['order_id'] == 'LOGX-103'].iloc[0]
    assert p_atrasado['is_otif'] == 0, "❌ Falha: Pedido atrasado não pode ter OTIF=1"

# TESTE 3: Validar análise financeira (Rotas dando prejuízo)
def test_analise_lucratividade(base_test_csv):
    input_path, output_path = base_test_csv
    df_silver = processar_camada_silver(input_path, output_path)
    
    # PED-504: Custo de frete (40) maior que a margem (35) -> Não lucrativo (0)
    p_prejuizo = df_silver[df_silver['order_id'] == 'PED-504'].iloc[0]
    assert p_prejuizo['is_profitable'] == 0, "❌ Falha: Pedido com frete maior que a margem deve ser is_profitable=0"
