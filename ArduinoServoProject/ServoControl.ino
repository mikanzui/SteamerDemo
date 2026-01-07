/*
 * Arduino Servo Control Script
 * 
 * This script controls a servo motor connected to Pin 9.
 * Logic:
 * - When Pin 2 is bridged to Ground (LOW): Rotate servo 10 degrees from base.
 * - When Pin 2 is NOT bridged (HIGH): Return to base position.
 * 
 * Includes safety limits to prevent the servo from trying to move beyond 0-180 degrees.
 */

#include <Servo.h>

Servo myServo;  // Create servo object to control a servo

// Pin Definitions
const int BUTTON_PIN = 2;  // Input pin (bridged to ground)
const int SERVO_PIN = 9;   // Servo control pin

// Configuration
const int BASE_ANGLE = 90; // Starting angle (0 to 180)
const int ROTATION_AMOUNT = 10; // How many degrees to rotate when triggered

void setup() {
  // Initialize the servo pin
  myServo.attach(SERVO_PIN);
  
  // Initialize the button pin with internal pull-up resistor
  // This ensures the pin reads HIGH when not connected, and LOW when bridged to ground
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Move servo to initial position
  myServo.write(BASE_ANGLE);
}

void loop() {
  // Read the state of the pin
  // LOW means connected to Ground (Bridged)
  // HIGH means open (Not bridged)
  int pinState = digitalRead(BUTTON_PIN);
  
  int targetAngle;

  if (pinState == LOW) {
    // Bridged to ground: Rotate +10 degrees
    targetAngle = BASE_ANGLE + ROTATION_AMOUNT;
  } else {
    // Not bridged: Return to base (do the opposite)
    targetAngle = BASE_ANGLE;
  }

  // --- LIMITS SAFETY CHECK ---
  // Ensure the target angle never exceeds the servo's physical limits (0-180)
  if (targetAngle > 180) {
    targetAngle = 180;
  }
  if (targetAngle < 0) {
    targetAngle = 0;
  }

  // Move the servo
  myServo.write(targetAngle);
  
  // Small delay to prevent jitter and allow servo to reach position
  delay(50);
}
