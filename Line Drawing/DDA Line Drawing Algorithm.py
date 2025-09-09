"""
DDA (Digital Differential Analyzer) Line Drawing Algorithm

WORKING PRINCIPLE:
The DDA algorithm is a line drawing algorithm that uses differential calculus concepts.
It calculates the incremental changes in x and y coordinates based on the slope of the line.

Algorithm Steps:
1. Calculate dx = x2 - x1 and dy = y2 - y1
2. Determine the number of steps needed: steps = max(|dx|, |dy|)
3. Calculate incremental changes: x_inc = dx/steps, y_inc = dy/steps
4. Start from (x1, y1) and increment x and y by their respective increments
5. Plot points at each integer coordinate

ADVANTAGES:
- Simple to implement
- Works for all slopes (horizontal, vertical, diagonal)
- Good accuracy for lines with gentle slopes

LIMITATIONS:
- Uses floating-point arithmetic (slower than integer-based algorithms)
- Accumulation of rounding errors over long lines
- May produce gaps in lines with steep slopes due to rounding
- Not as efficient as Bresenham's algorithm for integer-based graphics

DIFFERENCES FROM BRESENHAM'S ALGORITHM:
- DDA uses floating-point arithmetic, Bresenham uses integer arithmetic
- Bresenham's is more efficient and accurate for raster graphics
- DDA is simpler to understand but slower to execute
"""

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Global variables for line coordinates
x1, y1 = 100, 100
x2, y2 = 400, 300

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Set background color to black
    gluOrtho2D(0, 500, 0, 500)        # Set the coordinate system (2D)

def draw_pixel(x, y):
    """Draw a single pixel at the specified coordinates"""
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

def dda_line(x1, y1, x2, y2):
    """
    Implement DDA line drawing algorithm

    Parameters:
    x1, y1: Starting point coordinates
    x2, y2: Ending point coordinates
    """
    dx = x2 - x1  # Change in x
    dy = y2 - y1  # Change in y
    steps = max(abs(dx), abs(dy))  # Number of steps needed (largest delta)

    # Calculate increments for each step
    x_inc = dx / float(steps) if steps != 0 else 0
    y_inc = dy / float(steps) if steps != 0 else 0

    # Start from the first point
    x = float(x1)
    y = float(y1)

    glColor3f(1.0, 1.0, 1.0)  # Set line color to white
    glPointSize(2.0)  # Set point size for better visibility

    # Plot points along the line
    for i in range(int(steps) + 1):
        draw_pixel(round(x), round(y))
        x += x_inc  # Increment x
        y += y_inc  # Increment y

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    dda_line(x1, y1, x2, y2)
    glFlush()

def main():
    global x1, y1, x2, y2

    # Get user input for line coordinates
    try:
        print("DDA Line Drawing Algorithm")
        print("Enter coordinates for the line to draw:")
        x1 = float(input("Enter x1 (start point x): "))
        y1 = float(input("Enter y1 (start point y): "))
        x2 = float(input("Enter x2 (end point x): "))
        y2 = float(input("Enter y2 (end point y): "))
    except ValueError:
        print("Invalid input. Using default coordinates (100,100) to (400,300)")

    glutInit()
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(500, 500)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"DDA Line Drawing Algorithm - OpenGL")
    init()
    glutDisplayFunc(display)
    glutMainLoop()

if __name__ == "__main__":
    main()
