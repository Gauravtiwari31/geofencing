from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Triangle vertices - will be set by user input
triangle_vertices = [
    (1.0, 1.0),
    (2.0, 3.0),
    (3.0, 1.0)
]

# Colors for different quadrants
quadrant_colors = {
    'original': (1.0, 0.0, 0.0),    # Red for (+x, +y)
    'x_mirror': (0.0, 1.0, 0.0),    # Green for (-x, +y)
    'y_mirror': (0.0, 0.0, 1.0),    # Blue for (+x, -y)
    'both_mirror': (1.0, 1.0, 0.0)  # Yellow for (-x, -y)
}

def draw_triangle(vertices, color):
    glColor3f(*color)  # Set the drawing color
    glBegin(GL_TRIANGLES)
    for vertex in vertices:
        glVertex2f(*vertex)
    glEnd()

def plot():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the color buffer

    # Draw triangle reflections in all four quadrants

    # Quadrant I (+x, +y) - Original triangle
    draw_triangle(triangle_vertices, quadrant_colors['original'])

    # Quadrant II (-x, +y) - Reflection across Y-axis
    reflected_y_axis = [(-x, y) for (x, y) in triangle_vertices]
    draw_triangle(reflected_y_axis, quadrant_colors['x_mirror'])

    # Quadrant III (-x, -y) - Reflection across both axes
    reflected_both = [(-x, -y) for (x, y) in triangle_vertices]
    draw_triangle(reflected_both, quadrant_colors['both_mirror'])

    # Quadrant IV (+x, -y) - Reflection across X-axis
    reflected_x_axis = [(x, -y) for (x, y) in triangle_vertices]
    draw_triangle(reflected_x_axis, quadrant_colors['y_mirror'])

    # Draw X and Y axes
    glColor3f(0.0, 0.0, 0.0)  # Black color for axes
    glBegin(GL_LINES)
    glVertex2f(-10.0, 0.0)
    glVertex2f(10.0, 0.0)
    glVertex2f(0.0, 10.0)
    glVertex2f(0.0, -10.0)
    glEnd()

    # Add quadrant labels
    glColor3f(0.5, 0.5, 0.5)  # Gray for labels
    # These would be text labels, but for now we'll just use the colors to distinguish

    glFlush()  # Ensure all OpenGL commands are executed

def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)  # Set background color to white
    gluOrtho2D(-10.0, 10.0, -10.0, 10.0)  # Set coordinate system

def main():
    global triangle_vertices

    # Get user input for triangle coordinates
    try:
        print("Enter coordinates for the triangle vertices:")
        print("Format: x1 y1 x2 y2 x3 y3 (e.g., 1 1 2 3 3 1)")

        coords_input = input("Enter triangle coordinates: ").strip()
        if coords_input:
            coords = list(map(float, coords_input.split()))
            if len(coords) == 6:
                triangle_vertices = [
                    (coords[0], coords[1]),
                    (coords[2], coords[3]),
                    (coords[4], coords[5])
                ]
            else:
                print("Need exactly 6 coordinates (3 vertices). Using default triangle.")
        else:
            print("Using default triangle coordinates.")

    except (ValueError, IndexError):
        print("Invalid input. Using default triangle coordinates.")

    glutInit()  # Initialize GLUT
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)  # Set display mode
    glutInitWindowSize(1000, 1000)  # Set window size
    glutInitWindowPosition(50, 50)  # Set window position
    glutCreateWindow(b"Triangle Reflections in 4 Quadrants")  # Create a window with title

    init()  # Initialize OpenGL settings
    glutDisplayFunc(plot)  # Register the display function

    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
