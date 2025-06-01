#include <Wire.h>
#include <stdio.h>


  int analogAngle = A0; // potentiometer wiper (middle terminal) connected to analog pin 0
  int analogPressure = A1; // pressure sensor mounted in tank connected to analog pin 1
                        // outside leads to ground and +5V
    int angleRead = 0;  // variable to store the value read
    int initAngleRead = 0;
    float angleVoltage = 0.0;
    float angle = 0.0;
    float prev_angle = 0.0;
    float angle_kalman = 0.0;

    int pressureRead = 0;
    double pressureVoltage = 0.0;
    double pressure = 0.0;
    int initPressureRead = 0;

    uint32_t timer;

    void setup() {
      Serial.begin(115200);           //  setup serial
      delay(2000);
      //load value of zero pressure and angle to calibrate
      initPressureRead = analogRead(analogPressure); 
      initAngleRead = analogRead(analogAngle);
      //100 is 0bar
      //159 is 1bar
      //238 is 2bar
      //323 is 3bar
      //413 is 4bar
      //493 is 5bar
      // just for kalman filtering - not in use, maybe in future.
      angle = analogRead(analogAngle)*(300.0/1023);
      prev_angle = angle;
      timer = micros();
    }

    void loop() {
      // read from sensors
      angleRead = analogRead(analogAngle) - initAngleRead;  // read the input pin
      pressureRead = analogRead(analogPressure);
      double dt = (double)(micros() - timer) / 1000000; // Calculate delta time
      timer = micros();
      angle = (angleRead-0)*(300.0/1023);
      //kalmanAngle.setAngle(angleRead);
      // (angleRead - angleOffset)*sensitivity
      angleVoltage = (angleRead-0)*(5.0/1023);
      pressureVoltage = (pressureRead-0)*(5.0/1023);


      // Serial.print("AngleVoltage_[V]:"); Serial.print(angleVoltage); Serial.print(", ");
      // Serial.print("Angle_[deg]:"); Serial.print(angle,2); Serial.print(", ");
      // Serial.print("Kalman_Angle_[deg]:"); Serial.print(angle_kalman,2); Serial.print(", ");
      // Serial.print("PressureVoltage_[V]:"); Serial.print(pressureVoltage,2); Serial.print(", ");
      // pressure = (pressureRead-0)*(10.0/1023);
      pressure = interpolate(pressureRead);
      // Serial.print("Pressure_[bar]:"); Serial.print(pressure,2); Serial.print("\n");
      Serial.println(String(angle) + ";" + String(pressure));
      delay(2);
    }

    double interpolate(int x){
      double y;
      //double coeffs[] = {0.0, 0.0, 0.0124030369503467, -1.06794029604973}; 
      double coeffs[] = {4.10165569095784e-08, -4.15475598306762e-05, 0.0249390085657180, -2.10853535628821};
      y = coeffs[0]*pow(x,3) + coeffs[1]*pow(x,2) + coeffs[2]*x + coeffs[3];
      if (y<=0.0) y=0.0;
      return y;
    }
