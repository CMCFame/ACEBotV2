# ACEBotV2 - ACE Questionnaire Assistant

Una aplicación Streamlit para guiar a los usuarios a través del cuestionario ACE (Automated Callout Enhancement) para documentar procesos de callout de servicios públicos.

## 🚀 Inicio Rápido

### Prerrequisitos
- Docker y Docker Compose
- AWS Account con acceso a Bedrock
- (Opcional) Configuración de email para notificaciones

### 🚢 Ejecutar con Docker (Recomendado)

1. **Clona el repositorio:**
   ```bash
   git clone <repository-url>
   cd ACEBotV2
   ```

2. **Verifica la configuración de Docker:**
   ```powershell
   .\test_docker.ps1
   ```

3. **Configura variables de entorno:**
   Copia el archivo de ejemplo y edítalo:
   ```bash
   cp docker-env-example.txt .env
   # Edita .env con tus credenciales de AWS y configuración opcional
   ```

4. **Ejecuta con Docker:**
   ```powershell
   .\run_docker.ps1
   ```
   O directamente:
   ```bash
   docker-compose up --build
   ```

5. **Accede a la aplicación:**
   Abre http://localhost:8520 en tu navegador

### 💻 Ejecutar Localmente (Alternativo)

#### Prerrequisitos
- Python 3.8+
- AWS Account con acceso a Bedrock

#### Instalación Local

1. **Instala dependencias:**
   ```bash
   pip install -r requirements.txt
   pip install streamlit boto3 google-api-python-client google-auth
   ```

2. **Configura variables de entorno:**
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

3. **Ejecuta la aplicación:**
   ```powershell
   .\run_simple_clean.ps1
   ```
   O:
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
├── run_simple_clean.ps1       # 🚀 Script de ejecución local
├── run_docker.ps1             # 🚢 Script de ejecución con Docker
├── test_docker.ps1            # ✅ Script de validación de Docker
├── run_tests.ps1              # 🧪 Script de tests
├── requirements.txt           # 📦 Dependencias Python
├── Dockerfile                 # 🐳 Configuración de Docker
├── docker-compose.yml         # 🐳 Orquestación de contenedores
├── docker-env-example.txt     # 📝 Ejemplo de variables de entorno
├── README.md                  # 📖 Esta documentación
├── assets/
│   └── style.css             # 🎨 Estilos
├── data/
│   ├── prompts/              # 💬 Prompts del sistema
│   └── questions.txt         # ❓ Conjunto de preguntas
├── examples/                 # 📝 Ejemplos de conversación
└── archive/                  # 🗂️ Código y archivos deprecated
```

## 🐳 Docker

### Beneficios de usar Docker

- **Entorno consistente**: La aplicación se ejecuta igual en cualquier sistema con Docker
- **Aislamiento**: No interfiere con otras instalaciones de Python en tu sistema
- **Fácil distribución**: Comparte la aplicación como una imagen Docker
- **Escalabilidad**: Fácil de desplegar en servidores o servicios en la nube

### Comandos útiles de Docker

```bash
# Construir la imagen
docker-compose build

# Ejecutar en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f acebot

# Detener la aplicación
docker-compose down

# Limpiar imágenes no utilizadas
docker system prune
```

### Configuración de Producción

Para despliegue en producción, configura las variables de entorno apropiadas en tu servidor:

```bash
export AWS_ACCESS_KEY_ID=your_prod_key
export AWS_SECRET_ACCESS_KEY=your_prod_secret
# ... otras variables

docker-compose -f docker-compose.yml up -d
```

## 🤝 Contribución

Este repositorio está optimizado para un único punto de entrada claro. Todo el código relacionado con características no utilizadas ha sido movido a la carpeta `archive/`.

## 📞 Soporte

Para soporte técnico o preguntas sobre la configuración, contacta al equipo de desarrollo.
