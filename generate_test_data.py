"""
generate_test_data.py -- Generador de datos de prueba para testing.
CONSERVAR PAGA -- Dashboard de Control Financiero

Ejecutar: python generate_test_data.py
Crea un archivo Excel con datos ficticios que respeta la estructura
esperada por el dashboard, sin usar datos reales del cliente.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)


def generate_test_excel(output_path="datos_prueba.xlsx"):
    """Genera un Excel con datos ficticios para testing del dashboard."""

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:

        # ===== INF PAGOS =====
        proveedores = [
            'EMPRESA DEMO S.A.S.', 'CONSULTOR PRUEBA LTDA',
            'SERVICIOS AMBIENTALES DEMO', 'CONTRATISTA EJEMPLO',
            'LABORATORIO TEST S.A.', 'ASESORIA DEMO CORP',
            'TRANSPORTE PRUEBA S.A.', 'INSUMOS DEMO LTDA',
        ]
        conceptos = ['CONTRATISTAS P. NATURAL', 'CONTRATISTAS P. JURIDICA',
                      'IMPUESTOS', 'COMISION BANCARIA', 'GASTOS DE VIAJE']
        n_rows = 50
        fechas = [datetime(2024, 7, 1) + timedelta(days=int(np.random.randint(0, 540))) for _ in range(n_rows)]

        df_pagos = pd.DataFrame({
            'Descripcion Proveedor': np.random.choice(proveedores, n_rows),
            'Valor Bruto': np.random.uniform(500000, 15000000, n_rows).round(0),
            'Iva': np.random.uniform(0, 500000, n_rows).round(0),
            'Valor ReteIva': np.random.uniform(0, 100000, n_rows).round(0),
            'Valor ReteFuente': np.random.uniform(0, 300000, n_rows).round(0),
            'Valor ReteIca': np.random.uniform(0, 50000, n_rows).round(0),
            'Valor Neto': 0,
            'No.Beneficiario': [str(np.random.randint(100000, 999999)) for _ in range(n_rows)],
            'Fecha de Pago': fechas,
            'Proyecto': 'Proyecto Demo Ambiental',
            'CONCEPTO': np.random.choice(conceptos, n_rows),
            'Ano': [f.year for f in fechas],
            'Mes': [f.month for f in fechas],
        })
        df_pagos['Valor Neto'] = (df_pagos['Valor Bruto'] + df_pagos['Iva']
                                   - df_pagos['Valor ReteFuente']
                                   - df_pagos['Valor ReteIva']
                                   - df_pagos['Valor ReteIca'])
        df_pagos.to_excel(writer, sheet_name='INF PAGOS', index=False)

        # ===== GASTOS CP (matching real structure) =====
        # Uses the DESCRIPCION format: A. PERSONAL, B. PAGO DE INCENTIVOS, etc.
        gastos_cp_data = [
            ['DESCRIPCION', 'PRESUPUESTO', '', '', '', ''],
            ['A. PERSONAL', 93500000, '', '', '', ''],
            ['TOTAL COSTOS DE PERSONAL', 93500000, '', '', '', ''],
            ['B. PAGO DE INCENTIVOS', 560000000, '', '', '', ''],
            ['TOTAL INCENTIVOS', 560000000, '', '', '', ''],
            ['C. PAGO SERVICIOS BANCARIOS', 21500000, '', '', '', ''],
            ['TOTAL COSTOS SERVICIOS BANCARIOS', 21500000, '', '', '', ''],
            ['D. PAGO A DINAMIZADORES', 45000000, '', '', '', ''],
            ['TOTAL DINAMIZADORES', 45000000, '', '', '', ''],
            ['E. PAGO DE VIATICOS', 18000000, '', '', '', ''],
            ['TOTAL VIATICOS', 18000000, '', '', '', ''],
            ['F. PAGO DE IMPUESTOS', 12000000, '', '', '', ''],
            ['VALOR IMPUESTOS', 12000000, '', '', '', ''],
            ['TOTAL GASTOS DEL PROYECTO', 750000000, '', '', '', ''],
        ]
        df_gastos = pd.DataFrame(gastos_cp_data)
        df_gastos.to_excel(writer, sheet_name='GASTOS CP', index=False, header=False)

        # ===== INGRESOS CP =====
        ingresos_header = pd.DataFrame([['', '', ''], ['', '', ''], ['', '', '']])
        df_ingresos = pd.DataFrame({
            'Fecha': [datetime(2024, 7, 15), datetime(2024, 10, 20), datetime(2025, 1, 10), datetime(2025, 6, 1)],
            'CONCEPTO': ['Transferencia inicial', 'Segundo desembolso', 'Tercer desembolso', 'Cuarto desembolso'],
            'VALOR': [2500000000, 1800000000, 1200000000, 700000000],
        })
        combined = pd.concat([ingresos_header, df_ingresos], ignore_index=True)
        combined.to_excel(writer, sheet_name='INGRESOS CP', index=False, header=False)

        # ===== INCENTIVOS =====
        incentivos_header = pd.DataFrame([['', '', '', ''], ['', '', '', ''], ['', '', '', '']])
        df_incentivos = pd.DataFrame({
            'PAGO INCENTIVOS': [f'Ciclo {i}' for i in range(1, 6)],
            'FECHA DE PAGO': [datetime(2024, 8, 1) + timedelta(days=60 * i) for i in range(5)],
            'VALOR PAGO TOTAL': np.random.uniform(5000000, 25000000, 5).round(0),
            'ABONO NETO': 0,
        })
        df_incentivos['ABONO NETO'] = (df_incentivos['VALOR PAGO TOTAL'] * 0.85).round(0)
        combined_inc = pd.concat([incentivos_header, df_incentivos], ignore_index=True)
        combined_inc.to_excel(writer, sheet_name='INCENTIVOS', index=False, header=False)

        # ===== GASTOS VIAJE =====
        viaje_header = pd.DataFrame([[''] * 3] * 10)
        df_viajes = pd.DataFrame({
            'NOMBRE COMPLETO': ['VIAJERO DEMO A', 'VIAJERO DEMO B', 'VIAJERO DEMO C'],
            'PAGO VIATICOS': [1500000, 2200000, 800000],
            'FECHA DE PAGO': [datetime(2024, 9, 1), datetime(2025, 2, 15), datetime(2025, 5, 20)],
        })
        combined_viaje = pd.concat([viaje_header, df_viajes], ignore_index=True)
        combined_viaje.to_excel(writer, sheet_name='GASTOS VIAJE', index=False, header=False)

        # ===== MOVIMIENTO DB Y CR =====
        mov_header = pd.DataFrame([['', '', '', '', '', ''], ['', '', '', '', '', '']])
        meses = ['Julio-24', 'Agosto-24', 'Sept-24', 'Oct-24', 'Nov-24', 'Dic-24',
                 'Enero-25', 'Feb-25', 'Marzo-25', 'Abril-25', 'Mayo-25', 'Junio-25']
        saldo = 2500000000
        mov_rows = []
        for mes in meses:
            ing = np.random.uniform(100000000, 500000000)
            pag = np.random.uniform(50000000, 400000000)
            ints = np.random.uniform(1000000, 5000000)
            saldo_fin = saldo + ing - pag + ints
            mov_rows.append({'MES': mes, 'SALDO INICIAL': round(saldo), 'INGRESOS': round(ing),
                             'PAGOS': round(pag), 'INTERESES': round(ints), 'SALDO FINAL': round(saldo_fin)})
            saldo = saldo_fin
        df_mov = pd.DataFrame(mov_rows)
        combined_mov = pd.concat([mov_header, df_mov], ignore_index=True)
        combined_mov.to_excel(writer, sheet_name='MOVIMIENTO DB Y CR', index=False, header=False)

        # ===== FIDUCOLDEX =====
        fidu_data = [[''] * 17] * 2
        months_row = ['', ''] + [f'2024-{m:02d}' for m in range(7, 13)] + [f'2025-{m:02d}' for m in range(1, 7)] + ['2025-07', '2025-08', '2025-09']
        fidu_data.append(months_row[:17])
        for _ in range(5):
            fidu_data.append(['', 'INGRESOS'] + [round(np.random.uniform(100e6, 500e6)) for _ in range(15)])
        saldo_row = ['', 'SALDO FINAL'] + [round(np.random.uniform(500e6, 3000e6)) for _ in range(15)]
        fidu_data.append(saldo_row)
        df_fidu = pd.DataFrame(fidu_data)
        df_fidu.to_excel(writer, sheet_name='FIDUCOLDEX', index=False, header=False)

    file_size = os.path.getsize(output_path) / 1024
    print(f"Archivo de prueba generado: {output_path}")
    print(f"  Hojas: INF PAGOS, GASTOS CP, INGRESOS CP, INCENTIVOS, GASTOS VIAJE, MOVIMIENTO DB Y CR, FIDUCOLDEX")
    print(f"  Tamano: {file_size:.0f} KB")
    return output_path


if __name__ == '__main__':
    generate_test_excel()
