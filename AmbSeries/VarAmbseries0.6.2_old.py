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


def is_xml_file(fp):
    """Verifica se o arquivo começa com '<' após BOM/whitespace."""
    try:
        with open(fp, 'rb') as f:
            start = f.read(128)
        text = start.decode('utf-8', errors='ignore').lstrip('\ufeff').lstrip()
        return text.startswith('<')
    except Exception as e:
        print(f"Aviso is_xml_file falhou: {e}", file=sys.stderr)
        return False


def list_subdirs_dates(base_dir):
    entries = []
    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        if os.path.isdir(path) and re.match(r"^\d{5}$", name):
            yy = int(name[:2]); ddd = int(name[2:]); year = 2000 + yy
            try:
                date = datetime.date(year, 1, 1) + datetime.timedelta(days=ddd - 1)
                entries.append((date, name))
            except Exception:
                continue
    return sorted(entries, key=lambda x: x[0])


def detect_sensors(dates_subdirs, base_dir):
    for _, sub in dates_subdirs:
        fp = os.path.join(base_dir, sub, f"log_ambientvars-{sub}.xml")
        if not os.path.isfile(fp) or not is_xml_file(fp):
            continue
        try:
            tree = ET.parse(fp); root = tree.getroot()
        except ET.ParseError as e:
            print(f"Aviso detect_sensors parse falhou ({fp}): {e}", file=sys.stderr)
            continue
        for m in root.findall('measure'):
            sensors = {e.tag[2] for e in m if len(e.tag)==3 and e.tag[:2] in ('RH','TC')}
            if sensors:
                return sorted(sensors)
    return []


def parse_files(dates_subdirs, base_dir, sensor_letters):
    records = []
    for _, sub in dates_subdirs:
        fp = os.path.join(base_dir, sub, f"log_ambientvars-{sub}.xml")
        if not os.path.isfile(fp) or not is_xml_file(fp):
            print(f"Ignorando não-XML ou ausente: {fp}", file=sys.stderr)
            continue
        try:
            tree = ET.parse(fp); root = tree.getroot()
        except ET.ParseError as e:
            print(f"Aviso parse falhou ({fp}): {e}", file=sys.stderr)
            continue
        for m in root.findall('measure'):
            ts_str = m.get('timestamp','')
            try:
                ts = datetime.datetime.fromisoformat(ts_str)
            except Exception:
                try:
                    ts = datetime.datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S.%f")
                except Exception:
                    print(f"Aviso timestamp inválido em {fp}: {ts_str}", file=sys.stderr)
                    continue
            entry = {'timestamp': ts}
            for L in sensor_letters:
                rh = m.find(f"RH{L}"); tc = m.find(f"TC{L}")
                entry[f"RH{L}"] = float(rh.text) if rh is not None else np.nan
                entry[f"TC{L}"] = float(tc.text) if tc is not None else np.nan
            records.append(entry)
    if records:
        df = pd.DataFrame(records)
        df.sort_values('timestamp', inplace=True)
        return df
    cols = ['timestamp'] + [f"RH{l}" for l in sensor_letters] + [f"TC{l}" for l in sensor_letters]
    return pd.DataFrame(columns=cols)


def plot_data(df, sensor_letters):
    if df.empty:
        messagebox.showinfo("Sem dados", "Nenhum registro no período selecionado.")
        return
    locator = mdates.AutoDateLocator()
    formatter = mdates.DateFormatter('%d %H:%M')
    # Temperatura
    fig, ax = plt.subplots()
    for L in sensor_letters:
        ax.plot(df['timestamp'], df[f"TC{L}"], label=f"TC{L}")
    ax.set_xlabel("Timestamp"); ax.set_ylabel("Temperatura (°C)")
    ax.set_title("Série Temporal de Temperatura")
    ax.xaxis.set_major_locator(locator); ax.xaxis.set_major_formatter(formatter)
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    ax.legend(); ax.grid(True)
    # Umidade
    fig2, ax2 = plt.subplots()
    for L in sensor_letters:
        ax2.plot(df['timestamp'], df[f"RH{L}"], label=f"RH{L}")
    ax2.set_xlabel("Timestamp"); ax2.set_ylabel("Umidade Relativa (%)")
    ax2.set_title("Série Temporal de Umidade")
    ax2.xaxis.set_major_locator(locator); ax2.xaxis.set_major_formatter(formatter)
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    ax2.legend(); ax2.grid(True)
    plt.tight_layout(); plt.show()


