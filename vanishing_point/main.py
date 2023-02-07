import cv2
import math
import numpy as np
import matplotlib.pyplot as plt
from vanish_point import RANSAC

from lkt_lines import get_lkt_lines


def cartesian_to_polar(xy_line):
    # https://math.stackexchange.com/questions/1382437/line-segment-equation-in-polar-coordinates
    x1, y1, x2, y2 = xy_line
    rho = abs((x2-x1)*y1 - x1*(y2-y1)) / math.sqrt((x2-x1)**2 + (y2-y1)**2)
    theta = -(x2-x1) / (y2-y1)
    return np.array([[rho, theta]])


if __name__ == "__main__":
    # Read image
    img = cv2.imread('images/ai_city.png')

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = np.zeros_like(img_gray)

    all_line_segments = get_lkt_lines()

    # Fill edges
    for line in all_line_segments:
        x1, y1, x2, y2 = line
        if x1 > 799 or x2 > 799 or y1 > 409 or y2 > 409:
            print(line)
            continue
        edges[y1][x1] = 255
        edges[y2][x2] = 255

    # Apply probabilistic hough line transform
    lines2 = cv2.HoughLinesP(edges, 2, np.pi / 180.0, 50, minLineLength=10, maxLineGap=100)
    lines = cv2.HoughLines(edges, 1, np.pi / 120, 55)

    # Draw lines on the detected points
    for line in lines2:
        x1, y1, x2, y2 = line[0]
        cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 1)

    cv2.imshow("Edges", edges)

    # # lines_in_polar = []
    # for line in all_line_segments:
    #     x1, y1, x2, y2 = line
    #     if x1 == x2 or y1 == y2:
    #         continue;
    #     # lines_in_polar.append(cartesian_to_polar(line))
    #     cv2.line(img, (x1, y1), (x2, y2), [0, 0, 0], 2)

    # RANSAC parameters:
    valid_lines = []
    # Remove horizontal and vertical lines as they would not converge to vanishing point
    for line in lines:
        rho,theta = line[0]
        if (theta>0.4 and theta < 1.47) or (theta > 1.67 and theta < 2.74):
            valid_lines.append(line)

    ransac_iterations, ransac_threshold, ransac_ratio = 350, 13, 0.93
    vanishing_point = RANSAC(valid_lines, ransac_iterations, ransac_threshold, ransac_ratio)
    print(vanishing_point)
    # vanishing_point = (100, 100)

    cv2.circle(img, vanishing_point, 3, (0, 255, 0), thickness=3)

    cv2.imshow("Image", img)

    while True:
        key = cv2.waitKey(1)
        if key == 27:
            break

    cv2.destroyAllWindows()