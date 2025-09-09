from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Define the coordinates of the start and end point
x1, y1 = 100, 100
x2, y2 = 400, 300

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Set background color to black
    gluOrtho2D(0, 500, 0, 500)        # Set the coordinate system (2D)

def draw_pixel(x, y):
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

def dda_line(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    steps = max(abs(dx), abs(dy))  # Number of steps needed

    x_inc = dx / float(steps)
    y_inc = dy / float(steps)

    x = x1
    y = y1

    glColor3f(1.0, 1.0, 1.0)  # Set line color to white

    for i in range(int(steps) + 1):
        draw_pixel(round(x), round(y))
        x += x_inc
        y += y_inc

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    dda_line(x1, y1, x2, y2)
    glFlush()

# Main function
glutInit()
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
glutInitWindowSize(500, 500)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"DDA Line Drawing Algorithm - OpenGL")
init()
glutDisplayFunc(display)
glutMainLoop()
