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
    glPointSize(3.0)  # Set point size
    glBegin(GL_POINTS)
    
    for x in np.arange(-10, 10, 0.01):
        # Sin function
        glColor3f(0.5, 0.5, 0.5)  # Gray color
        sin_ = math.sin(x)
        glVertex2f(x, sin_)
        
        # Cos function
        glColor3f(0.9, 0.0, 0.9)  # Purple color
        cos_ = math.cos(x)
        glVertex2f(x, cos_)
        
        # Tan function (Avoid extreme values)
        if -math.pi/2 < x < math.pi/2:
            glColor3f(0.0, 0.5, 0.7)  # Blue color
            tan_ = math.tan(x)
            glVertex2f(x, tan_)
    
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
