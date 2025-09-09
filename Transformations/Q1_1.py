from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys

# Global variables for point and mirror points
point = (1, 2)
mirror_point_x = (1, -2)
mirror_point_y = (-1, 2)

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
    glColor3f(1.0, 0.0, 0.0) # Red color for the original point
    draw_point(point)
    glColor3f(0.0, 1.0, 0.0) # Green color for the mirror image across X-axis
    draw_point(mirror_point_x)
    glColor3f(0.0, 0.0, 1.0) # Blue color for the mirror image across Y-axis
    draw_point(mirror_point_y)

    glColor3f(0.5, 0.5, 0.5) # Gray color for mirror axes
    draw_mirror_line('X')
    draw_mirror_line('Y')
    glFlush()

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(400, 400)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Mirror Image using PyOpenGL")  # Ensure the title is a byte string
    glClearColor(1.0, 1.0, 1.0, 1.0) # White background
    gluOrtho2D(-10, 10, -10, 10) # Set the coordinate system
    glutDisplayFunc(display)
    glutMainLoop()

if __name__ == "__main__":
    main()
