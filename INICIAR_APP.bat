@echo off
title Generador de Actas - servidor
cd /d "%~dp0"
echo ============================================
echo  Generador de Actas
echo  En este equipo:      https://localhost:8501
echo  Desde otros equipos: https://172.16.20.5:8501
echo  (la primera vez el navegador pide aceptar
echo   la advertencia del certificado: Avanzado - Continuar)
echo  NO cierres esta ventana mientras la uses.
echo ============================================
:loop
python -m streamlit run app.py --server.headless true --server.sslCertFile certs/cert.pem --server.sslKeyFile certs/clave.pem
echo.
echo [%date% %time%] La aplicacion se detuvo. Reiniciando en 3 segundos...
timeout /t 3 /nobreak >nul
goto loop
