from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np
import math

# Global variables for colors
background_color = (1.0, 1.0, 1.0)  # Default white background
function_colors = {
    'sin': (0.5, 0.5, 0.5),      # Gray
    'cos': (0.9, 0.0, 0.9),      # Purple
    'tan': (0.0, 0.5, 0.7),      # Blue
    'cosec': (1.0, 0.5, 0.0),    # Orange
    'sec': (0.0, 1.0, 0.0),      # Green
    'cot': (1.0, 0.0, 1.0)       # Magenta
}

def init():
    glClearColor(*background_color, 1.0)  # Set user-defined background color
    gluOrtho2D(-10.0, 10.0, -10.0, 10.0)  # Set coordinate system

def plot():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the color buffer

    # Draw trigonometric functions
    glPointSize(2.0)  # Set point size

    # Sin function
    glBegin(GL_LINE_STRIP)
    glColor3f(*function_colors['sin'])
    for x in np.arange(-10, 10, 0.01):
        sin_ = math.sin(x)
        glVertex2f(x, sin_)
    glEnd()

    # Cos function
    glBegin(GL_LINE_STRIP)
    glColor3f(*function_colors['cos'])
    for x in np.arange(-10, 10, 0.01):
        cos_ = math.cos(x)
        glVertex2f(x, cos_)
    glEnd()

    # Tan function (Avoid extreme values)
    glBegin(GL_LINE_STRIP)
    glColor3f(*function_colors['tan'])
    for x in np.arange(-10, 10, 0.01):
        if (x % (math.pi/2)) != 0:  # Avoid vertical asymptotes
            tan_ = math.tan(x)
            if abs(tan_) < 10:  # Limit range to avoid extreme values
                glVertex2f(x, tan_)
    glEnd()

    # Cosec function (1/sin) (Avoid values where sin(x) is zero)
    glBegin(GL_LINE_STRIP)
    glColor3f(*function_colors['cosec'])
    for x in np.arange(-10, 10, 0.01):
        sin_ = math.sin(x)
        if abs(sin_) > 0.01:  # Avoid division by zero
            cosec_ = 1 / sin_
            if abs(cosec_) < 10:  # Limit range
                glVertex2f(x, cosec_)
    glEnd()

    # Sec function (1/cos) (Avoid values where cos(x) is zero)
    glBegin(GL_LINE_STRIP)
    glColor3f(*function_colors['sec'])
    for x in np.arange(-10, 10, 0.01):
        cos_ = math.cos(x)
        if abs(cos_) > 0.01:  # Avoid division by zero
            sec_ = 1 / cos_
            if abs(sec_) < 10:  # Limit range
                glVertex2f(x, sec_)
    glEnd()

    # Cot function (1/tan) (Avoid values where tan(x) is zero)
    glBegin(GL_LINE_STRIP)
    glColor3f(*function_colors['cot'])
    for x in np.arange(-10, 10, 0.01):
        if (x % (math.pi)) != 0:  # Avoid vertical asymptotes
            tan_ = math.tan(x)
            if abs(tan_) > 0.01:  # Avoid division by zero
                cot_ = 1 / tan_
                if abs(cot_) < 10:  # Limit range
                    glVertex2f(x, cot_)
    glEnd()

    # Draw X and Y axes
    glColor3f(0.0, 0.0, 0.0)  # Black color for axes
    glBegin(GL_LINES)
    glVertex2f(-10.0, 0.0)
    glVertex2f(10.0, 0.0)
    glVertex2f(0.0, 10.0)
    glVertex2f(0.0, -10.0)
    glEnd()

    glFlush()  # Ensure all OpenGL commands are executed

def main():
    global background_color, function_colors

    # Get user input for colors
    try:
        print("Set desired colors for background and trigonometric functions:")
        bg_input = input("Enter background color (R G B) [0.0-1.0] (default: 1.0 1.0 1.0): ").strip()
        if bg_input:
            bg_vals = list(map(float, bg_input.split()))
            if len(bg_vals) == 3:
                background_color = tuple(bg_vals)

        print("\nSet colors for each trigonometric function (R G B) [0.0-1.0]:")
        for func_name in function_colors.keys():
            color_input = input(f"Enter color for {func_name} (default: {function_colors[func_name]}): ").strip()
            if color_input:
                try:
                    color_vals = list(map(float, color_input.split()))
                    if len(color_vals) == 3:
                        function_colors[func_name] = tuple(color_vals)
                except ValueError:
                    print(f"Invalid color for {func_name}, using default.")

    except (ValueError, KeyboardInterrupt):
        print("Using default colors.")

    glutInit()  # Initialize GLUT
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)  # Set display mode
    glutInitWindowSize(1000, 1000)  # Set window size
    glutInitWindowPosition(50, 50)  # Set window position
    glutCreateWindow(b"All Trigonometric Functions with Custom Colors")  # Updated title

    init()  # Initialize OpenGL settings
    glutDisplayFunc(plot)  # Register the display function

    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
