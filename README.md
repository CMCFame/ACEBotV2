# ACEBotV2 - ACE Questionnaire Assistant

Una aplicación Streamlit para guiar a los usuarios a través del cuestionario ACE (Automated Callout Enhancement) para documentar procesos de callout de servicios públicos.

## 🚀 Inicio Rápido

### Prerrequisitos
- Python 3.8+
- AWS Account con acceso a Bedrock
- (Opcional) Configuración de email para notificaciones

### Instalación

1. **Clona el repositorio:**
   ```bash
   git clone <repository-url>
   cd ACEBotV2
   ```

2. **Instala dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configura variables de entorno:**
   Crea un archivo `.env` en el directorio raíz con:
   ```env
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_DEFAULT_REGION=us-east-1

   # Opcional: Configuración de email
   EMAIL_SENDER=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   EMAIL_RECIPIENT=recipient@example.com
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

### Ejecutar la Aplicación

**Opción recomendada (Windows):**
```powershell
.\run_simple_clean.ps1
```

**Opción alternativa:**
```bash
streamlit run simple_ace_app.py --server.port 8520
```

## 📋 Características

- **23 preguntas estructuradas** sobre procesos de callout
- **Integración con AWS Bedrock** (Claude 3.5 Sonnet)
- **Sistema de guardado/reanudación** de sesiones
- **Exportación de respuestas** en múltiples formatos
- **Sistema de auditoría** con redacción PII
- **Notificaciones por email** opcionales

## 🏗️ Arquitectura

- **`simple_ace_app.py`** - Aplicación principal (único punto de entrada)
- **`run_simple_clean.ps1`** - Script de ejecución principal
- **`requirements.txt`** - Dependencias Python
- **`assets/`** - Archivos estáticos (CSS)
- **`data/`** - Datos de la aplicación (prompts, preguntas)

## 🧪 Tests

Para ejecutar los tests:
```powershell
.\run_tests.ps1
```

## 📁 Estructura del Proyecto

```
ACEBotV2/
├── simple_ace_app.py          # 🏠 Aplicación principal
├── run_simple_clean.ps1       # 🚀 Script de ejecución
├── run_tests.ps1              # 🧪 Script de tests
├── requirements.txt           # 📦 Dependencias
├── README.md                  # 📖 Esta documentación
├── assets/
│   └── style.css             # 🎨 Estilos
├── data/
│   ├── prompts/              # 💬 Prompts del sistema
│   └── questions.txt         # ❓ Conjunto de preguntas
├── examples/                 # 📝 Ejemplos de conversación
└── archive/                  # 🗂️ Código y archivos deprecated
```

## 🤝 Contribución

Este repositorio está optimizado para un único punto de entrada claro. Todo el código relacionado con características no utilizadas ha sido movido a la carpeta `archive/`.

## 📞 Soporte

Para soporte técnico o preguntas sobre la configuración, contacta al equipo de desarrollo.
