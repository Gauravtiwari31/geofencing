from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Triangle vertices
triangle_vertices = [
    (1.0, 1.0),
    (2.0, 3.0),
    (3.0, 1.0)
]

def draw_triangle(vertices, color):
    glColor3f(*color)  # Set the drawing color
    glBegin(GL_TRIANGLES)
    for vertex in vertices:
        glVertex2f(*vertex)
    glEnd()

def plot():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the color buffer

    # Draw original triangle
    draw_triangle(triangle_vertices, (1.0, 0.0, 0.0))  # Red color

    # Reflect in the four quadrants
    # Quadrant (+x, +y)
    draw_triangle(triangle_vertices, (1.0, 0.0, 0.0))  # Red

    # Quadrant (-x, +y)
    reflected_triangle1 = [(-x, y) for (x, y) in triangle_vertices]
    draw_triangle(reflected_triangle1, (0.0, 1.0, 0.0))  # Green

    # Quadrant (-x, -y)
    reflected_triangle2 = [(-x, -y) for (x, y) in triangle_vertices]
    draw_triangle(reflected_triangle2, (0.0, 0.0, 1.0))  # Blue

    # Quadrant (+x, -y)
    reflected_triangle3 = [(x, -y) for (x, y) in triangle_vertices]
    draw_triangle(reflected_triangle3, (1.0, 1.0, 0.0))  # Yellow

    # Draw X and Y axes
    glColor3f(0.0, 0.0, 0.0)  # Black color for axes
    glBegin(GL_LINES)
    glVertex2f(-10.0, 0.0)
    glVertex2f(10.0, 0.0)
    glVertex2f(0.0, 10.0)
    glVertex2f(0.0, -10.0)
    glEnd()

    glFlush()  # Ensure all OpenGL commands are executed

def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)  # Set background color to white
    gluOrtho2D(-10.0, 10.0, -10.0, 10.0)  # Set coordinate system

def main():
    glutInit()  # Initialize GLUT
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)  # Set display mode
    glutInitWindowSize(1000, 1000)  # Set window size
    glutInitWindowPosition(50, 50)  # Set window position
    glutCreateWindow(b"Triangle Reflections")  # Create a window with title "Triangle Reflections"
    
    init()  # Initialize OpenGL settings
    glutDisplayFunc(plot)  # Register the display function
    
    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
