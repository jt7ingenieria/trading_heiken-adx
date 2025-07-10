# Bot de Trading Heiken ADX

Este proyecto implementa un bot de trading automatizado utilizando la estrategia Heiken Ashi y el indicador ADX. El bot está diseñado para realizar backtesting y optimización de estrategias, con planes futuros para operación en tiempo real y un dashboard de visualización.

## Características

*   **Estrategia Heiken Ashi + ADX**: Implementa una estrategia de trading basada en la combinación de velas Heiken Ashi y el Average Directional Index (ADX).
*   **Backtesting Robusto**: Simula operaciones en datos históricos para evaluar el rendimiento de la estrategia.
*   **Optimización de Parámetros**: Encuentra los mejores parámetros para la estrategia a través de múltiples backtests.
*   **Manejo de Datos Flexible**: Obtiene datos históricos de exchanges a través de CCXT, con un mecanismo de reintento y fallback a yfinance.
*   **Inyección de Dependencias**: Arquitectura modular y testeable gracias a la inyección de dependencias.
*   **Logging Centralizado**: Registro detallado de eventos para depuración y monitoreo.
*   **Notificaciones (Telegram)**: Envía notificaciones sobre eventos clave del bot (requiere configuración).
*   **Gestión de Take Profit Parcial**: Implementación de múltiples niveles de toma de ganancias.
*   **Guardado de Resultados**: Los resultados del backtesting y la optimización se guardan en archivos CSV/JSON para su análisis.
*   **Dashboard Web Básico (en progreso)**: Una interfaz web simple para visualizar los resultados (integración en curso).

## Instalación

1.  **Clonar el Repositorio**:
    ```bash
    git clone https://github.com/jt7ingenieria/trading_heiken-adx.git
    cd trading_heiken-adx
    ```

2.  **Crear y Activar Entorno Virtual**:
    ```bash
    python -m venv trading_heiken_adx
    # En Windows
    .\trading_heiken_adx\Scripts\activate
    # En macOS/Linux
    source trading_heiken_adx/bin/activate
    ```

3.  **Instalar Dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuración

1.  **`config.ini`**:
    *   Abre `config.ini` y ajusta los parámetros de trading (`symbol`, `timeframe`, `exchange`) y de la estrategia (`sma_length`, `volume_sma_length`, `volume_multiplier`, `adx_length`, `adx_threshold`, `atr_length`, `rsi_length`, `take_profit_levels`).
    *   **Ejemplo de configuración actual (rentable para SOL/USDT en 1h):**
        ```ini
        [TRADING]
        symbol = SOL/USDT
        timeframe = 1h
        exchange = okx
        risk_per_trade = 1.0

        [STRATEGY]
        sma_length = 50
        volume_sma_length = 20
        volume_multiplier = 1.0
        adx_length = 14
        adx_threshold = 20
        atr_length = 14
        rsi_length = 14
        take_profit_levels = 2.0,3.0
        ```

2.  **`.env` (para notificaciones y API Keys)**:
    *   Crea un archivo `.env` en la raíz del proyecto.
    *   Añade tus claves de API del exchange (ej. `OKX_API_KEY=tu_api_key`, `OKX_API_SECRET=tu_api_secret`).
    *   Para notificaciones de Telegram, añade `TELEGRAM_BOT_TOKEN=tu_token_bot` y `TELEGRAM_CHAT_ID=tu_chat_id`.

## Uso

### Ejecutar Backtesting y Optimización

Para ejecutar el backtesting y la optimización con la configuración actual:

```bash
.\trading_heiken_adx\Scripts\python.exe src\main.py
```

Los resultados del backtesting se guardarán en `results/backtest_results.json` y los resultados de la optimización en `results/optimization_results.csv`.

### Ejecutar el Dashboard Web (en progreso)

Para iniciar el dashboard (asegúrate de tener Flask instalado, lo cual se hace con `pip install -r requirements.txt`):

```bash
.\trading_heiken_adx\Scripts\python.exe dashboard\app.py
```

Luego, abre tu navegador web y ve a `http://127.0.0.1:5000/` (o la dirección que te indique la consola).

## Pruebas Unitarias

Para ejecutar las pruebas unitarias del proyecto:

```bash
.\trading_heiken_adx\Scripts\python.exe -m pytest
```

## Problemas Conocidos y Próximos Pasos

*   **Integración con el Dashboard**: La visualización completa en el dashboard web aún requiere trabajo para mostrar todos los datos de manera efectiva.
*   **Despliegue y Operación en Vivo**: Preparar el bot para operar en vivo, incluyendo la configuración de un entorno de producción y la monitorización.
*   **Mejoras en la Estrategia**: Explorar y añadir nuevas lógicas de entrada/salida o indicadores para mejorar el rendimiento de la estrategia.
*   **Gestión de Órdenes Avanzada**: Implementar lógica para gestionar órdenes abiertas, modificar órdenes y cancelar órdenes si es necesario.
*   **Manejo de Eventos en Tiempo Real**: Si se planea operar en vivo, implementar un sistema de manejo de eventos en tiempo real para reaccionar a los cambios del mercado de forma instantánea.

