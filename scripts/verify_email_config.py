#!/usr/bin/env python
"""
Script para verificar la configuración de email de Flask-Mail.
Ejecutar: python scripts/verify_email_config.py
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from flask_mail import Message
from app.extensions import mail


def verify_config():
    """Verifica que las variables de configuración estén presentes"""
    app = create_app()

    print("=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN DE EMAIL")
    print("=" * 60)

    config_keys = [
        'MAIL_SERVER',
        'MAIL_PORT',
        'MAIL_USE_TLS',
        'MAIL_USERNAME',
        'MAIL_PASSWORD',
        'MAIL_DEFAULT_SENDER'
    ]

    all_ok = True
    for key in config_keys:
        value = app.config.get(key)
        if key == 'MAIL_PASSWORD' and value:
            # No mostrar la contraseña completa
            display_value = value[:4] + '****' if len(value) > 4 else '****'
        else:
            display_value = value

        status = "OK" if value else "FALTA"
        if not value:
            all_ok = False

        print(f"  {key}: {display_value} [{status}]")

    print("-" * 60)

    if not all_ok:
        print("ERROR: Faltan variables de configuración.")
        print("Por favor configura el archivo .env con las credenciales de email.")
        print("\nPara Gmail, necesitas:")
        print("1. Habilitar verificación en 2 pasos")
        print("2. Crear una 'Contraseña de aplicación' en:")
        print("   https://myaccount.google.com/security")
        return False

    return True


def send_test_email(recipient_email):
    """Envía un email de prueba"""
    app = create_app()

    with app.app_context():
        try:
            msg = Message(
                subject='[TEST] Verificación de Email - Puerto Distribución',
                recipients=[recipient_email],
                html="""
                <h2>Prueba de Configuración de Email</h2>
                <p>Si estás leyendo este mensaje, la configuración de Flask-Mail está funcionando correctamente.</p>
                <p style="color: #C85103; font-weight: bold;">Puerto Distribución - Sistema de Inventario</p>
                """
            )
            mail.send(msg)
            print(f"\nEmail de prueba enviado exitosamente a: {recipient_email}")
            print("Revisa tu bandeja de entrada (y la carpeta de spam).")
            return True
        except Exception as e:
            print(f"\nERROR al enviar email: {e}")
            print("\nPosibles causas:")
            print("- Credenciales incorrectas")
            print("- Gmail bloqueando 'apps menos seguras'")
            print("- Necesitas usar 'Contraseña de aplicación' de Gmail")
            return False


if __name__ == '__main__':
    if not verify_config():
        sys.exit(1)

    print("\n¿Deseas enviar un email de prueba? (s/n): ", end='')
    response = input().strip().lower()

    if response == 's':
        print("Ingresa el email de destino: ", end='')
        email = input().strip()
        if email:
            send_test_email(email)
        else:
            print("Email inválido.")
    else:
        print("Configuración verificada. No se envió email de prueba.")
