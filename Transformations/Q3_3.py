from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Global variables to store user inputs
background_color = (0.0, 0.0, 0.0)  # Default black
square_color = (1.0, 0.0, 0.0)      # Default red
square_center = (0.0, 0.0)          # Default center
square_size = 1.0                   # Default size

def clear_screen():
    glClearColor(*background_color, 1.0)  # Set background color
    # Adjust the coordinate system based on square size
    half_size = square_size / 2.0
    gluOrtho2D(-half_size - 1, half_size + 1, -half_size - 1, half_size + 1)  # Set coordinate system

def plot_points():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the color buffer
    
    glColor3f(*square_color)  # Set drawing color to the user-defined color

    half_size = square_size / 2.0
    
    glBegin(GL_QUADS)  # Begin drawing a filled quadrilateral
    
    # Draw the square based on center and size
    glVertex2f(square_center[0] - half_size, square_center[1] - half_size)  # Bottom-left corner
    glVertex2f(square_center[0] + half_size, square_center[1] - half_size)  # Bottom-right corner
    glVertex2f(square_center[0] + half_size, square_center[1] + half_size)  # Top-right corner
    glVertex2f(square_center[0] - half_size, square_center[1] + half_size)  # Top-left corner
    
    glEnd()
    
    glFlush()  # Ensure all OpenGL commands are executed

def main():
    global background_color, square_color, square_center, square_size
    
    # Input from the user
    try:
        bg_color_input = input("Enter the background color (R G B) in the range [0.0, 1.0]: ").split()
        background_color = tuple(map(float, bg_color_input))
        
        sq_color_input = input("Enter the square color (R G B) in the range [0.0, 1.0]: ").split()
        square_color = tuple(map(float, sq_color_input))
        
        center_input = input("Enter the center of the square (X Y): ").split()
        square_center = tuple(map(float, center_input))
        
        square_size = float(input("Enter the size of the square (positive number): "))
        
    except ValueError:
        print("Invalid input. Using default values.")
    
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
