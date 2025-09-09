from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys

# Global variables for point and mirror points
point = (1, 2)
mirror_point = (1, -2)  # Default to mirror point across X-axis
mirror_axis = 'X'  # Default mirror axis

def draw_point(p):
    glPointSize(10)  # Set the point size to 10 (adjust as needed)
    glBegin(GL_POINTS)
    glVertex2f(*p)
    glEnd()

def draw_mirror_line(axis):
    glBegin(GL_LINES)
    if axis == 'X':
        glVertex2f(-10, 0)
        glVertex2f(10, 0)
    elif axis == 'Y':
        glVertex2f(0, -10)
        glVertex2f(0, 10)
    glEnd()

def display():
    glClear(GL_COLOR_BUFFER_BIT)

    # Draw the original point in red
    glColor3f(1.0, 0.0, 0.0)
    draw_point(point)

    # Draw the mirror image in green
    glColor3f(0.0, 1.0, 0.0)
    draw_point(mirror_point)

    # Draw mirror lines in gray
    glColor3f(0.5, 0.5, 0.5)
    draw_mirror_line('X')
    draw_mirror_line('Y')

    glFlush()

def keyboard(key, x, y):
    global point, mirror_point, mirror_axis

    if key == b'x' or key == b'X':
        mirror_axis = 'X'
        mirror_point = (point[0], -point[1])  # Invert y-coordinate for X-axis mirroring
    elif key == b'y' or key == b'Y':
        mirror_axis = 'Y'
        mirror_point = (-point[0], point[1])  # Invert x-coordinate for Y-axis mirroring

    glutPostRedisplay()  # Redraw the scene with updated mirror point

def main():
    global mirror_point  # Ensure global variable can be modified

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(400, 400)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Mirror Image using PyOpenGL")  # Ensure the title is a byte string

    glClearColor(1.0, 1.0, 1.0, 1.0)  # White background
    gluOrtho2D(-10, 10, -10, 10)  # Set the coordinate system

    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)  # Register the keyboard function

    glutMainLoop()

if __name__ == "__main__":
    main()
