# Bot de Trading con Heiken Ashi y ADX

Este proyecto implementa un bot de trading algorítmico utilizando las velas Heiken Ashi y el indicador Average Directional Index (ADX) para identificar y operar tendencias. Incluye funcionalidades de backtesting, optimización de parámetros y un dashboard web básico para visualizar los resultados.

## Características

- **Estrategia Basada en Heiken Ashi y ADX**: Identifica tendencias fuertes y puntos de entrada/salida.
- **Gestión de Riesgos**: Cálculo de tamaño de posición basado en el riesgo por operación y ATR.
- **Backtesting Robusto**: Simula el rendimiento de la estrategia en datos históricos, calculando métricas clave como PnL total, tasa de ganancias, Sharpe Ratio, Sortino Ratio y Calmar Ratio.
- **Optimización de Parámetros**: Permite encontrar los mejores parámetros de la estrategia mediante la ejecución de múltiples backtests.
- **Notificaciones de Telegram**: Envía alertas en tiempo real sobre el inicio de procesos y las operaciones ejecutadas.
- **Dashboard Web Básico**: Visualiza los resultados de la optimización y la curva de capital de forma interactiva.
- **Manejo de Datos Flexible**: Obtiene datos de mercado a través de `ccxt` con un fallback a `yfinance`.
- **Logging Centralizado**: Registra eventos importantes para facilitar la depuración y el monitoreo.

## Instalación

1.  **Clonar el Repositorio**:
    ```bash
    git clone <URL_DEL_REPOSITORIO>
    cd bot_trading_heiken_adx
    ```

2.  **Crear un Entorno Virtual** (recomendado):
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

El bot se configura a través de dos archivos principales: `config.ini` para los parámetros de trading y estrategia, y `.env` para las claves de API y tokens sensibles.

### `config.ini`

Crea o edita el archivo `config.ini` en la raíz del proyecto con la siguiente estructura:

```ini
[TRADING]
symbol = BTC/USDT
timeframe = 1h
exchange = binance
risk_per_trade = 1.0

[STRATEGY]
sma_length = 50
volume_sma_length = 20
volume_multiplier = 1.5
adx_length = 14
adx_threshold = 25
atr_length = 14
rsi_length = 14
take_profit_levels = 2.0,3.0,4.0
```

-   **`[TRADING]`**: Configuración general de trading.
    -   `symbol`: Par de trading (ej. `BTC/USDT`).
    -   `timeframe`: Marco de tiempo de las velas (ej. `1h`, `4h`, `1d`).
    -   `exchange`: ID del exchange a usar (ej. `binance`, `bybit`). Asegúrate de que `ccxt` lo soporte.
    -   `risk_per_trade`: Porcentaje de capital a arriesgar por operación (ej. `1.0` para 1%).
-   **`[STRATEGY]`**: Parámetros específicos de la estrategia.
    -   `sma_length`: Longitud para la Media Móvil Simple.
    -   `volume_sma_length`: Longitud para la Media Móvil Simple del volumen.
    -   `volume_multiplier`: Multiplicador para el umbral de volumen.
    -   `adx_length`: Longitud para el indicador ADX.
    -   `adx_threshold`: Umbral del ADX para confirmar la fuerza de la tendencia.
    -   `atr_length`: Longitud para el Average True Range (ATR).
    -   `rsi_length`: Longitud para el Relative Strength Index (RSI).
    -   `take_profit_levels`: Lista de multiplicadores ATR para los niveles de toma de ganancias, separados por comas (ej. `2.0,3.0,4.0`).

### `.env`

Crea un archivo `.env` en la raíz del proyecto para almacenar tus claves de API y el token de Telegram. **Nunca subas este archivo a tu repositorio público.**

```dotenv
BINANCE_API_KEY=tu_api_key_de_binance
BINANCE_API_SECRET=tu_api_secret_de_binance

TELEGRAM_BOT_TOKEN=tu_token_de_bot_telegram
TELEGRAM_CHAT_ID=tu_id_de_chat_telegram
```

-   Reemplaza `BINANCE` con el ID de tu exchange en mayúsculas (ej. `BYBIT_API_KEY`).
-   Obtén tu `TELEGRAM_BOT_TOKEN` de BotFather en Telegram.
-   Obtén tu `TELEGRAM_CHAT_ID` enviando un mensaje a tu bot y luego accediendo a `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`.

## Uso

### Ejecutar el Backtester

Para ejecutar la simulación de backtesting con la configuración actual:

```bash
python src/main.py
```

Los resultados del backtest se imprimirán en la consola y se guardarán en los logs.

### Ejecutar la Optimización

Para optimizar los parámetros de la estrategia (definidos en `src/main.py` en la función `run_optimization_pipeline`):

```bash
python src/main.py
```

Los resultados de la optimización se guardarán en `results/optimization_results.csv`.

### Ejecutar el Dashboard Web

Para visualizar los resultados de la optimización en un dashboard interactivo:

```bash
python dashboard/app.py
```

Luego, abre tu navegador y ve a `http://127.0.0.1:5000/`.

## Estructura del Proyecto

```
bot_trading_heiken_adx/
├── .env                 # Variables de entorno (claves API, tokens Telegram)
├── config.ini           # Archivo de configuración de la estrategia
├── requirements.txt     # Dependencias del proyecto
├── GEMINI_CONTEXT.md    # Historial de desarrollo con Gemini
├── results/             # Directorio para guardar resultados de optimización
│   └── optimization_results.csv
├── logs/                # Directorio para archivos de log
│   └── trading_bot.log
├── src/
│   ├── __init__.py
│   ├── backtester.py    # Lógica de simulación de backtesting
│   ├── config.py        # Carga y gestión de la configuración
│   ├── data_handler.py  # Obtención y limpieza de datos de mercado
│   ├── execution_handler.py # Simulación de ejecución de órdenes
│   ├── indicator_calculator.py # Cálculo de indicadores técnicos
│   ├── logger.py        # Configuración del sistema de logging
│   ├── main.py          # Punto de entrada principal del bot
│   ├── notifier.py      # Envío de notificaciones (ej. Telegram)
│   ├── optimizer.py     # Lógica de optimización de parámetros
│   ├── risk_manager.py  # Gestión de riesgos y tamaño de posición
│   └── strategy.py      # Lógica central de la estrategia de trading
└── tests/
    ├── test_backtester.py
    ├── test_config.py
    ├── test_data_handler.py
    ├── test_execution_handler.py
    ├── test_indicator_calculator.py
    └── test_risk_manager.py
```

## Pruebas

Para ejecutar las pruebas unitarias del proyecto, usa `pytest`:

```bash
pytest
```

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o envía un pull request con tus mejoras.

```