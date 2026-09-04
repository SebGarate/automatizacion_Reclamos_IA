# Intelligent Claims Categorization & Incident Management System

Sistema end-to-end para la captura, análisis con Inteligencia Artificial, almacenamiento y visualización ejecutiva de reclamos de clientes. Cada reclamo ingresado es analizado automáticamente por Gemini AI, que determina su categoría, sentimiento del cliente, nivel de urgencia y genera un resumen ejecutivo, antes de persistirlo en PostgreSQL.

El proyecto integra una API REST en FastAPI para la ingesta y análisis en tiempo real, Power Apps para la captura operativa, Power Automate para la gestión de incidentes, y Power BI para la toma de decisiones ejecutiva.

---

## Arquitectura de la Solución

Un reclamo llega a través de la API REST (FastAPI) o de la app en Power Apps. El módulo de procesamiento envía el texto del reclamo a Gemini AI, que devuelve la categoría, sentimiento, urgencia y un resumen ejecutivo. Ese resultado, junto con los datos del cliente, se guarda en PostgreSQL. Desde ahí, Power Automate dispara alertas en tiempo real y las vistas SQL con Window Functions alimentan el Dashboard de Power BI.

Para poblar el dashboard con un histórico representativo sin depender de llamadas reales a la API de Gemini (lo que haría muy lento simular miles de reclamos y correr el flujo de Power Automate mil veces), existe un script independiente de generación masiva de datos.

---

## Componentes del Sistema

### 1. API de Categorización Inteligente (main.py + processor.py)
- API REST construida con FastAPI que expone un endpoint para registrar reclamos, validando los datos de entrada (nombre, DNI, email, texto del reclamo) con Pydantic.
- El módulo de procesamiento (processor.py) envía el texto del reclamo a la API de Gemini AI, que responde en formato JSON con la categoría, el sentimiento del cliente, el nivel de urgencia y un resumen ejecutivo de máximo 15 palabras.
- Incluye manejo de reintentos y conmutación entre modelos de Gemini ante errores del servidor (503), y control de errores de cliente.
- El resultado del análisis se inserta en PostgreSQL junto con los datos del cliente, devolviendo el registro creado como respuesta de la API.

### 2. Generación Masiva de Datos Históricos (poblar_bd.py)
- Script en Python que genera 1,000+ reclamos de prueba distribuidos entre un pool fijo de 50 clientes recurrentes, para simular trazabilidad e historial real de clientes.
- Su propósito es exclusivamente poblar la base de datos para efectos del Dashboard: pasar cada uno de esos reclamos por el flujo real de análisis con Gemini AI y por el flujo de Power Automate sería demasiado lento para generar un histórico de prueba, así que este script asigna categoría, sentimiento, urgencia y resumen de forma simulada y directa.
- Permite tener rápidamente un volumen de datos realista para construir y probar las vistas SQL y el reporte de Power BI sin esperar miles de llamadas a la API ni disparar miles de alertas.

### 3. Motor Analítico PostgreSQL (SQL Window Functions)
Vistas optimizadas mediante funciones de ventana y CTEs para análisis avanzado sin destruir el detalle de las filas:
- Recidiva y Frecuencia (LAG): mide el intervalo de días entre el reclamo actual y el anterior por DNI (PARTITION BY cliente_dni).
- Priorización de Atención (ROW_NUMBER): clasifica reclamos por categoría según nivel de urgencia (Alta > Media > Baja) y fecha de registro.
- Participación sobre el Total (COUNT / SUM OVER): evalúa la cuota porcentual de cada categoría frente al volumen global.

### 4. Automatización de Incidentes (Power Automate)
- Flujo de Escalamiento Inmediato: se dispara con cada nuevo registro en PostgreSQL con urgencia "Alta" y envía una alerta crítica por Email/Teams al equipo de supervisión con los datos del cliente y el resumen ejecutivo generado por la IA.
- Flujo de Alerta Temprana de Reincidencia: consulta diariamente la vista de clientes recurrentes filtrando por reclamos ocurridos en los últimos 3 días, y genera un reporte automático de riesgo de fuga (churn) enviado a Operaciones.

### 5. Dashboard Ejecutivo en Power BI
- Modelo en Estrella (Star Schema): relación de la tabla de hechos de reclamos con la dimensión temporal de fechas.
- Capa DAX: indicadores clave de volumen, tasa de severidad, promedios de recidiva y comportamiento del cliente.
- Secciones del informe:
  - Panel KPI: volumen total, % de urgencia alta y promedio de días de recidiva.
  - Matriz de Sentimiento: categorías vs. estado emocional del cliente detectado por la IA (Enojado, Frustrado, Neutral, etc.).
  - Módulo de Priorización: tabla de acción rápida filtrada en el Top 10 de casos críticos.

---

## Guía de Despliegue y Replicación

### Prerrequisitos
- Python 3.10+
- PostgreSQL 14+
- Power BI Desktop
- Cuenta y API Key de Gemini AI
- Licencia Power Apps / Power Automate con conector PostgreSQL

### Pasos
1. Crear la base de datos PostgreSQL y ejecutar las vistas analíticas ubicadas en el directorio sql/.
2. Configurar las variables de entorno necesarias (credenciales de PostgreSQL y la API Key de Gemini) en un archivo .env.
3. Levantar la API REST (main.py) para habilitar el registro y análisis de reclamos en tiempo real vía Gemini AI.
4. Ejecutar poblar_bd.py únicamente para generar un histórico simulado de reclamos y poder construir/probar el Dashboard sin depender de miles de llamadas reales a la IA.
5. Configurar los flujos de Power Automate: el de escalamiento inmediato para casos de urgencia alta y el de alerta temprana de reincidencia.
6. Crear las medidas DAX en Power BI (Total Reclamos, Clientes Únicos, % Urgencia Alta, Promedio Días Recidiva) y publicar el informe.
7. Conectar la app de Power Apps a la API o a PostgreSQL para el registro y actualización de estados de los reclamos en tiempo real.

---

## Estructura del Repositorio

```
├── assets/                  # Capturas de pantalla del Dashboard y Power Apps
├── sql/
│   ├── esquema_tabla.sql    # DDL de la base de datos
│   └── vistas_window.sql    # Vistas analíticas con Window Functions
├── main.py                  # API REST en FastAPI para la ingesta y análisis de reclamos
├── processor.py             # Módulo de análisis con Gemini AI y persistencia en PostgreSQL
├── poblar_bd.py             # Script de generación masiva de datos históricos simulados
├── Claims_Dashboard.pbix    # Reporte interactivo de Power BI
├── .gitignore                # Exclusión de archivos sensibles
├── requirements.txt          # Dependencias del proyecto
└── README.md                  # Documentación principal
```