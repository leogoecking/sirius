import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox

# --- Lógica do Banco de Dados (Backend) ---

DB_FILE = "banco_de_dados.json"

def carregar_db():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
        except json.JSONDecodeError:
            return []

def salvar_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def normalizar_mac(mac):
    return re.sub(r'[^0-9A-Fa-f]', '', mac).upper()

# --- Interface Gráfica (Frontend) ---

class GerenciadorApp:
    def __init__(self, root):
        self.db = carregar_db()
        self.root = root
        self.root.title("Gerenciador de Senhas MAC")
        self.root.geometry("500x450")
        self.root.resizable(False, False)

        # Estilo das abas
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # Aba 1: Adicionar
        self.frame_add = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_add, text='Adicionar Senha')
        self.setup_add_tab()

        # Aba 2: Buscar
        self.frame_search = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_search, text='Buscar Senha')
        self.setup_search_tab()

    def setup_add_tab(self):
        # Campo MAC
        lbl_mac = ttk.Label(self.frame_add, text="MAC Completo (Ex: AB-CD...):")
        lbl_mac.pack(pady=(20, 5))
        self.entry_mac = ttk.Entry(self.frame_add, width=40)
        self.entry_mac.pack(pady=5)

        # Campo Senha
        lbl_pass = ttk.Label(self.frame_add, text="Senha:")
        lbl_pass.pack(pady=(10, 5))
        self.entry_pass = ttk.Entry(self.frame_add, width=40, show="*") # show="*" esconde a senha
        self.entry_pass.pack(pady=5)

        # Botão Salvar
        btn_save = ttk.Button(self.frame_add, text="Salvar Registro", command=self.adicionar)
        btn_save.pack(pady=20)

    def setup_search_tab(self):
        # Campo Busca
        lbl_search = ttk.Label(self.frame_search, text="Digite os últimos 4 dígitos do MAC:")
        lbl_search.pack(pady=(20, 5))
        
        frame_busca_input = ttk.Frame(self.frame_search)
        frame_busca_input.pack()
        
        self.entry_search = ttk.Entry(frame_busca_input, width=20)
        self.entry_search.pack(side=tk.LEFT, padx=5)
        
        btn_search = ttk.Button(frame_busca_input, text="Buscar", command=self.buscar)
        btn_search.pack(side=tk.LEFT, padx=5)

        # Área de Resultados (Texto)
        self.result_area = tk.Text(self.frame_search, height=12, width=55, state='disabled')
        self.result_area.pack(pady=20)

    def adicionar(self):
        mac = self.entry_mac.get().strip()
        senha = self.entry_pass.get()

        if not mac:
            messagebox.showwarning("Aviso", "O campo MAC é obrigatório.")
            return
        if not senha:
            messagebox.showwarning("Aviso", "O campo Senha é obrigatório.")
            return

        entry = {
            "mac_original": mac,
            "mac_normalizado": normalizar_mac(mac),
            "senha": senha
        }
        self.db.append(entry)
        salvar_db(self.db)
        
        messagebox.showinfo("Sucesso", "Informação salva com sucesso!")
        self.entry_mac.delete(0, tk.END)
        self.entry_pass.delete(0, tk.END)

    def buscar(self):
        ultimos = self.entry_search.get().strip()
        if not ultimos:
            messagebox.showwarning("Aviso", "Digite os dígitos para buscar.")
            return

        ultimos_norm = re.sub(r'[^0-9A-Fa-f]', '', ultimos).upper()
        if len(ultimos_norm) > 4:
            ultimos_norm = ultimos_norm[-4:]

        encontrados = []
        for entry in self.db:
            mac_norm = entry.get("mac_normalizado", "")
            if mac_norm.endswith(ultimos_norm):
                encontrados.append(entry)

        # Exibir no campo de texto
        self.result_area.config(state='normal') # Habilita edição para limpar e escrever
        self.result_area.delete(1.0, tk.END)
        
        if not encontrados:
            self.result_area.insert(tk.END, "Nenhum registro encontrado.\n")
        else:
            for i, e in enumerate(encontrados, start=1):
                texto = f"#{i}\nMAC: {e.get('mac_original')}\nSENHA: {e.get('senha')}\n{'-'*30}\n"
                self.result_area.insert(tk.END, texto)
        
        self.result_area.config(state='disabled') # Bloqueia edição novamente

if __name__ == "__main__":
    root = tk.Tk()
    app = GerenciadorApp(root)
    root.mainloop()
