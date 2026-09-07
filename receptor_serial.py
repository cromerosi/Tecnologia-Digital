import serial
import time

# --- CONFIGURACIÓN ---
PUERTO = "COM7"
BAUD_RATE = 115200

# Elige el modo: 'normal', 'binario', 'hexadecimal' o 'todos'
MODO_VISTA = "todos"
# ---------------------

try:
    esp32 = serial.Serial(PUERTO, BAUD_RATE, timeout=1)
    time.sleep(2)

    print(f"Conectado en {PUERTO}. Modo de vista: {MODO_VISTA.upper()}\n")

    while True:
        if esp32.in_waiting > 0:

            # Leer el dato en crudo
            datos_raw = esp32.readline().rstrip()

            if not datos_raw:
                continue

            # Texto normal
            texto = datos_raw.decode("utf-8", errors="ignore")

            # Hexadecimal
            hexa = datos_raw.hex(" ").upper()

            # Binario
            binario = " ".join(format(byte, "08b") for byte in datos_raw)

            # Mostrar según el modo
            if MODO_VISTA == "normal":
                print(texto)

            elif MODO_VISTA == "binario":
                print(binario)

            elif MODO_VISTA == "hexadecimal":
                print(hexa)

            elif MODO_VISTA == "todos":
                print("-" * 50)
                print(f"Normal : {texto}")
                print(f"Hex    : {hexa}")
                print(f"Binario: {binario}")

            else:
                print("Modo de vista no válido.")
                break

except KeyboardInterrupt:
    print("\nLectura finalizada.")

except serial.SerialException as e:
    print(f"\nError de puerto: {e}")

finally:
    if "esp32" in locals() and esp32.is_open:
        esp32.close()
