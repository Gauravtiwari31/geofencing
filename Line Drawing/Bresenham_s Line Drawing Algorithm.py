from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Initialize window size and coordinates
window_width = 500
window_height = 500
x1, y1 = 50, 50    # Starting point
x2, y2 = 400, 300  # Ending point

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Black background
    gluOrtho2D(0, window_width, 0, window_height)  # 2D orthographic projection

def plot_point(x, y):
    glBegin(GL_POINTS)
    glVertex2i(x, y)
    glEnd()

def bresenham_line(x1, y1, x2, y2):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x, y = x1, y1

    sx = 1 if x2 > x1 else -1
    sy = 1 if y2 > y1 else -1

    if dy <= dx:
        p = 2 * dy - dx
        for _ in range(dx):
            plot_point(x, y)
            x += sx
            if p >= 0:
                y += sy
                p += 2 * (dy - dx)
            else:
                p += 2 * dy
    else:
        p = 2 * dx - dy
        for _ in range(dy):
            plot_point(x, y)
            y += sy
            if p >= 0:
                x += sx
                p += 2 * (dx - dy)
            else:
                p += 2 * dx

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(1.0, 1.0, 1.0)  # White color for drawing
    glPointSize(2)  # Point size
    bresenham_line(x1, y1, x2, y2)
    glFlush()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Bresenham Line Drawing - OpenGL Python")
    init()
    glutDisplayFunc(display)
    glutMainLoop()

if __name__ == "__main__":
    main()
