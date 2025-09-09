from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Global variables for line drawing
line_type = ""
x_start = y_start = x_end = y_end = 0

def clear_screen():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Set background color to black
    gluOrtho2D(-20, 20, -20, 20)  # Set coordinate system to accommodate larger ranges

def plot_points():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the color buffer
    glColor3f(0.0, 1.0, 0.0)  # Set drawing color to green

    if line_type == "horizontal":
        glPointSize(5.0)
        glBegin(GL_POINTS)
        for x in range(int(min(x_start, x_end)), int(max(x_start, x_end)) + 1):
            glVertex2f(x, y_start)
        glEnd()

    elif line_type == "vertical":
        glPointSize(5.0)
        glBegin(GL_POINTS)
        for y in range(int(min(y_start, y_end)), int(max(y_start, y_end)) + 1):
            glVertex2f(x_start, y)
        glEnd()

    elif line_type == "diagonal":
        # Draw individual points along the diagonal: (start,start), (start+1,start+1), ..., (end,end)
        glPointSize(5.0)
        glBegin(GL_POINTS)
        for i in range(int(x_start), int(x_end) + 1):
            glVertex2f(i, i)
        glEnd()

    glFlush()  # Ensure all OpenGL commands are executed

def main():
    global line_type, x_start, y_start, x_end, y_end

    # Get user input for line type and coordinates
    print("Choose a line drawing option:")
    print("1. Horizontal Line")
    print("2. Vertical Line")
    print("3. Diagonal Line")

    choice = input("Enter your choice (1-3): ").strip()

    if choice == "1":
        line_type = "horizontal"
        x_start = float(input("Enter X-coordinate start: "))
        x_end = float(input("Enter X-coordinate end: "))
        y_start = float(input("Enter Y-coordinate: "))
        print(f"Drawing horizontal line from ({x_start}, {y_start}) to ({x_end}, {y_start})")

    elif choice == "2":
        line_type = "vertical"
        x_start = float(input("Enter X-coordinate: "))
        y_start = float(input("Enter Y-coordinate start: "))
        y_end = float(input("Enter Y-coordinate end: "))
        print(f"Drawing vertical line from ({x_start}, {y_start}) to ({x_start}, {y_end})")

    elif choice == "3":
        line_type = "diagonal"
        # For diagonal lines, take input as "start_value, end_value" and plot (start,start)...(end,end)
        diagonal_input = input("Enter diagonal line range (e.g., 5, 10): ")
        try:
            start_val, end_val = map(int, diagonal_input.split(','))
            x_start = start_val
            y_start = start_val
            x_end = end_val
            y_end = end_val
            print(f"Drawing diagonal line from ({start_val}, {start_val}) to ({end_val}, {end_val})")
        except ValueError:
            print("Invalid input format. Using default 5,10")
            x_start, y_start = 5, 5
            x_end, y_end = 10, 10

    else:
        print("Invalid choice. Using horizontal line as default.")
        line_type = "horizontal"
        x_start, x_end, y_start = 0, 10, 5

    glutInit()  # Initialize GLUT
    glutInitDisplayMode(GLUT_RGB)  # Set display mode
    glutInitWindowSize(1000, 1000)  # Set window size
    glutInitWindowPosition(100, 100)  # Set window position
    glutCreateWindow(b"Line Drawing Options - OpenGL")  # Create window with descriptive title

    clear_screen()  # Set clear color and coordinate system
    glutDisplayFunc(plot_points)  # Register display function

    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()
