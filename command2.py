from inputs import get_gamepad
import math
import threading
import serial
import time

#from using command -----  dmesg | tail -f
#ARDUINO_PORT = "/dev/ttyACM0"
ARDUINO_PORT = "COM4"

#ARDUINO_PORT = "COM4" # Should probably make this automatically look for the arduino in
              # the future, or at the very least make it fetch command line
              # argument.

class XboxController():
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):

        # Controller State variables:
        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

        # Initialize the daemon thread which monitors the gamepad events
        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    # return the buttons/triggers we want to use
    # TODO: decide which buttons we want to use
    def read(self):
        #note: "A" is for testing
        return [self.A, self.LeftJoystickX, self.LeftJoystickY, self.RightJoystickX, self.RightJoystickY,
        self.RightBumper, self.LeftBumper, self.RightTrigger, self.LeftTrigger], 0#self.CameraToggle

    # Update the state varibles every time there is an event
    def _monitor_controller(self):
        while True:
            events = get_gamepad()
            for event in events:
                if event.code == 'ABS_Y':
                    self.LeftJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_X':
                    self.LeftJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_RY':
                    self.RightJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_RX':
                    self.RightJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_Z':
                    self.LeftTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.RightTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'BTN_TL':
                    self.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    self.RightBumper = event.state
                elif event.code == 'BTN_SOUTH':
                    self.A = event.state
                elif event.code == 'BTN_NORTH':
                    self.Y = event.state
                elif event.code == 'BTN_WEST':
                    self.X = event.state
                elif event.code == 'BTN_EAST':
                    self.B = event.state
                elif event.code == 'BTN_THUMBL':
                    self.LeftThumb = event.state
                elif event.code == 'BTN_THUMBR':
                    self.RightThumb = event.state
                elif event.code == 'BTN_SELECT':
                    self.CameraToggle = event.state
                elif event.code == 'BTN_START':
                    self.Start = event.state

def wait(ser, timeout):
    t = time.time()
    while ser.in_waiting == 0:
        if time.time() - t > timeout:
            print("wait timed out")
            break
    print("receive wait: " + str(time.time() - t) + "s")

#put the loop function in a big while loop with a try clause so the program automatically sleeps and restarts when an error is thrown
if __name__ == '__main__':
    controller = XboxController()
    ser = serial.Serial(ARDUINO_PORT, 9500, timeout=0.01)

    time.sleep(1)

    while True:
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        '''raw inputs:
        [self.A (testing), self.LeftJoystickX, self.LeftJoystickY, self.RightJoystickX, self.RightJoystickY,
        self.RightBumper, self.LeftBumper, self.RightTrigger, self.LeftTrigger]'''

        raw, toggle_camera = controller.read() #9 inputs total for instructions
 
        instructions = [raw[0], 100, 100, 100, 100, 100, 100, 100] #set

        dx, dy = raw[1], raw[2]
        turnx, turny = raw[3], raw[4]
        rt, lt = raw[7], raw[8]
        if (raw[5] > 0.5):
            instructions[7] = 0
        elif (raw[6] > 0.5):
            instructions[7] = 180
        if (abs(dx + dy) > 0.05):
            #x+y for -1 to 1, convert to 0 to 200 scale            
            instructions[1] =  (dx + dy) / ((abs(dx) + abs(dy)) / max(abs(dx), abs(dy)))
            instructions[1] = int(abs(instructions[1] - 1) * 100)
            instructions[5] = 200 - instructions[1]

            #(x+y)/sqrt(x^2+y^2) for -1 to 1, convert to 0 to 200 scale
            instructions[3] =  (dx - dy) / ((abs(dx) + abs(dy)) / max(abs(dx), abs(dy)))
            instructions[3] = int(abs(instructions[3] - 1) * 100)
            instructions[4] = 200 - instructions[3]
        #if (abs(turnx + turny) > 0.05):
            #intructions[3] = instruction[3] * 0.
            #intructions[3] = instruction[3] * 
        if (abs(rt) > 0.05 or abs(lt) > 0.05):
            instructions[2] = int(100 + (rt * 100) - (lt * 100))
            instructions[6] = instructions[2]

        print("sending: " + str(instructions))

        ser.write(bytearray(instructions)) #write a bytearray that takes a list of integers from 0 to 255
        

        time.sleep(.05)
        
        wait(ser, 2) #waits for arduino response for up to 2 seconds

        response = ser.readline()
        print(response)