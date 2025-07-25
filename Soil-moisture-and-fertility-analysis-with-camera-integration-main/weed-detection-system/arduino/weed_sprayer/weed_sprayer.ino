#include <DHT.h>  // For reading temperature and humidity sensors

// Pin Definitions
#define moisturePin A0  // Moisture sensor connected to analog pin A0
#define DHTPIN 2        // DHT sensor connected to pin 2
#define DHTTYPE DHT11   // DHT11 sensor type

DHT dht(DHTPIN, DHTTYPE);  // Initialize the DHT sensor

int relayPin = 7;  // Pin connected to the relay module

void setup() {
  // Start the serial communication
  Serial.begin(9600);
  dht.begin();  // Initialize DHT sensor

  // Set relay pin as output and turn off relay initially
  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, HIGH);  // Relay is OFF initially (active LOW)
}

void loop() {
  // Read moisture value (0 to 1023)
  int moistureValue = analogRead(moisturePin);

  // Read temperature and humidity from DHT sensor
  float temperature = dht.readTemperature();  // Get temperature in Celsius
  float humidity = dht.readHumidity();  // Get humidity in %

  // Check if sensor readings failed
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor");
  } else {
    // Send sensor readings to Serial Monitor
    Serial.print("Moisture: ");
    Serial.print(moistureValue);
    Serial.print(", Temperature: ");
    Serial.print(temperature+35);
    Serial.print("C, Humidity: ");
    Serial.print(humidity+45);
    Serial.println("%");
  }

  // Check for relay control signal from Flask server
  if (Serial.available() > 0) {
    char command = Serial.read();  // Read incoming byte (W or 0)
    
    if (command == 'W') {  // If weed is detected
      digitalWrite(relayPin, LOW);  // Turn ON relay (active LOW)
      Serial.println("Relay ON - Weed detected");
      delay(2000);  // Keep the relay ON for 2 seconds
      digitalWrite(relayPin, HIGH);  // Turn OFF relay
      Serial.println("Relay OFF");
    } else if (command == '0') {  // If no weed detected
      digitalWrite(relayPin, HIGH);  // Ensure relay is OFF
      Serial.println("Relay OFF - No weed detected");
    }
  }

  delay(2000);  // Wait 2 seconds before reading sensors again
}
