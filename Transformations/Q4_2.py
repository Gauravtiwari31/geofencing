from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import numpy as np
import math

def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)  # Set background color to white
    gluOrtho2D(-10.0, 10.0, -10.0, 10.0)  # Set coordinate system

def plot():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the color buffer

    # Draw trigonometric functions
    glPointSize(2.0)  # Set point size

    # Sin function
    glBegin(GL_LINE_STRIP)
    glColor3f(0.5, 0.5, 0.5)  # Gray color
    for x in np.arange(-10, 10, 0.01):
        sin_ = math.sin(x)
        glVertex2f(x, sin_)
    glEnd()

    # Cos function
    glBegin(GL_LINE_STRIP)
    glColor3f(0.9, 0.0, 0.9)  # Purple color
    for x in np.arange(-10, 10, 0.01):
        cos_ = math.cos(x)
        glVertex2f(x, cos_)
    glEnd()

    # Tan function (Avoid extreme values)
    glBegin(GL_LINE_STRIP)
    glColor3f(0.0, 0.5, 0.7)  # Blue color
    for x in np.arange(-10, 10, 0.01):
        if (x % (math.pi/2)) != 0:  # Avoid vertical asymptotes
            tan_ = math.tan(x)
            if abs(tan_) < 10:  # Limit range to avoid extreme values
                glVertex2f(x, tan_)
    glEnd()

    # Cosec function (1/sin) (Avoid values where sin(x) is zero)
    glBegin(GL_LINE_STRIP)
    glColor3f(1.0, 0.5, 0.0)  # Orange color
    for x in np.arange(-10, 10, 0.01):
        sin_ = math.sin(x)
        if abs(sin_) > 0.01:  # Avoid division by zero
            cosec_ = 1 / sin_
            glVertex2f(x, cosec_)
    glEnd()

    # Sec function (1/cos) (Avoid values where cos(x) is zero)
    glBegin(GL_LINE_STRIP)
    glColor3f(0.0, 1.0, 0.0)  # Green color
    for x in np.arange(-10, 10, 0.01):
        cos_ = math.cos(x)
        if abs(cos_) > 0.01:  # Avoid division by zero
            sec_ = 1 / cos_
            glVertex2f(x, sec_)
    glEnd()

    # Cot function (1/tan) (Avoid values where tan(x) is zero)
    glBegin(GL_LINE_STRIP)
    glColor3f(1.0, 0.0, 1.0)  # Magenta color
    for x in np.arange(-10, 10, 0.01):
        if (x % (math.pi)) != 0:  # Avoid vertical asymptotes
            tan_ = math.tan(x)
            if abs(tan_) > 0.01:  # Avoid division by zero
                cot_ = 1 / tan_
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
    glutInit()  # Initialize GLUT
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)  # Set display mode
    glutInitWindowSize(1000, 1000)  # Set window size
    glutInitWindowPosition(50, 50)  # Set window position
    glutCreateWindow(b"Trigonometric Functions")  # Create a window with title "Trigonometric Functions"
    
    init()  # Initialize OpenGL settings
    glutDisplayFunc(plot)  # Register the display function
    
    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
