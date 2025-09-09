from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Set background color to black
    gluOrtho2D(-10.0, 10.0, -10.0, 10.0)  # Set coordinate system

def draw():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the color buffer

    # Coordinates for the original lines
    x1, x2, x3 = 1, 1, 3
    y1, y2, y3 = 1, 3, 1

    glColor3f(0.5, 0.5, 0.0)  # Set color to olive
    glPointSize(3.0)

    glBegin(GL_LINES)
    # Draw X and Y axes
    glVertex2f(-10.0, 0.0)
    glVertex2f(10.0, 0.0)
    glVertex2f(0.0, 10.0)
    glVertex2f(0.0, -10.0)
    
    # Draw original lines
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glVertex2f(x1, y1)
    glVertex2f(x3, y3)
    
    glVertex2f(x2, y2)
    glVertex2f(x3, y3)

    # Draw reflections across the Y-axis
    glVertex2f(-x1, y1)
    glVertex2f(-x2, y2)
    glVertex2f(-x1, y1)
    glVertex2f(-x3, y3)
    
    glVertex2f(-x2, y2)
    glVertex2f(-x3, y3)

    # Draw reflections across the X-axis
    glVertex2f(x1, -y1)
    glVertex2f(x2, -y2)
    glVertex2f(x1, -y1)
    glVertex2f(x3, -y3)
    
    glVertex2f(x2, -y2)
    glVertex2f(x3, -y3)

    # Draw reflections across both axes
    glVertex2f(-x1, -y1)
    glVertex2f(-x2, -y2)
    glVertex2f(-x1, -y1)
    glVertex2f(-x3, -y3)
    
    glVertex2f(-x2, -y2)
    glVertex2f(-x3, -y3)
    
    glEnd()
    glFlush()

def main():
    glutInit()  # Initialize GLUT
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)  # Set display mode
    glutInitWindowSize(1000, 1000)  # Set window size
    glutInitWindowPosition(50, 50)  # Set window position
    glutCreateWindow(b"Square")  # Create a window with title "Square"
    
    init()  # Initialize OpenGL settings
    glutDisplayFunc(draw)  # Register the display function
    
    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
