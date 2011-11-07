'''*********************************************
* Zeus CMD - OpenGL Tutorial 12 : Perspective *
* By Grant James (ZEUS)                       *
* http://www.zeuscmd.com                      *
*********************************************'''
#pragma comment(linker, "/subsystem:\"windows\" \
#/entry:\"mainCRTStartup\"")

#include <stdlib.h>
#include <GL/glut.h>

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys

fullscreen = False

perspective = True

def drawQuad():

	glBegin(GL_QUADS);
	glVertex2f(-0.25, -0.25);
	glVertex2f(0.25, -0.25);
	glVertex2f(0.25, 0.25);
	glVertex2f(-0.25, 0.25);
	glEnd();


def init():
	glClearColor(0.93, 0.93, 0.93, 0.0);

	glEnable(GL_DEPTH_TEST);
	glDepthFunc(GL_LEQUAL);
	glClearDepth(1.0);

	return True;

def display():

	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glLoadIdentity();

	gluLookAt(
		0.0, 0.0, 2.0,
		0.0, 0.0, 0.0,
		0.0, 1.0, 0.0);

	glColor4f(1.0, 0.0, 0.0, 1.0);
	glTranslatef(0.25, 0.0, 0.0);
	drawQuad();

	glColor4f(0.0, 1.0, 0.0, 1.0);
	glTranslatef(-0.25, 0.0, -1.0);
	drawQuad();

	glColor4f(0.0, 0.0, 1.0, 1.0);
	glTranslatef(-0.25, 0.0, -1.0);
	drawQuad();

	glFlush();
	glutSwapBuffers();

def resize(w, h):
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();

	glViewport(0, 0, w, h);

	if (perspective):
		gluPerspective(45.0, 1.0 * w / h, 1.0, 100.0);
	else:
		glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 20.0);

	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();

def idle():

	glutPostRedisplay()


def keyboard(key, x, y):
	global perspective
	
	if key == 27 : 
		exit(1); 
	elif key in ['p' , 'P']:
		perspective = not perspective;
		resize(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT));

def specialKeyboard(key, x, y):
	global fullscreen
	if (key == GLUT_KEY_F1):
	
		fullscreen = not fullscreen;

		if (fullscreen):
			glutFullScreen();
		else:
		
			glutReshapeWindow(500, 500);
			glutPositionWindow(50, 50);

def main(argv):
	glutInit(argv);

	glutInitWindowPosition(50, 50);
	glutInitWindowSize(500, 500);

	glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE);
	
	glutCreateWindow("12 - Perspective");

	glutDisplayFunc(display);
	glutKeyboardFunc(keyboard);
	glutSpecialFunc(specialKeyboard);
	glutReshapeFunc(resize);
	glutIdleFunc(idle);

	if (not init()):
		return 1;

	glutMainLoop();

	return 0;

if __name__ == '__main__':
	main(sys.argv)