/*
 * Arduino Nano RP2040 Connect - Servo Web Control
 * 
 * This script connects to an existing WiFi network.
 * Edit arduino_secrets.h with your WiFi SSID and Password.
 * Open the Serial Monitor to see the IP address, then visit that IP
 * to configure the servo angles.
 * 
 * Hardware:
 * - Servo on Pin 9
 * - Switch/Bridge on Pin 2 (to Ground)
 */

#include <SPI.h>
#include <WiFiNINA.h>
#include <Servo.h>

// --- Configuration ---
char ssid[] = "pppppppp";      // Network Name
char pass[] = "";  // Network Password
int keyIndex = 0;                 // your network key Index number (needed only for WEP)

int status = WL_IDLE_STATUS;
WiFiServer server(80);

// --- Servo & Logic ---
Servo myServo;
const int SERVO_PIN = 9;
const int BUTTON_PIN = 2;

// Variables controlled by Web Interface
int baseAngle = 90;      // Default base angle
int pushAmount = 10;     // Default push amount

void setup() {
  // Initialize Serial for debugging
  Serial.begin(9600);

  // --- Hardware Setup ---
  myServo.attach(SERVO_PIN);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // --- WiFi Setup (Access Point Mode) ---
  Serial.println("Access Point Web Server");
Station Mode) ---
  Serial.println("Connecting to WiFi Network...");

  // Check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    while (true);
  }

  // Attempt to connect to WiFi network:
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    status = WiFi.begin(ssid, pass);

    // wait 10 seconds for connection:
    delay(10000);
  }
  
}

void loop() {
  // --- 1. Handle Web Clients ---
  WiFiClient client = server.available();
  if (client) {
    handleClient(client);
  }

  // --- 2. Servo Logic ---
  int pinState = digitalRead(BUTTON_PIN);
  int targetAngle;

  if (pinState == LOW) {
    // Bridged: Base + Push
    targetAngle = baseAngle + pushAmount;
  } else {
    // Not Bridged: Base
    targetAngle = baseAngle;
  }

  // --- 3. Safety Limits (9g Servo 0-180) ---
  if (targetAngle > 180) targetAngle = 180;
  if (targetAngle < 0) targetAngle = 0;

  myServo.write(targetAngle);
  
  // Small delay for stability
  delay(15); 
}

void handleClient(WiFiClient client) {
  Serial.println("new client");
  String currentLine = "";
  String request = "";
  
  while (client.connected()) {
    if (client.available()) {
      char c = client.read();
      request += c;
      if (c == '\n') {
        if (currentLine.length() == 0) {
          // HTTP headers ended, send response
          
          // Check for GET parameters before sending page
          // Expected format: GET /set?b=90&p=10
          if (request.indexOf("GET /set?") >= 0) {
            parseParams(request);
          }

          sendWebPage(client);
          break;
        } else {
          currentLine = "";
        }
      } else if (c != '\r') {
        currentLine += c;
      }
    }
  }
  client.stop();
  Serial.println("client disconnected");
}

void parseParams(String req) {
  // Simple parsing for "b=" and "p="
  int bIndex = req.indexOf("b=");
  int pIndex = req.indexOf("p=");
  
  if (bIndex > 0) {
    int bEnd = req.indexOf('&', bIndex);
    if (bEnd == -1) bEnd = req.indexOf(' ', bIndex);
    String bVal = req.substring(bIndex + 2, bEnd);
    baseAngle = bVal.toInt();
  }
  
  if (pIndex > 0) {
    int pEnd = req.indexOf('&', pIndex);
    if (pEnd == -1) pEnd = req.indexOf(' ', pIndex);
    String pVal = req.substring(pIndex + 2, pEnd);
    pushAmount = pVal.toInt();
  }
}

void sendWebPage(WiFiClient client) {
  client.println("HTTP/1.1 200 OK");
  client.println("Content-type:text/html");
  client.println();
  
  client.print("<!DOCTYPE HTML><html><head>");
  client.print("<meta name='viewport' content='width=device-width, initial-scale=1'>");
  client.print("<style>");
  client.print("body { font-family: Arial; text-align: center; margin-top: 50px; }");
  client.print("input[type=range] { width: 80%; }");
  client.print(".val { font-weight: bold; color: blue; }");
  client.print("</style></head><body>");
  
  client.print("<h1>Servo Controller</h1>");
  
  // Base Angle Slider
  client.print("<p>Base Angle: <span id='bVal' class='val'>");
  client.print(baseAngle);
  client.print("</span>&deg;</p>");
  client.print("<input type='range' min='0' max='180' value='");
  client.print(baseAngle);
  client.print("' id='bSld' oninput='upd()'>");
  
  // Push Amount Slider
  client.print("<p>Push Amount: <span id='pVal' class='val'>");
  client.print(pushAmount);
  client.print("</span>&deg;</p>");
  client.print("<input type='range' min='-90' max='90' value='");
  client.print(pushAmount);
  client.print("' id='pSld' oninput='upd()'>");
  
  // JavaScript
  client.print("<script>");
  client.print("function upd() {");
  client.print("  var b = document.getElementById('bSld').value;");
  client.print("  var p = document.getElementById('pSld').value;");
  client.print("  document.getElementById('bVal').innerHTML = b;");
  client.print("  document.getElementById('pVal').innerHTML = p;");
  client.print("  fetch('/set?b=' + b + '&p=' + p);");
  client.print("}");
  client.print("</script>");
  
  client.print("</body></html>");
  client.println();
}

void printWiFiStatus() {
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);
  Serial.print("To see this page in action, open a browser to http://");
  Serial.println(ip);
}
