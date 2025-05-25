import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

from dproj_parser import get_pas_files_from_dproj
from pas_analyzer import analyze_pas_files
from report_generator import generate_report

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Analisador de Memória Delphi")
        self.geometry("700x500")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame superior para seleção de projetos
        top_frame = tk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(top_frame, text="Projeto:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Entrada para exibir o caminho do arquivo
        self.dproj_path_var = tk.StringVar()
        self.dproj_entry = tk.Entry(top_frame, textvariable=self.dproj_path_var, width=40)
        self.dproj_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        single_file_btn = tk.Button(top_frame, text="Selecionar Arquivo", command=self.select_dproj)
        single_file_btn.pack(side=tk.LEFT, padx=5)
        
        # Checkbox para relatório detalhado
        options_frame = tk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=5)
        
        self.detailed_var = tk.BooleanVar(value=True)
        
        # Botão para iniciar análise
        analyze_btn = tk.Button(options_frame, text="Iniciar Análise", command=self.start_analysis)
        analyze_btn.pack(side=tk.LEFT, padx=10)
        
        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=5)
        
        # Frame inferior para log
        log_frame = tk.LabelFrame(main_frame, text="Log")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Área de texto para log
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar para o log
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Status inicial
        self.log("Pronto para análise. Selecione um arquivo .dproj ou .pas para começar.")
    
    def select_dproj(self):
        """Abre diálogo para selecionar arquivo .dproj"""
        file_path = filedialog.askopenfilename(
            title="Selecionar arquivo .dproj",
            filetypes=[("Arquivos de projeto Delphi", "*.dproj"), ("Arquivos Delphi", "*.pas")]
        )
        if file_path:
            self.dproj_path_var.set(file_path)
            self.log(f"Selecionado: {file_path}")
    
    def start_analysis(self):
        """Inicia a análise em um thread separado"""
        file_path = self.dproj_path_var.get()
        
        if not file_path:
            messagebox.showerror("Erro", "Selecione um arquivo .dproj ou .pas primeiro")
            return
        
        # Limpar log anterior
        self.log_text.delete(1.0, tk.END)
        self.log(f"Iniciando análise de {file_path}")
        
        # Resetar progresso
        self.progress_var.set(0)
        
        # Verificar tipo de arquivo
        is_single_file = file_path.lower().endswith('.pas')
        detailed = self.detailed_var.get()
        
        # Iniciar thread para não bloquear a interface
        threading.Thread(
            target=self.run_analysis,
            args=(file_path, is_single_file, detailed),
            daemon=True
        ).start()
    
    def run_analysis(self, dproj_path, single_file, detailed=False):
        """Executa a análise em um thread separado"""
        try:
            self.log(f"{'Analisando arquivo único' if single_file else 'Analisando projeto'}")
            
            # Lista de arquivos a analisar
            pas_files = []
            
            if single_file:
                pas_files = [dproj_path]
                self.log(f"Analisando arquivo: {os.path.basename(dproj_path)}")
            else:
                self.log(f"Lendo projeto: {os.path.basename(dproj_path)}")
                pas_files = get_pas_files_from_dproj(dproj_path)
                self.log(f"Encontrados {len(pas_files)} arquivos .pas no projeto")
            
            # Definir callbacks para progresso e log
            def log_callback(message):
                self.after(0, lambda: self.log(message))
            
            def progress_callback(percent):
                self.after(0, lambda: self.progress_var.set(percent))
            
            # Executar análise
            results = analyze_pas_files(pas_files, log_callback, progress_callback)
            
            if results:
                self.log(f"Análise completa. Encontrados {len(results)} objetos não liberados.")
                
                # Gerar relatório
                report_path = os.path.join(os.path.dirname(dproj_path), "memory_leak_report.html")
                
                generate_report(
                    results, 
                    report_path, 
                    title=f"Relatório de Vazamento de Memória: {os.path.basename(dproj_path)}",
                    detailed=detailed
                )
                
                os.startfile(report_path)
            else:
                self.log("Análise completa. Nenhum vazamento de memória encontrado!")
                messagebox.showinfo("Análise Concluída", "Nenhum vazamento de memória encontrado!")
            
        except Exception as e:
            self.log(f"Erro durante a análise: {str(e)}")
            messagebox.showerror("Erro", f"Ocorreu um erro durante a análise:\n{str(e)}")
    
    def log(self, message):
        """Adiciona mensagem ao log"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # Rolar para o final
        
if __name__ == "__main__":
    app = Application()
    app.mainloop() 