def main():
    root = tk.Tk(); root.title("Análise de Séries Temporais")
    tk.Label(root, text="Diretório Base:").grid(row=0, column=0, sticky="e")
    base_var = tk.StringVar(value=os.getcwd())
    tk.Entry(root, textvariable=base_var, width=40).grid(row=0, column=1)
    tk.Button(root, text="Browse", command=lambda: base_var.set(filedialog.askdirectory() or base_var.get())).grid(row=0, column=2)
    tk.Label(root, text="Início (YYYY-MM-DD HH:MM):").grid(row=1, column=0, sticky="e")
    start_var = tk.StringVar(); tk.Entry(root, textvariable=start_var).grid(row=1, column=1)
    tk.Label(root, text="Fim    (YYYY-MM-DD HH:MM):").grid(row=2, column=0, sticky="e")
    end_var = tk.StringVar(); tk.Entry(root, textvariable=end_var).grid(row=2, column=1)

    stats_frame = tk.LabelFrame(root, text="Estatísticas do Período")
    stats_frame.grid(row=3, column=0, columnspan=3, pady=5, sticky="we")
    stats_label = tk.Label(stats_frame, text="Defina início/fim (mínimo 3h) e processe.")
    stats_label.pack(anchor="w")

    btn_process = tk.Button(root, text="Processar", command=lambda: on_process(root, base_var, start_var, end_var, stats_label))
    btn_process.grid(row=4, column=1, pady=5)
    btn_close = tk.Button(root, text="Fechar", command=root.destroy)
    btn_close.grid(row=4, column=2, pady=5)

    root.mainloop()


def on_process(root, base_var, start_var, end_var, stats_label):
    stats_label.config(text="Processando...")
    try:
        sd = datetime.datetime.strptime(start_var.get(), "%Y-%m-%d %H:%M")
        ed = datetime.datetime.strptime(end_var.get(), "%Y-%m-%d %H:%M")
    except ValueError:
        messagebox.showerror("Erro Período", "Formato inválido. Use YYYY-MM-DD HH:MM.")
        stats_label.config(text=""); return
    if ed <= sd:
        messagebox.showerror("Erro Período", "Final deve ser depois do início.")
        stats_label.config(text=""); return
    if ed - sd < datetime.timedelta(hours=3):
        messagebox.showerror("Erro Período", "Intervalo mínimo de 3 horas.")
        stats_label.config(text=""); return
    base = base_var.get(); ds = list_subdirs_dates(base)
    period = [(d, s) for d, s in ds if sd.date() <= d <= ed.date()]
    if not period:
        messagebox.showerror("Erro", "Nenhum diretório no período.")
        stats_label.config(text=""); return
    sensors = detect_sensors(period, base)
    if not sensors:
        messagebox.showerror("Erro", "Sensores não encontrados.")
        stats_label.config(text=""); return
    sel = tk.Toplevel(root); sel.title("Selecionar Sensores")
    tk.Label(sel, text="Sensores disponíveis:").pack(anchor="w")
    vars_map = {}
    for L in sensors:
        v = tk.BooleanVar(value=True); tk.Checkbutton(sel, text=L, variable=v).pack(anchor="w"); vars_map[L] = v

    def on_ok():
        chosen = [L for L, v in vars_map.items() if v.get()]
        if not chosen:
            messagebox.showerror("Erro", "Selecione ao menos um sensor."); return
        sel.destroy()
        df = parse_files(period, base, chosen)
        # filtra exatamente entre sd e ed
        df = df[(df['timestamp'] >= sd) & (df['timestamp'] <= ed)]
        if df.empty:
            messagebox.showinfo("Sem dados no intervalo", "Nenhum registro dentro do período exato selecionado.")
            stats_label.config(text=""); return
        lines = []
        for L in chosen:
            for pfx, lbl in [("TC","Temperatura"),("RH","Umidade")]:
                col = f"{pfx}{L}"; s = df[col].dropna()
                if not s.empty:
                    lines.append(f"{lbl} sensor {L}: média {s.mean():.2f}, mediana {s.median():.2f}, min {s.min():.2f}, max {s.max():.2f}")
        stats_text = "\n".join(lines)
        stats_label.config(text=stats_text)
        fname = f"Statstemporal_{sd.strftime('%Y%m%d_%H%M')}_{ed.strftime('%Y%m%d_%H%M')}.txt"
        try:
            with open(fname, 'w') as f:
                f.write(stats_text)
            print(f"Estatísticas gravadas em {fname}")
        except Exception as e:
            print(f"Erro salvando {fname}: {e}", file=sys.stderr)
        for L in chosen:
            if df[f"TC{L}"].count() <= 5:
                messagebox.showwarning("Poucos Dados", f"Sensor {L}: poucos registros de temperatura.")
            if df[f"RH{L}"].count() <= 5:
                messagebox.showwarning("Poucos Dados", f"Sensor {L}: poucos registros de umidade.")
        plot_data(df, chosen)

    tk.Button(sel, text="OK", command=on_ok).pack()

if __name__ == "__main__":
    main()
