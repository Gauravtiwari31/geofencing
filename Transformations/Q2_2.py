from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Global variables to store user input for line drawing
line_type = ""
x_start = y_start = x_end = y_end = 0

def clear_screen():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Set background color to black
    gluOrtho2D(-10, 10, -10, 10)  # Set coordinate system

def draw_line(x1, y1, x2, y2):
    glBegin(GL_LINES)
    glVertex2f(x1, y1)
    glVertex2f(x2, y2)
    glEnd()

def plot_points():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the color buffer
    glColor3f(0.0, 1.0, 0.0)  # Set drawing color to green

    if line_type == "horizontal":
        glBegin(GL_LINES)
        glVertex2f(x_start, y_start)
        glVertex2f(x_end, y_start)
        glEnd()
    
    elif line_type == "vertical":
        glBegin(GL_LINES)
        glVertex2f(x_start, y_start)
        glVertex2f(x_start, y_end)
        glEnd()
    
    elif line_type == "diagonal":
        glBegin(GL_LINES)
        glVertex2f(x_start, y_start)
        glVertex2f(x_end, y_end)
        glEnd()
    
    glFlush()  # Ensure all OpenGL commands are executed

def main():
    global line_type, x_start, y_start, x_end, y_end

    # Example inputs (You can modify these to get user input)
    line_type = input("Enter line type (horizontal/vertical/diagonal): ").strip().lower()
    
    if line_type == "horizontal":
        x_start = float(input("Enter X-coordinate start: "))
        x_end = float(input("Enter X-coordinate end: "))
        y_start = float(input("Enter Y-coordinate: "))
        y_end = y_start  # For horizontal lines, y_start and y_end are the same

    elif line_type == "vertical":
        x_start = float(input("Enter X-coordinate: "))
        y_start = float(input("Enter Y-coordinate start: "))
        y_end = float(input("Enter Y-coordinate end: "))
        x_end = x_start  # For vertical lines, x_start and x_end are the same

    elif line_type == "diagonal":
        x_start = float(input("Enter X-coordinate start: "))
        y_start = float(input("Enter Y-coordinate start: "))
        x_end = float(input("Enter X-coordinate end: "))
        y_end = float(input("Enter Y-coordinate end: "))

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
