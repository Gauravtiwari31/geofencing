from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Global variables for user input
background_color = (0.0, 0.0, 0.0)  # Default black
square_color = (1.0, 0.0, 0.0)      # Default red
square_center = (0.0, 0.0)          # Default center
square_size = 1.0                   # Default size

def clear_screen():
    glClearColor(*background_color, 1.0)  # Set user-defined background color
    # Adjust coordinate system based on square size and center
    half_size = square_size / 2.0
    margin = half_size + 1.0
    center_x, center_y = square_center
    gluOrtho2D(center_x - margin, center_x + margin,
               center_y - margin, center_y + margin)

def plot_points():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the color buffer

    # Set color to draw the filled square
    glColor3f(*square_color)  # Set drawing color to user-defined color

    glBegin(GL_QUADS)  # Begin drawing a filled quadrilateral

    # Calculate square corners based on center and size
    half_size = square_size / 2.0
    center_x, center_y = square_center

    # Draw the filled square
    glVertex2f(center_x - half_size, center_y - half_size)  # Bottom-left corner
    glVertex2f(center_x + half_size, center_y - half_size)  # Bottom-right corner
    glVertex2f(center_x + half_size, center_y + half_size)  # Top-right corner
    glVertex2f(center_x - half_size, center_y + half_size)  # Top-left corner

    glEnd()

    glFlush()  # Ensure all OpenGL commands are executed

def main():
    global background_color, square_color, square_center, square_size

    # Get user input as specified in lab requirements
    try:
        print("Enter colors as three values separated by spaces (e.g., 0.5 0.5 0.5)")
        bg_color_input = input("Enter the background color (R G B) in the range [0.0, 1.0]: ").strip().split()
        if len(bg_color_input) == 3:
            background_color = tuple(map(float, bg_color_input))
        else:
            raise ValueError("Need exactly 3 color values")

        sq_color_input = input("Enter the square color (R G B) in the range [0.0, 1.0]: ").strip().split()
        if len(sq_color_input) == 3:
            square_color = tuple(map(float, sq_color_input))
        else:
            raise ValueError("Need exactly 3 color values")

        center_input = input("Enter the center of the square (X Y): ").strip().split()
        if len(center_input) == 2:
            square_center = tuple(map(float, center_input))
        else:
            raise ValueError("Need exactly 2 coordinates")

        square_size = float(input("Enter the size of the square (positive number): "))
        if square_size <= 0:
            raise ValueError("Size must be positive")

    except (ValueError, IndexError) as e:
        print(f"Invalid input: {e}. Using default values.")
        background_color = (0.0, 0.0, 0.0)  # Black
        square_color = (1.0, 0.0, 0.0)      # Red
        square_center = (0.0, 0.0)          # Center
        square_size = 1.0                   # Reasonable size

    glutInit()  # Initialize GLUT
    glutInitDisplayMode(GLUT_RGB)  # Set display mode
    glutInitWindowSize(1000, 1000)  # Set window size
    glutInitWindowPosition(100, 100)  # Set window position
    glutCreateWindow(b"Filled Square Drawing - OpenGL")  # Descriptive title

    clear_screen()  # Set clear color and coordinate system
    glutDisplayFunc(plot_points)  # Register display function

    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
