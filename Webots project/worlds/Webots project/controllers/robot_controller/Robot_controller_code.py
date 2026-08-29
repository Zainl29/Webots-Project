"""coursework_2 controller."""

from controller import Robot

# Constants
TIMESTEP = 32
MOTOR_VELOCITY = 3.0  
ARM_UP_TIMEOUT = 0.9  # Time to lift arm
APPROACH_DISTANCE = 0.20
GROUND_SENSOR_THRESHOLD = 450
TARGET_SENSOR_THRESHOLD = 180
BASKET_SENSOR_THRESHOLD = 950
OBSTACLE_SENSOR_THRESHOLD = 500
GRIPPER_OPEN = 0.0
GRIPPER_CLOSE = 0.05  # Reduced value for gentler grip
GRIPPER_VELOCITY = 0.1  # 0.2 Slower velocity for smoother grip


# Create Robot instance
robot = Robot()

objtype = -1
boxes = 3

# Motor Initialization
motor_names = ['wheel1', 'wheel2']
motors = [robot.getDevice(name) for name in motor_names]
for motor in motors:
    motor.setPosition(float('inf'))
    motor.setVelocity(0.0)

# Device Initialization
ground_sensor = robot.getDevice('GroundSensor')
target_sensor = robot.getDevice('TargetSensor')
basket_sensor1 = robot.getDevice('BasketSensor1')
basket_sensor2 = robot.getDevice('BasketSensor2')
basket_sensor3 = robot.getDevice('BasketSensor3')
obstacle_sensor1 = robot.getDevice('ObstacleSensor1')
obstacle_sensor2 = robot.getDevice('ObstacleSensor2')
ground_sensor.enable(TIMESTEP)
target_sensor.enable(TIMESTEP)
basket_sensor1.enable(TIMESTEP)
basket_sensor2.enable(TIMESTEP)
basket_sensor3.enable(TIMESTEP)
obstacle_sensor1.enable(TIMESTEP)
obstacle_sensor2.enable(TIMESTEP)

arm_part1 = robot.getDevice("ArmPart1")
arm_part1.setPosition(float('inf'))
arm_part1.setVelocity(0.0)

gripper_finger_one = robot.getDevice("GripperFingerOne")
gripper_finger_two = robot.getDevice("GripperFingerTwo")
gripper_finger_one.setPosition(GRIPPER_OPEN)
gripper_finger_two.setPosition(GRIPPER_OPEN)

camera1 = robot.getDevice("camera1")
camera1.enable(TIMESTEP)
camera1.recognitionEnable(TIMESTEP)

# State Definitions
IDLE, AVOID, APPROACH, ADJUST1, ADJUST2, ARMDOWN, ARMGRAB, ARMUP, ROTATE1, ROTATE2, APPROACHBASKET1, APPROACHBASKET2, APPROACHBASKET3, DROP = range(14)
STATE_TIMEOUTS = {ARMUP: ARM_UP_TIMEOUT}

current_state = APPROACH
state_start_time = robot.getTime()


# State Transition Helper
def change_state(new_state):
    global current_state, state_start_time 
    print(f"Changing state to {new_state}")
    current_state = new_state
    state_start_time = robot.getTime()


# Helper Functions
def set_motor_speeds(left_speed, right_speed):
    motors[0].setVelocity(left_speed)
    motors[1].setVelocity(right_speed)
        

def open_gripper():
    gripper_finger_one.setPosition(GRIPPER_OPEN)
    gripper_finger_two.setPosition(GRIPPER_OPEN)
    gripper_finger_one.setVelocity(GRIPPER_VELOCITY)
    gripper_finger_two.setVelocity(GRIPPER_VELOCITY)

def close_gripper():
    gripper_finger_one.setPosition(GRIPPER_CLOSE)
    gripper_finger_two.setPosition(-GRIPPER_CLOSE)
    gripper_finger_one.setVelocity(GRIPPER_VELOCITY)
    gripper_finger_two.setVelocity(GRIPPER_VELOCITY)
    
def target_detected():
    return len(camera1.getRecognitionObjects()) > 0
    

# State Behaviors
def idle():
    set_motor_speeds(0, 0)
    
    
def avoid_obstacle(): 
    obj = camera1.getRecognitionObjects()
    
    if len(obj) > 0:
       
        change_state(APPROACH)
        return
        
    left_obstacle = obstacle_sensor2.getValue()
    right_obstacle = obstacle_sensor1.getValue()
    
    if left_obstacle > OBSTACLE_SENSOR_THRESHOLD and right_obstacle > OBSTACLE_SENSOR_THRESHOLD:
    
        set_motor_speeds(MOTOR_VELOCITY, -MOTOR_VELOCITY)
        
    elif left_obstacle > OBSTACLE_SENSOR_THRESHOLD:
    
        set_motor_speeds(MOTOR_VELOCITY, -MOTOR_VELOCITY)
        
    elif right_obstacle > OBSTACLE_SENSOR_THRESHOLD:
    
        set_motor_speeds(-MOTOR_VELOCITY, MOTOR_VELOCITY)
        
    else:
        set_motor_speeds(MOTOR_VELOCITY, MOTOR_VELOCITY)


