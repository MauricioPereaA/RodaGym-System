void setup() {
  // Inicializa la comunicación serial
  Serial.begin(9600);
  
  // Configura los pines digitales
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(10, INPUT);
  pinMode(11, INPUT);
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    
    if (command == "OUT7") {
      digitalWrite(7, HIGH);
      delay(100); // Espera 0.1 segundos
      digitalWrite(7, LOW);
    } else if (command == "OUT8") {
      digitalWrite(8, HIGH);
      delay(100); // Espera 0.1 segundos
      digitalWrite(8, LOW);
    } else if (command == "IN10") {
      Serial.println(digitalRead(10));
    } else if (command == "IN11") {
      Serial.println(digitalRead(11));
    }
  }
}
