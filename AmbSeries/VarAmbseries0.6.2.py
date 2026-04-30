#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
timeseries_analysis.py
Versão para Python 3.7 com robustez extra, formatação de eixo X para horas,
e filtragem explícita do intervalo de tempo selecionado:
- Filtra apenas arquivos XML válidos
- Seleção de período por data/hora (mínimo 3h)
- Estatísticas exibidas no GUI e exportadas para TXT
- Botão "Fechar" para encerrar o aplicativo
- Plots de série temporal com ticks horários e formatação de data/hora
- Filtra o DataFrame para mostrar apenas dados entre início e fim exatos
"""

"""
VarAmbseries_Fixed.py
Versão Corrigida:
- Resolve o erro 'Sensores não encontrados' usando busca dinâmica de arquivos.
- Aceita formatos de data com 4 dígitos (YYDD) ou 5 dígitos (YYDDD).
- Robustez contra arquivos corrompidos.
"""
import os
import sys
import re
import datetime
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import messagebox, filedialog
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import glob

def is_xml_file(fp):
    """Verifica se o arquivo é valido e começa com tag XML."""
    try:
        if not os.path.isfile(fp): return False
        with open(fp, 'rb') as f:
            start = f.read(128)
        text = start.decode('utf-8', errors='ignore').lstrip('\ufeff').lstrip()
        return text.startswith('<')
    except Exception:
        return False

def find_xml_in_dir(dir_path):
    """
    Procura o primeiro arquivo XML válido que comece com 'log_ambientvars' 
    dentro do diretório, ignorando o sufixo numérico exato.
    """
    try:
        # Padrão: log_ambientvars*.xml (pega -2626, -26026, etc)
        pattern = os.path.join(dir_path, "log_ambientvars*.xml")
        candidates = glob.glob(pattern)
        
        # Retorna o primeiro candidato válido
        for cand in candidates:
            if is_xml_file(cand):
                return cand
        return None
    except Exception as e:
        print(f"Erro buscando XML em {dir_path}: {e}")
        return None

def list_subdirs_dates(base_dir):
    """Lista diretórios convertendo nomes YYDDD ou YYDD para data."""
    entries = []
    print(f"Varrendo diretório base: {base_dir}")
    
    if not os.path.isdir(base_dir):
        print("Diretório base não existe!")
        return []

    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        # Aceita 4 ou 5 dígitos (ex: 2626 ou 26026)
        if os.path.isdir(path) and re.match(r"^\d{4,5}$", name):
            try:
                yy = int(name[:2])
                ddd = int(name[2:])
                year = 2000 + yy
                # Data base = 1 Jan do ano atual + (dias - 1)
                date = datetime.date(year, 1, 1) + datetime.timedelta(days=ddd - 1)
                entries.append((date, name))
            except Exception as e:
                print(f"Erro convertendo pasta {name}: {e}")
                continue
    
    entries = sorted(entries, key=lambda x: x[0])
    print(f"Encontrados {len(entries)} subdiretórios válidos de data.")
    return entries

def detect_sensors(dates_subdirs, base_dir):
    detected_sensors = set()
    for _, sub in dates_subdirs:
        dir_path = os.path.join(base_dir, sub)
        fp = find_xml_in_dir(dir_path) # Busca dinâmica
        
        if not fp:
            continue
            
        try:
            tree = ET.parse(fp)
            root = tree.getroot()
            # Procura na primeira medida válida para identificar sensores
            for m in root.findall('measure'):
                # Identifica tags como RHA, TCB, etc.
                current_sensors = {e.tag[2] for e in m if len(e.tag)==3 and e.tag[:2] in ('RH','TC')}
                if current_sensors:
                    detected_sensors.update(current_sensors)
                    # Se achou sensores neste arquivo, pode pular para o próximo diretório
                    break 
        except Exception:
            continue
            
    return sorted(list(detected_sensors))

def parse_files(dates_subdirs, base_dir, sensor_letters):
    records = []
    print(f"Iniciando parsing de {len(dates_subdirs)} pastas...")
    
    for dt, sub in dates_subdirs:
        dir_path = os.path.join(base_dir, sub)
        fp = find_xml_in_dir(dir_path)
        
        if not fp:
            print(f"Aviso: XML ausente na pasta {sub}")
            continue

        try:
            tree = ET.parse(fp)
            root = tree.getroot()
        except Exception as e:
            print(f"Erro lendo {fp}: {e}")
            continue
            
        for m in root.findall('measure'):
            ts_str = m.get('timestamp','')
            try:
                # Tenta ISO format primeiro (mais rápido)
                ts = datetime.datetime.fromisoformat(ts_str)
            except ValueError:
                try:
                    ts = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
                except Exception:
                    continue # Pula timestamp inválido

            entry = {'timestamp': ts}
            has_data = False
            for L in sensor_letters:
                rh = m.find(f"RH{L}")
                tc = m.find(f"TC{L}")
                
                # Tratamento robusto para valores float
                try:
                    val_rh = float(rh.text) if (rh is not None and rh.text) else np.nan
                except ValueError: val_rh = np.nan
                
                try:
                    val_tc = float(tc.text) if (tc is not None and tc.text) else np.nan
                except ValueError: val_tc = np.nan

                entry[f"RH{L}"] = val_rh
                entry[f"TC{L}"] = val_tc
                
                if not np.isnan(val_rh) or not np.isnan(val_tc):
                    has_data = True

            if has_data:
                records.append(entry)

    if records:
        print(f"Total de registros extraídos: {len(records)}")
        df = pd.DataFrame(records)
        df.sort_values('timestamp', inplace=True)
        return df
    
    return pd.DataFrame()

def plot_data(df, sensor_letters):
    if df.empty:
        messagebox.showinfo("Sem dados", "Nenhum registro válido para plotagem.")
        return
        
    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter('%d/%m %H:%M')
    
    # Plot Temperatura
    fig, ax = plt.subplots(figsize=(10, 5))
    for L in sensor_letters:
        if f"TC{L}" in df.columns:
            ax.plot(df['timestamp'], df[f"TC{L}"], label=f"Temp Sensor {L}")
    
    ax.set_ylabel("Temperatura (°C)")
    ax.set_title("Monitoramento Térmico")
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Plot Umidade
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    for L in sensor_letters:
        if f"RH{L}" in df.columns:
            ax2.plot(df['timestamp'], df[f"RH{L}"], label=f"Umidade Sensor {L}")
            
    ax2.set_ylabel("Umidade Relativa (%)")
    ax2.set_title("Monitoramento de Umidade")
    ax2.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_formatter(formatter)
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.show()

def on_process(root, base_var, start_var, end_var, stats_label):
    stats_label.config(text="Iniciando processamento...")
    root.update() # Força atualização da GUI
    
    try:
        sd = datetime.datetime.strptime(start_var.get(), "%Y-%m-%d %H:%M")
        ed = datetime.datetime.strptime(end_var.get(), "%Y-%m-%d %H:%M")
    except ValueError:
        messagebox.showerror("Erro", "Formato de data inválido.\nUse: YYYY-MM-DD HH:MM")
        stats_label.config(text="Aguardando..."); return

    if ed <= sd:
        messagebox.showerror("Erro", "A data final deve ser maior que a inicial.")
        stats_label.config(text="Aguardando..."); return

    base = base_var.get()
    ds = list_subdirs_dates(base)
    
    # Filtro de período (considera o dia inteiro)
    period = [(d, s) for d, s in ds if sd.date() <= d <= ed.date()]
    
    if not period:
        messagebox.showerror("Aviso", f"Nenhuma pasta de dados encontrada entre {sd.date()} e {ed.date()}.")
        stats_label.config(text="Sem dados no período."); return

    sensors = detect_sensors(period, base)
    if not sensors:
        messagebox.showerror("Erro Crítico", 
            "Estrutura de arquivos incompatível.\n"
            "Não foi possível identificar sensores (RH/TC) dentro dos arquivos XML.\n"
            "Verifique se os arquivos log_ambientvars-*.xml existem nas pastas."
        )
        stats_label.config(text="Erro de leitura."); return

    # Janela de Seleção
    sel = tk.Toplevel(root)
    sel.title("Sensores Detectados")
    sel.geometry("300x400")
    
    tk.Label(sel, text="Selecione os Sensores:", font=("Arial", 10, "bold")).pack(pady=10)
    vars_map = {}
    
    for L in sensors:
        v = tk.BooleanVar(value=True)
        frame = tk.Frame(sel)
        frame.pack(fill='x', padx=20)
        tk.Checkbutton(frame, text=f"Sensor {L}", variable=v).pack(side='left')
        vars_map[L] = v

    def run_analysis():
        chosen = [L for L, v in vars_map.items() if v.get()]
        if not chosen: return
        sel.destroy()
        
        df = parse_files(period, base, chosen)
        if df.empty:
            messagebox.showinfo("Vazio", "Nenhum dado encontrado no intervalo exato.")
            return

        # Filtro fino de horário
        df = df[(df['timestamp'] >= sd) & (df['timestamp'] <= ed)]
        
        if df.empty:
            messagebox.showinfo("Vazio", "Dados existem nas pastas, mas fora do horário das 08:00 às 08:00 selecionado.")
            return

        # Estatísticas
        lines = []
        for L in chosen:
            # Stats Temperatura
            stc = df[f"TC{L}"].dropna()
            if not stc.empty:
                lines.append(f"[Sensor {L}] Temp: Média {stc.mean():.1f}°C | Min {stc.min():.1f} | Max {stc.max():.1f}")
            
            # Stats Umidade
            srh = df[f"RH{L}"].dropna()
            if not srh.empty:
                lines.append(f"[Sensor {L}] Umid: Média {srh.mean():.1f}% | Min {srh.min():.1f} | Max {srh.max():.1f}")
                
        result_text = "\n".join(lines)
        stats_label.config(text=result_text)
        
        # Salvar TXT
        try:
            fname = f"Relatorio_{sd.strftime('%Y%m%d')}_{ed.strftime('%Y%m%d')}.txt"
            with open(fname, 'w') as f: f.write(result_text)
            print(f"Relatório salvo em: {fname}")
        except Exception: pass
        
        plot_data(df, chosen)

    tk.Button(sel, text="Gerar Gráficos", command=run_analysis, bg="#DDDDDD", height=2).pack(fill='x', padx=20, pady=20)

def main():
    root = tk.Tk()
    root.title("Análise de Séries Temporais (Lab Automation)")
    
    # Layout Principal
    tk.Label(root, text="Diretório de Logs:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    base_var = tk.StringVar(value=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'varamblog')))
    tk.Entry(root, textvariable=base_var, width=50).grid(row=0, column=1, padx=5)
    tk.Button(root, text="...", command=lambda: base_var.set(filedialog.askdirectory() or base_var.get())).grid(row=0, column=2, padx=5)

    tk.Label(root, text="Início (YYYY-MM-DD HH:MM):").grid(row=1, column=0, sticky="e")
    start_var = tk.StringVar(value="2026-01-26 08:00")
    tk.Entry(root, textvariable=start_var).grid(row=1, column=1, sticky="w")

    tk.Label(root, text="Fim (YYYY-MM-DD HH:MM):").grid(row=2, column=0, sticky="e")
    end_var = tk.StringVar(value="2026-01-29 08:00")
    tk.Entry(root, textvariable=end_var).grid(row=2, column=1, sticky="w")

    # Área de Status
    stats_frame = tk.LabelFrame(root, text="Resultado da Análise", padx=10, pady=10)
    stats_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
    stats_label = tk.Label(stats_frame, text="Aguardando comando...", justify="left", font=("Consolas", 9))
    stats_label.pack(fill="both", expand=True)

    # Botões
    btn_frame = tk.Frame(root)
    btn_frame.grid(row=4, column=0, columnspan=3, pady=10)
    tk.Button(btn_frame, text="PROCESSAR DADOS", command=lambda: on_process(root, base_var, start_var, end_var, stats_label), bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=10)
    tk.Button(btn_frame, text="Sair", command=root.destroy, bg="#f44336", fg="white").pack(side="left", padx=10)

    root.mainloop()

if __name__ == "__main__":
    main()