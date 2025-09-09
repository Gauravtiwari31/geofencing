from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

def clear_screen():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Set background color to black
    gluOrtho2D(-1.0, 1.0, -1.0, 1.0)  # Set coordinate system

def plot_points():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the color buffer
    glColor3f(0.0, 1.0, 0.0)  # Set drawing color to green
    glPointSize(10.0)  # Set point size (optional, note this affects points, not lines)
    
    glBegin(GL_LINES)  # Begin drawing lines
    glVertex2f(0, 0)  # Line from (0,0) to (1,0)
    glVertex2f(1, 0)
    glVertex2f(0, 0)  # Line from (0,0) to (0,1)
    glVertex2f(0, 1)
    glVertex2f(0, 0)  # Line from (0,0) to (1,1)
    glVertex2f(1, 1)
    glEnd()
    
    glFlush()  # Ensure all OpenGL commands are executed

def main():
    glutInit()  # Initialize GLUT
    glutInitDisplayMode(GLUT_RGB)  # Set display mode
    glutInitWindowSize(1000, 1000)  # Set window size
    glutInitWindowPosition(100, 100)  # Set window position
    glutCreateWindow(b"OpenGL Window")  # Create window with title "OpenGL Window"
    
    clear_screen()  # Set clear color and coordinate system
    glutDisplayFunc(plot_points)  # Register display function
    
    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