def approach():
   
    obj = camera1.getRecognitionObjects()
    if not obj:
        change_state(AVOID)  
        return           
       
    set_motor_speeds(MOTOR_VELOCITY, MOTOR_VELOCITY)
    pos = obj[0].getPosition()
    print('aaa', pos[0], pos[1], pos[2])
    global objtype
    color = obj[0].getColors()
    if pos[0] < APPROACH_DISTANCE:
       
        if color[2] == 0.1:
            objtype = 1
        elif color[2] == 0.2:
            objtype = 2
        elif color[2] == 0.3:
            objtype = 3
        change_state(ADJUST1)  


def move_arm_down():
    idle()
    arm_part1.setVelocity(0.1)
    if ground_sensor.getValue() < GROUND_SENSOR_THRESHOLD:
        arm_part1.setVelocity(0)
        change_state(ARMGRAB)

def grab_object():
    idle()
    close_gripper()
    if target_sensor.getValue() < TARGET_SENSOR_THRESHOLD:
        change_state(ARMUP)

def move_arm_up():
    idle()
    arm_part1.setVelocity(-1)
    if robot.getTime() - state_start_time > STATE_TIMEOUTS[ARMUP]:
        arm_part1.setVelocity(0)
        change_state(ROTATE1)

def rotate(a):
    global objtype
    set_motor_speeds(-2, 2)
        
    obj = camera1.getRecognitionObjects()  
    if len(obj) > 0:
        for i in range(len(obj)):
            pos = obj[i].getPosition() 
            color = obj[i].getColors() 
            print(a, pos[0], pos[1], color[0], objtype)
            if a == 1:
                if pos[1] > 0.018 and color[0] == 0.1 and objtype == 1:
                    change_state(APPROACHBASKET1)
                elif pos[1] > 0.018 and color[0] == 0.2 and objtype == 2:
                    change_state(APPROACHBASKET2)
                elif pos[1] > 0.018 and color[0] == 0.3 and objtype == 3:
                    change_state(APPROACHBASKET3)
            elif a == 2 and pos[1] > 0.000001 and pos[0] > 0.3 and color[0] == 0.0:
                change_state(APPROACH)
    
def approach_basket1():  
    set_motor_speeds(MOTOR_VELOCITY, MOTOR_VELOCITY)
    if basket_sensor1.getValue() < BASKET_SENSOR_THRESHOLD or basket_sensor2.getValue() < BASKET_SENSOR_THRESHOLD:
        change_state(DROP)
        
def approach_basket2():
    set_motor_speeds(MOTOR_VELOCITY, MOTOR_VELOCITY)
    if basket_sensor1.getValue() < BASKET_SENSOR_THRESHOLD or basket_sensor2.getValue() < BASKET_SENSOR_THRESHOLD:
        change_state(DROP)
        
def approach_basket3():
    set_motor_speeds(MOTOR_VELOCITY, MOTOR_VELOCITY)
    if basket_sensor1.getValue() < BASKET_SENSOR_THRESHOLD or basket_sensor2.getValue() < BASKET_SENSOR_THRESHOLD:
        change_state(DROP)

def drop_object():
    global boxes
    idle()
    open_gripper() 
    boxes -= 1
    if boxes > 0:
        change_state(ROTATE2)
       
    
def adjust(): 
    global objtype
    idle()
    
    set_motor_speeds(0.5, -0.5)
    obj = camera1.getRecognitionObjects()
    pos = obj[0].getPositionOnImage()
    color = obj[0].getColors()
    print('d1 ', pos[0], pos[1])
    if pos[0] > 34 and pos[0] < 37:
        if color[2] == 0.1:
          objtype = 1
        elif color[2] == 0.2:
          objtype = 2
        elif color[2] == 0.3:
          objtype = 3
        print('objtype1', objtype)
        change_state(ARMDOWN)
    
    elif pos[0] > 36:
        if color[2] == 0.1:
            objtype = 1
        elif color[2] == 0.2:
            objtype = 2
        elif color[2] == 0.3:
            objtype = 3
        print('objtype2', objtype)
        change_state(ADJUST2)
        
    else:
        change_state(ADJUST1)

    
            
def adjust2(): 
    global objtype
    idle() 
    
    set_motor_speeds(-0.5, 0.5)
    print('ADJUST2')
    if target_detected():
        obj = camera1.getRecognitionObjects()
        pos = obj[0].getPositionOnImage()
        color = obj[0].getColors()
        print('d2 ', pos[0], pos[1])
        if pos[0] < 36:
            if color[2] == 0.1:
                objtype = 1
            elif color[2] == 0.2:
                objtype = 2
            elif color[2] == 0.3:
                objtype = 3
            print('objtype', objtype)
            change_state(ARMDOWN)

        
        
   

# Main loop
while robot.step(TIMESTEP) != -1:
            
    if current_state == IDLE:
        idle()
    elif current_state == AVOID:
        avoid_obstacle()
    elif current_state == APPROACH:
        approach()
    elif current_state == ARMDOWN:
        move_arm_down()
    elif current_state == ADJUST1:
        adjust()
    elif current_state == ARMGRAB:
        grab_object()
    elif current_state == ARMUP:
        move_arm_up()
    elif current_state == ROTATE1:
        rotate(1)
    elif current_state == ROTATE2:
        rotate(2)
    elif current_state == APPROACHBASKET1:
        approach_basket1()
    elif current_state == APPROACHBASKET2:
        approach_basket2()
    elif current_state == APPROACHBASKET3:
        approach_basket3()
    elif current_state == DROP:
        drop_object()