//#### AUTO ORDER PICKER ___ ARDUINO UNO PART

#include <GCodeParser.h>

#include <ESP32_Servo.h>

#define ENDER_PIN 25


#define U_SERVO_PIN 12
#define V_SERVO_PIN 14
#define Y_SERVO_PIN 27

Servo uServo;
Servo vServo;
Servo yServo;

GCodeParser GCode = GCodeParser();



void ender_init(){
  pinMode(ENDER_PIN, INPUT_PULLUP);
}

bool ender_check(){
  return digitalRead(ENDER_PIN);
}




//grab
#define U_SERVO_CLOSED 0
#define U_SERVO_OPENED 180

//выдвижение
#define V_SERVO_OPENED 180
#define V_SERVO_CLOSED 0




void grab_init(){
  uServo.attach(U_SERVO_PIN, 500, 2500);
  vServo.attach(V_SERVO_PIN, 500, 2500);
}

void grab(int v, int u){
  v = constrain(v, V_SERVO_CLOSED, V_SERVO_OPENED); 
  u = constrain(u, U_SERVO_CLOSED, U_SERVO_OPENED);
  //uServo.writeMicroseconds(u);
  //vServo.writeMicroseconds(v);
  uServo.write(u);
  vServo.write(v);
}


void grab_u(int u){
  u = constrain(u, U_SERVO_CLOSED, U_SERVO_OPENED);
  uServo.write(u);
}


void grab_v(int v){
  v = constrain(v, V_SERVO_CLOSED, V_SERVO_OPENED);
  vServo.write(v);
}

void grab_home(){
  grab(V_SERVO_CLOSED, U_SERVO_OPENED);
}




#define LIFT_UP_SPEED     0
#define LIFT_DOWN_SPEED   180
#define LIFT_STOP_SPEED   90

double current_y = 0;

#define LIFT_SPEED_MM_PER_MS  0.004
#define LIFT_UP_SPEED_MM_PER_MS     LIFT_SPEED_MM_PER_MS  
#define LIFT_DOWN_SPEED_MM_PER_MS   LIFT_SPEED_MM_PER_MS

uint32_t y_mm_to_ms(double y_diff){
  uint32_t delayTime = 0;

  if (y_diff > 0){
    delayTime = abs(y_diff) / LIFT_UP_SPEED_MM_PER_MS;
  }
  else if (y_diff < 0){
    delayTime = abs(y_diff) / LIFT_DOWN_SPEED_MM_PER_MS;
  }
  return delayTime;
}

void lift_init(){
  yServo.attach(Y_SERVO_PIN, 500, 2500);
}

void lift_stop(){
  yServo.write(LIFT_STOP_SPEED);
}


void lift_go(double target_y){
  double y_dif = target_y - current_y;
  uint32_t delay_time = y_mm_to_ms(y_dif);
  
  if (y_dif == 0){
    lift_stop();
  }
  else if (y_dif > 0){
    yServo.write(LIFT_UP_SPEED);
  }
  else{
    yServo.write(LIFT_DOWN_SPEED);
  } 
  delay(delay_time);
  current_y = target_y;
  lift_stop();
}

void lift_set_origin(){
  current_y = 0;
}


void lift_home(){
  yServo.write(LIFT_DOWN_SPEED);
  while (!ender_check());
  lift_stop();
  lift_set_origin();
}






void g1(float y, int v, int u){
  Serial.println("G1 cmd - go to absolute coordinate..");
  Serial.println("Y: " + String(y) + "\tV: " + String(v) + "\tU: " + String(u));
  
  if (v != -1){
    grab_v(v);
  }
  if (u != -1){
    grab_u(u);
  }
  if (y != -1){
    lift_go(y);
  }
}


void g28(){
  Serial.println("G28 cmd - Home..");
  grab_home();
  delay(1000);
  lift_home();
}




void setup() 
{
  Serial.begin(115200);
  ender_init();
  grab_init();
  lift_init();
  delay(100);
  g28();
}

void loop() 
{ 
  if (Serial.available() > 0)
  {
    if (GCode.AddCharToLine(Serial.read()))
    {
      Serial.println(GCode.line);
      GCode.ParseLine();
      GCode.RemoveCommentSeparators();
      if (GCode.HasWord('G'))
      {
        int code = (int)GCode.GetWordValue('G'); 
        if (code == 1){
          int y = (GCode.HasWord('Y')) ? (int)GCode.GetWordValue('Y') : -1;
          int v = (GCode.HasWord('V')) ? (int)GCode.GetWordValue('V') : -1;
          int u = (GCode.HasWord('U')) ? (int)GCode.GetWordValue('U') : -1;
          g1(y,v,u);
        }
        else if (code == 28){
          g28();
        }
      }
    }
  }
}
