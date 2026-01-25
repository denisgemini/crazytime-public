#!/bin/bash
# scripts/install_service.sh - Instala servicio systemd

set -e

echo "🔧 Instalando servicio CrazyTime..."

if [ ! -f "main.py" ]; then
    echo "❌ Error: Ejecutar desde el directorio raíz del proyecto"
    exit 1
fi

PROJECT_DIR=$(pwd)
USER=$(whoami)

echo "📝 Creando archivo de servicio..."

sudo tee /etc/systemd/system/crazytime.service > /dev/null <<EOF
[Unit]
Description=CrazyTime Analytics Service v2.0
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/.venv/bin"
ExecStart=$PROJECT_DIR/.venv/bin/python $PROJECT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/data/logs/service.log
StandardError=append:$PROJECT_DIR/data/logs/service_error.log
MemoryMax=400M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Recargando systemd..."
sudo systemctl daemon-reload

echo "✅ Habilitando inicio automático..."
sudo systemctl enable crazytime

echo ""
echo "✅ Servicio instalado correctamente"
echo ""
echo "Comandos útiles:"
echo "  Iniciar:   sudo systemctl start crazytime"
echo "  Detener:    sudo systemctl stop crazytime"
echo "  Estado:     sudo systemctl status crazytime"
echo "  Logs:       sudo journalctl -u crazytime -f"
echo ""
