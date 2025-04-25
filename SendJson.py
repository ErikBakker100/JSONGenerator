import sys
import json
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton,
    QLabel, QComboBox, QLineEdit, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import QTimer

class JsonSerialSender(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JSON to Serial")
        self.resize(800, 1000)

        self.serial_port = None
        self.json_object = {}

        layout = QVBoxLayout()

        # COM port selection
        self.port_label = QLabel("Select COM port:")
        self.port_combo = QComboBox()
        self.update_ports()
        layout.addWidget(self.port_label)
        layout.addWidget(self.port_combo)

        # Baudrate input
        self.baud_label = QLabel("Baudrate:")
        self.baud_input = QLineEdit("115200")
        layout.addWidget(self.baud_label)
        layout.addWidget(self.baud_input)

        # Open/Close port button
        self.open_button = QPushButton("Open Port")
        self.open_button.clicked.connect(self.toggle_serial)
        layout.addWidget(self.open_button)

        # Key and value input
        key_value_layout = QHBoxLayout()
        self.key_combo = QComboBox()
        self.key_combo.addItems(["pulseWidth1", "interPulseDelay", "pulseWidth2", "pulseInterval"])
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Enter a number")
        key_value_layout.addWidget(self.key_combo)
        key_value_layout.addWidget(self.value_input)
        layout.addLayout(key_value_layout)

        # Add to JSON button
        self.add_button = QPushButton("Modify JSON")
        self.add_button.clicked.connect(self.add_to_json)
        layout.addWidget(self.add_button)

        # JSON preview
        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        self.json_preview.setPlaceholderText("JSON preview...")
        layout.addWidget(self.json_preview)

        # Send button
        self.send_button = QPushButton("Send JSON")
        self.send_button.clicked.connect(self.send_json)
        layout.addWidget(self.send_button)

        # Serial receive display
        self.receive_label = QLabel("Serial output:")
        layout.addWidget(self.receive_label)
        self.receive_box = QTextEdit()
        self.receive_box.setReadOnly(True)
        layout.addWidget(self.receive_box)

        self.setLayout(layout)

        # Timer to read serial input
        self.read_timer = QTimer()
        self.read_timer.setInterval(200)
        self.read_timer.timeout.connect(self.read_serial)

    def update_ports(self):
        ports = serial.tools.list_ports.comports()
        self.port_combo.clear()
        for port in ports:
            self.port_combo.addItem(port.device)

    def toggle_serial(self):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.serial_port = None
            self.open_button.setText("Open Port")
            self.read_timer.stop()
        else:
            try:
                port = self.port_combo.currentText()
                baudrate = int(self.baud_input.text())
                self.serial_port = serial.Serial(port, baudrate, timeout=0.1)
                self.open_button.setText("Close Port")
                self.read_timer.start()
            except serial.SerialException as e:
                QMessageBox.critical(self, "Serial Error", f"Cannot open port:\n{e}")

    def add_to_json(self):
        key = self.key_combo.currentText()
        value_text = self.value_input.text()

        try:
            value = float(value_text) if '.' in value_text else int(value_text)
        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Please enter a valid number.")
            return

        self.json_object[key] = value
        self.update_preview()

    def update_preview(self):
        pretty_json = json.dumps(self.json_object).replace('\n', '').replace('\r', '')
        self.json_preview.setPlainText(pretty_json)

    def send_json(self):
        if not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(self, "Port Closed", "Open the serial port first.")
            return

        json_text = json.dumps(self.json_object)
        json_text = json_text.replace('\n', '').replace('\r', '')

        try:
            self.serial_port.write(json_text.encode('utf-8'))
            # No confirmation popup shown here
        except serial.SerialException as e:
            QMessageBox.critical(self, "Send Error", str(e))

    def read_serial(self):
        if self.serial_port and self.serial_port.in_waiting:
            try:
                data = self.serial_port.read_all().decode(errors='ignore')
                if data:
                    current = self.receive_box.toPlainText()
                    self.receive_box.setPlainText(current + data)
            except Exception as e:
                self.receive_box.append(f"[Read Error]: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = JsonSerialSender()
    window.show()
    sys.exit(app.exec_())
