#!/usr/bin/env python3
"""
File Organizer - Monitoramento e organização automática de arquivos
Aplicativo completo com interface PyQt5 e tray icon
"""

import sys
import os
import json
import shutil
import threading
import time
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QSystemTrayIcon, QMenu,
    QAction, QStyle, QCheckBox, QDialog, QDialogButtonBox,
    QFormLayout, QSpinBox, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QColor


class SignalEmitter(QObject):
    """Emissor de sinais para comunicação entre threads"""
    update_log = pyqtSignal(str)
    rules_updated = pyqtSignal()
    monitoring_status_changed = pyqtSignal(bool)


class FileMonitor:
    """Monitor de arquivos que roda em thread separada"""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.rules = []
        self.running = False
        self.interval = 2  # segundos
        self.emitter = SignalEmitter()
        self.load_rules()
        
    def load_rules(self):
        """Carrega regras do arquivo de configuração"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.rules = data.get('rules', [])
                    self.interval = data.get('interval', 2)
            else:
                self.rules = []
        except Exception as e:
            print(f"Erro ao carregar regras: {e}")
            self.rules = []
    
    def save_rules(self):
        """Salva regras no arquio de configuração"""
        try:
            data = {
                'rules': self.rules,
                'interval': self.interval,
                'monitoring_enabled': self.running
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar regras: {e}")
            return False
    
    def add_rule(self, watch_folder, keyword, target_folder):
        """Adiciona uma nova regra"""
        rule = {
            'watch_folder': watch_folder,
            'keyword': keyword.lower(),
            'target_folder': target_folder,
            'enabled': True
        }
        self.rules.append(rule)
        self.save_rules()
        self.emitter.rules_updated.emit()
        return True
    
    def edit_rule(self, index, watch_folder, keyword, target_folder):
        """Edita uma regra existente"""
        if 0 <= index < len(self.rules):
            self.rules[index] = {
                'watch_folder': watch_folder,
                'keyword': keyword.lower(),
                'target_folder': target_folder,
                'enabled': True
            }
            self.save_rules()
            self.emitter.rules_updated.emit()
            return True
        return False
    
    def delete_rule(self, index):
        """Exclui uma regra"""
        if 0 <= index < len(self.rules):
            del self.rules[index]
            self.save_rules()
            self.emitter.rules_updated.emit()
            return True
        return False
    
    def toggle_monitoring(self):
        """Alterna o estado do monitoramento"""
        if self.running:
            self.stop()
        else:
            self.start()
        return self.running
    
    def get_status(self):
        """Retorna o status do monitoramento"""
        return self.running
    
    def check_files(self):
        """Verifica e processa arquivos conforme as regras"""
        if not self.running:
            return
            
        for rule in self.rules:
            if not rule.get('enabled', True):
                continue
                
            watch_path = Path(rule['watch_folder'])
            keyword = rule['keyword']
            target_path = Path(rule['target_folder'])
            
            if not watch_path.exists() or not target_path.exists():
                continue
                
            try:
                for file_path in watch_path.iterdir():
                    if file_path.is_file():
                        filename = file_path.name.lower()
                        if keyword in filename:
                            # Verifica se o arquivo está completamente escrito
                            try:
                                # Tenta abrir o arquivo para leitura
                                with open(file_path, 'rb'):
                                    pass
                            except IOError:
                                continue
                                
                            # Cria pasta de destino se não existir
                            target_path.mkdir(parents=True, exist_ok=True)
                            
                            # Move o arquivo
                            target_file = target_path / file_path.name
                            counter = 1
                            
                            # Evita sobrescrever arquivos existentes
                            while target_file.exists():
                                stem = file_path.stem
                                suffix = file_path.suffix
                                target_file = target_path / f"{stem}_{counter}{suffix}"
                                counter += 1
                            
                            shutil.move(str(file_path), str(target_file))
                            
                            log_msg = f"✓ Movido: {file_path.name} → {target_path}"
                            self.emitter.update_log.emit(log_msg)
            except Exception as e:
                self.emitter.update_log.emit(f"✗ Erro em {watch_path}: {str(e)}")
    
    def start(self):
        """Inicia o monitoramento"""
        if not self.running and self.rules:
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            self.emitter.monitoring_status_changed.emit(True)
            return True
        return False
    
    def _monitor_loop(self):
        """Loop principal do monitor"""
        while self.running:
            self.check_files()
            time.sleep(self.interval)
    
    def stop(self):
        """Para o monitoramento"""
        if self.running:
            self.running = False
            if hasattr(self, 'thread'):
                self.thread.join(timeout=1)
            self.emitter.monitoring_status_changed.emit(False)
            return True
        return False


class RuleDialog(QDialog):
    """Diálogo para adicionar/editar regras"""
    
    def __init__(self, parent=None, rule_index=None, rule_data=None):
        super().__init__(parent)
        self.rule_index = rule_index
        self.rule_data = rule_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Adicionar/Editar Regra" if self.rule_index is None else "Editar Regra")
        self.setModal(True)
        self.resize(500, 200)
        
        layout = QVBoxLayout(self)
        
        # Formulário
        form_layout = QFormLayout()
        
        self.watch_folder_edit = QLineEdit()
        self.watch_folder_edit.setPlaceholderText("Selecione a pasta para monitorar")
        self.watch_folder_btn = QPushButton("Selecionar...")
        self.watch_folder_btn.clicked.connect(self.select_watch_folder)
        
        watch_layout = QHBoxLayout()
        watch_layout.addWidget(self.watch_folder_edit)
        watch_layout.addWidget(self.watch_folder_btn)
        
        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("Ex: faturas, imagem, projeto")
        
        self.target_folder_edit = QLineEdit()
        self.target_folder_edit.setPlaceholderText("Selecione a pasta de destino")
        self.target_folder_btn = QPushButton("Selecionar...")
        self.target_folder_btn.clicked.connect(self.select_target_folder)
        
        target_layout = QHBoxLayout()
        target_layout.addWidget(self.target_folder_edit)
        target_layout.addWidget(self.target_folder_btn)
        
        form_layout.addRow("Pasta Monitorada:", watch_layout)
        form_layout.addRow("Palavra-chave:", self.keyword_edit)
        form_layout.addRow("Pasta Destino:", target_layout)
        
        layout.addLayout(form_layout)
        
        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Preencher dados se estiver editando
        if self.rule_data:
            self.watch_folder_edit.setText(self.rule_data.get('watch_folder', ''))
            self.keyword_edit.setText(self.rule_data.get('keyword', ''))
            self.target_folder_edit.setText(self.rule_data.get('target_folder', ''))
    
    def select_watch_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta para Monitorar")
        if folder:
            self.watch_folder_edit.setText(folder)
    
    def select_target_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Selecionar Pasta de Destino")
        if folder:
            self.target_folder_edit.setText(folder)
    
    def get_data(self):
        return {
            'watch_folder': self.watch_folder_edit.text().strip(),
            'keyword': self.keyword_edit.text().strip(),
            'target_folder': self.target_folder_edit.text().strip()
        }


class MainWindow(QMainWindow):
    """Janela principal do aplicativo"""
    
    def __init__(self, start_minimized=False):
        super().__init__()
        self.monitor = FileMonitor()
        self.setup_ui()
        self.setup_tray()
        self.load_rules_to_table()
        
        # Conectar sinais
        self.monitor.emitter.update_log.connect(self.add_log)
        self.monitor.emitter.rules_updated.connect(self.load_rules_to_table)
        self.monitor.emitter.monitoring_status_changed.connect(self.update_monitoring_status)
        
        # Verificar se deve iniciar monitoramento automaticamente
        self.load_monitoring_state()
        
        if start_minimized:
            self.hide()
        
    def setup_ui(self):
        self.setWindowTitle("Organizador de Arquivos")
        self.setGeometry(100, 100, 800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Título
        title_label = QLabel("Organizador Automático de Arquivos")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("padding: 15px; color: #2c3e50;")
        main_layout.addWidget(title_label)
        
        # Grupo de controle de monitoramento
        control_group = QGroupBox("Controle de Monitoramento")
        control_layout = QHBoxLayout()
        
        # Botão Iniciar/Parar
        self.monitor_btn = QPushButton("▶️ Iniciar Monitoramento")
        self.monitor_btn.clicked.connect(self.toggle_monitoring)
        self.monitor_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
        """)
        
        # Botão de status
        self.status_btn = QPushButton("Status: Parado")
        self.status_btn.setEnabled(False)
        self.status_btn.setStyleSheet("""
            QPushButton {
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                background-color: #ff6b6b;
                color: white;
            }
        """)
        
        control_layout.addWidget(self.monitor_btn)
        control_layout.addWidget(self.status_btn)
        control_layout.addStretch()
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # Grupo de regras
        rules_group = QGroupBox("Regras de Organização")
        rules_layout = QVBoxLayout()
        
        # Botões de ação para regras
        buttons_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Adicionar Regra")
        self.add_btn.clicked.connect(self.add_rule)
        self.add_btn.setStyleSheet("padding: 8px; font-weight: bold;")
        
        self.edit_btn = QPushButton("✏️ Editar Regra")
        self.edit_btn.clicked.connect(self.edit_rule)
        self.edit_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("🗑️ Excluir Regra")
        self.delete_btn.clicked.connect(self.delete_rule)
        self.delete_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.edit_btn)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addStretch()
        
        rules_layout.addLayout(buttons_layout)
        
        # Tabela de regras
        self.rules_table = QTableWidget()
        self.rules_table.setColumnCount(3)
        self.rules_table.setHorizontalHeaderLabels(["Pasta Monitorada", "Palavra-chave", "Pasta Destino"])
        self.rules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.rules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.rules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rules_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rules_table.itemSelectionChanged.connect(self.on_rule_selected)
        
        rules_layout.addWidget(self.rules_table)
        rules_group.setLayout(rules_layout)
        main_layout.addWidget(rules_group)
        
        # Grupo de logs
        log_group = QGroupBox("Log de Atividades")
        log_layout = QVBoxLayout()
        
        self.log_text = QLabel("Pronto para monitorar...")
        self.log_text.setWordWrap(True)
        self.log_text.setStyleSheet("""
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 10px;
            min-height: 100px;
            font-family: monospace;
        """)
        
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # Status bar
        self.status_label = QLabel("Aguardando configuração...")
        self.statusBar().addWidget(self.status_label)
        
    def setup_tray(self):
        """Configura o ícone na bandeja do sistema"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Usar ícone padrão do sistema se não tiver um específico
        app_icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(app_icon)
        
        # Menu do tray
        self.tray_menu = QMenu()
        
        # Ação para mostrar/ocultar
        self.show_action = QAction("Abrir", self)
        self.show_action.triggered.connect(self.show_window)
        self.tray_menu.addAction(self.show_action)
        
        # Ação para iniciar/parar monitoramento
        self.tray_monitor_action = QAction("▶️ Iniciar Monitoramento", self)
        self.tray_monitor_action.triggered.connect(self.toggle_monitoring)
        self.tray_menu.addAction(self.tray_monitor_action)
        
        self.tray_menu.addSeparator()
        
        # Ação para sair
        quit_action = QAction("Sair", self)
        quit_action.triggered.connect(self.quit_app)
        self.tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
    def tray_icon_activated(self, reason):
        """Lida com cliques no ícone da bandeja"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """Mostra a janela principal"""
        self.show()
        self.activateWindow()
        self.raise_()
    
    def closeEvent(self, event):
        """Minimiza para bandeja ao fechar"""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Organizador de Arquivos",
            "O aplicativo continua rodando na bandeja do sistema",
            QSystemTrayIcon.Information,
            2000
        )
    
    def changeEvent(self, event):
        """Minimiza para bandeja ao minimizar"""
        if event.type() == event.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    "Organizador de Arquivos",
                    "O aplicativo foi minimizado para a bandeja",
                    QSystemTrayIcon.Information,
                    2000
                )
    
    def quit_app(self):
        """Encerra o aplicativo completamente"""
        self.monitor.stop()
        QApplication.quit()
    
    def load_monitoring_state(self):
        """Carrega o estado do monitoramento do arquivo de configuração"""
        try:
            if os.path.exists(self.monitor.config_file):
                with open(self.monitor.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    monitoring_enabled = data.get('monitoring_enabled', False)
                    
                    # Se houver regras e monitoring_enabled for True, inicia o monitoramento
                    if monitoring_enabled and self.monitor.rules:
                        self.monitor.start()
                        self.update_monitoring_status(True)
                    else:
                        self.update_monitoring_status(False)
        except Exception as e:
            print(f"Erro ao carregar estado: {e}")
            self.update_monitoring_status(False)
    
    def toggle_monitoring(self):
        """Alterna o estado do monitoramento"""
        if not self.monitor.rules:
            QMessageBox.warning(self, "Atenção", "Adicione pelo menos uma regra antes de iniciar o monitoramento!")
            return
        
        new_status = self.monitor.toggle_monitoring()
        self.update_monitoring_status(new_status)
        
        # Salva o estado
        self.monitor.save_rules()
        
        if new_status:
            self.add_log("Monitoramento INICIADO")
        else:
            self.add_log("Monitoramento PARADO")
    
    def update_monitoring_status(self, is_running):
        """Atualiza a interface com o status do monitoramento"""
        if is_running:
            self.monitor_btn.setText("⏸️ Parar Monitoramento")
            self.status_btn.setText("Status: Ativo")
            self.status_btn.setStyleSheet("""
                QPushButton {
                    padding: 10px;
                    font-weight: bold;
                    font-size: 14px;
                    border-radius: 5px;
                    background-color: #4CAF50;
                    color: white;
                }
            """)
            self.tray_monitor_action.setText("⏸️ Parar Monitoramento")
            self.status_label.setText("Monitoramento ATIVO")
        else:
            self.monitor_btn.setText("▶️ Iniciar Monitoramento")
            self.status_btn.setText("Status: Parado")
            self.status_btn.setStyleSheet("""
                QPushButton {
                    padding: 10px;
                    font-weight: bold;
                    font-size: 14px;
                    border-radius: 5px;
                    background-color: #ff6b6b;
                    color: white;
                }
            """)
            self.tray_monitor_action.setText("▶️ Iniciar Monitoramento")
            self.status_label.setText("Monitoramento PARADO")
    
    def add_log(self, message):
        """Adiciona uma mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        current_text = self.log_text.text()
        new_text = f"[{timestamp}] {message}<br>{current_text}"
        self.log_text.setText(new_text)
        
        # Mantém apenas as últimas 10 mensagens
        lines = new_text.split("<br>")
        if len(lines) > 10:
            self.log_text.setText("<br>".join(lines[:10]))
    
    def load_rules_to_table(self):
        """Carrega as regras para a tabela"""
        self.monitor.load_rules()
        rules = self.monitor.rules
        
        self.rules_table.setRowCount(len(rules))
        
        for i, rule in enumerate(rules):
            self.rules_table.setItem(i, 0, QTableWidgetItem(rule.get('watch_folder', '')))
            self.rules_table.setItem(i, 1, QTableWidgetItem(rule.get('keyword', '')))
            self.rules_table.setItem(i, 2, QTableWidgetItem(rule.get('target_folder', '')))
        
        # Atualiza status
        rule_count = len(rules)
        status_text = f"{rule_count} regra{'s' if rule_count != 1 else ''}"
        
        # Atualiza status do monitoramento na barra de status
        if self.monitor.get_status():
            status_text += " • Monitoramento ATIVO"
        else:
            status_text += " • Monitoramento PARADO"
        
        self.status_label.setText(status_text)
        
        # Habilita/desabilita botões conforme necessidade
        self.edit_btn.setEnabled(rule_count > 0)
        self.delete_btn.setEnabled(rule_count > 0)
        
        # Atualiza botão de monitoramento
        if rule_count == 0:
            self.monitor_btn.setEnabled(False)
            self.tray_monitor_action.setEnabled(False)
        else:
            self.monitor_btn.setEnabled(True)
            self.tray_monitor_action.setEnabled(True)
    
    def on_rule_selected(self):
        """Lida com seleção de regras na tabela"""
        selected = self.rules_table.selectedItems()
        has_selection = len(selected) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def add_rule(self):
        """Adiciona uma nova regra"""
        dialog = RuleDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            
            # Validação
            if not all([data['watch_folder'], data['keyword'], data['target_folder']]):
                QMessageBox.warning(self, "Atenção", "Todos os campos são obrigatórios!")
                return
            
            if not os.path.exists(data['watch_folder']):
                QMessageBox.warning(self, "Atenção", "A pasta monitorada não existe!")
                return
            
            if not os.path.exists(data['target_folder']):
                reply = QMessageBox.question(
                    self, "Confirmar",
                    "A pasta de destino não existe. Deseja criá-la?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    try:
                        os.makedirs(data['target_folder'], exist_ok=True)
                    except:
                        QMessageBox.critical(self, "Erro", "Não foi possível criar a pasta!")
                        return
                else:
                    return
            
            if self.monitor.add_rule(**data):
                QMessageBox.information(self, "Sucesso", "Regra adicionada com sucesso!")
                self.add_log(f"Regra adicionada: {data['keyword']}")
                
                # Se for a primeira regra, habilita o botão de monitoramento
                if len(self.monitor.rules) == 1:
                    self.monitor_btn.setEnabled(True)
                    self.tray_monitor_action.setEnabled(True)
    
    def edit_rule(self):
        """Edita a regra selecionada"""
        selected_rows = set(item.row() for item in self.rules_table.selectedItems())
        if not selected_rows:
            return
        
        row = list(selected_rows)[0]
        rule_data = self.monitor.rules[row]
        
        dialog = RuleDialog(self, row, rule_data)
        if dialog.exec_():
            data = dialog.get_data()
            
            # Validação
            if not all([data['watch_folder'], data['keyword'], data['target_folder']]):
                QMessageBox.warning(self, "Atenção", "Todos os campos são obrigatórios!")
                return
            
            if not os.path.exists(data['watch_folder']):
                QMessageBox.warning(self, "Atenção", "A pasta monitorada não existe!")
                return
            
            if not os.path.exists(data['target_folder']):
                reply = QMessageBox.question(
                    self, "Confirmar",
                    "A pasta de destino não existe. Deseja criá-la?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    try:
                        os.makedirs(data['target_folder'], exist_ok=True)
                    except:
                        QMessageBox.critical(self, "Erro", "Não foi possível criar a pasta!")
                        return
                else:
                    return
            
            if self.monitor.edit_rule(row, **data):
                QMessageBox.information(self, "Sucesso", "Regra atualizada com sucesso!")
                self.add_log(f"Regra editada: {data['keyword']}")
    
    def delete_rule(self):
        """Exclui a regra selecionada"""
        selected_rows = set(item.row() for item in self.rules_table.selectedItems())
        if not selected_rows:
            return
        
        row = list(selected_rows)[0]
        rule_data = self.monitor.rules[row]
        
        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a regra com palavra-chave '{rule_data['keyword']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.monitor.delete_rule(row):
                QMessageBox.information(self, "Sucesso", "Regra excluída com sucesso!")
                self.add_log(f"Regra excluída: {rule_data['keyword']}")
                
                # Se não houver mais regras, desabilita o botão de monitoramento
                if len(self.monitor.rules) == 0:
                    self.monitor_btn.setEnabled(False)
                    self.tray_monitor_action.setEnabled(False)
                    if self.monitor.get_status():
                        self.monitor.stop()


def main():
    """Função principal do aplicativo"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Organizador de Arquivos")
    
    # Verifica se há regras salvas e se o monitoramento estava ativo
    monitor = FileMonitor()
    monitor.load_rules()
    
    # Determina se deve iniciar minimizado
    start_minimized = False
    if monitor.rules:
        try:
            if os.path.exists(monitor.config_file):
                with open(monitor.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    monitoring_enabled = data.get('monitoring_enabled', False)
                    # Inicia minimizado se houver regras
                    start_minimized = True
        except:
            pass
    
    window = MainWindow(start_minimized=start_minimized)
    
    # Se não houver regras, abre a janela automaticamente
    if not monitor.rules:
        window.show()
        window.add_log("Aplicativo iniciado. Adicione sua primeira regra para começar.")
    else:
        # Com regras, inicia minimizado na bandeja (se start_minimized for True)
        if start_minimized:
            window.tray_icon.showMessage(
                "Organizador de Arquivos",
                f"Aplicativo iniciado na bandeja com {len(monitor.rules)} regra{'s' if len(monitor.rules) != 1 else ''}.",
                QSystemTrayIcon.Information,
                3000
            )
            window.add_log(f"Aplicativo iniciado com {len(monitor.rules)} regra{'s' if len(monitor.rules) != 1 else ''}.")
        else:
            window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()