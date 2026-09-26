#include <Arduino.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"

// El mismo tipo de dato del ejemplo original.
struct SensorData {
  int id;
  float temperature;
};

// Estructura GLOBAL compartida: reemplaza a la cola.
SensorData sharedData = {1, 24.5f};

// Indica si hay una actualizacion pendiente de leer.
// Tambien se protege con dataMutex.
bool newDataAvailable = false;

// Semaforo de exclusion mutua.
SemaphoreHandle_t dataMutex = NULL;

// Core 1 como en el original; Core 0 en configuracion de un nucleo.
#if defined(CONFIG_FREERTOS_UNICORE) && CONFIG_FREERTOS_UNICORE
const BaseType_t TASK_CORE = 0;
#else
const BaseType_t TASK_CORE = 1;
#endif

void SenderTask(void *pvParameters);
void ReceiverTask(void *pvParameters);

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Inicializando sistema: estructura global + Mutex...");

  // Crear el Mutex ANTES de crear las tareas que lo utilizaran.
  dataMutex = xSemaphoreCreateMutex();

  if (dataMutex == NULL) {
    Serial.println("Error: no se pudo crear el Mutex.");
    return; // No se crean tareas si no hay Mutex.
  }

  Serial.println("Mutex creado correctamente.");

  BaseType_t senderResult = xTaskCreatePinnedToCore(
    SenderTask,
    "Sender",
    4096,           // Tamano de pila en BYTES en ESP32.
    NULL,
    1,              // Prioridad del emisor.
    NULL,
    TASK_CORE
  );

  BaseType_t receiverResult = xTaskCreatePinnedToCore(
    ReceiverTask,
    "Receiver",
    4096,           // Tamano de pila en BYTES en ESP32.
    NULL,
    2,              // Mayor prioridad que el emisor.
    NULL,
    TASK_CORE
  );

  if (senderResult != pdPASS || receiverResult != pdPASS) {
    Serial.println("Error: no se pudieron crear ambas tareas.");
  } else {
    Serial.println("Tareas creadas correctamente.");
  }
}

void SenderTask(void *pvParameters) {
  (void)pvParameters;
  Serial.printf("SenderTask iniciada en Core %d\n", xPortGetCoreID());

  while (true) {
    // Esperar hasta obtener acceso exclusivo a los datos compartidos.
    if (xSemaphoreTake(dataMutex, portMAX_DELAY) == pdTRUE) {
      // INICIO del acceso protegido.
      sharedData.temperature += 0.1f; // Simulacion: no usa un sensor real.
      newDataAvailable = true;
      // FIN del acceso protegido.

      xSemaphoreGive(dataMutex);

      // Imprimir fuera del Mutex para no retenerlo durante la salida serial.
      Serial.println("[Sender] Estructura global actualizada");
    }

    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

void ReceiverTask(void *pvParameters) {
  (void)pvParameters;
  Serial.printf("ReceiverTask iniciada en Core %d\n", xPortGetCoreID());

  while (true) {
    SensorData receivedData = {};
    bool hasNewData = false;

    if (xSemaphoreTake(dataMutex, portMAX_DELAY) == pdTRUE) {
      // INICIO del acceso protegido.
      if (newDataAvailable) {
        receivedData = sharedData; // Copia local consistente.
        newDataAvailable = false;  // Marcar la actualizacion como leida.
        hasNewData = true;
      }
      // FIN del acceso protegido.

      xSemaphoreGive(dataMutex);
    }

    // Usar la copia local, NO leer sharedData fuera del Mutex.
    if (hasNewData) {
      Serial.printf(
        "[Receiver] ID: %d, Temp: %.2f (Core %d)\n",
        receivedData.id,
        receivedData.temperature,
        xPortGetCoreID()
      );
    }

    // El Mutex protege el acceso, pero NO espera a que lleguen datos nuevos.
    // Esta pausa evita un ciclo de consulta continua de alta prioridad.
    vTaskDelay(pdMS_TO_TICKS(100));
  }
}

void loop() {
  // El trabajo se realiza en las dos tareas.
  vTaskDelay(pdMS_TO_TICKS(1000));
}