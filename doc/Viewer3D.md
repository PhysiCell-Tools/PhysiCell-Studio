For 3D plotting, these commands are defined (taken from https://vtk.org/doc/release/4.2/html/classvtkInteractorStyle.html)

```
* Keypress j / Keypress t: toggle between joystick (position sensitive) and trackball (motion sensitive) styles. In joystick style, motion occurs continuously as long as a mouse button is pressed. In trackball style, motion occurs when the mouse button is pressed and the mouse pointer moves.
* Keypress c / Keypress o: toggle between camera and object (actor) modes. In camera mode, mouse events affect the camera position and focal point. In object mode, mouse events affect the actor that is under the mouse pointer.
* Button 1: rotate the camera around its focal point (if camera mode) or rotate the actor around its origin (if actor mode). The rotation is in the direction defined from the center of the renderer's viewport towards the mouse position. In joystick mode, the magnitude of the rotation is determined by the distance the mouse is from the center of the render window.
* Button 2: pan the camera (if camera mode) or translate the actor (if object mode). In joystick mode, the direction of pan or translation is from the center of the viewport towards the mouse position. In trackball mode, the direction of motion is the direction the mouse moves. (Note: with 2-button mice, pan is defined as <Shift>-Button 1.)
* Button 3: zoom the camera (if camera mode) or scale the actor (if object mode). Zoom in/increase scale if the mouse position is in the top half of the viewport; zoom out/decrease scale if the mouse position is in the bottom half. In joystick mode, the amount of zoom is controlled by the distance of the mouse pointer from the horizontal centerline of the window.
* Keypress 3: toggle the render window into and out of stereo mode. By default, red-blue stereo pairs are created. Some systems support Crystal Eyes LCD stereo glasses; you have to invoke SetStereoTypeToCrystalEyes() on the rendering window.
* Keypress f: fly to the picked point
* Keypress p: perform a pick operation. The render window interactor has an internal instance of vtkCellPicker that it uses to pick.
* Keypress r: reset the camera view along the current view direction. Centers the actors and moves the camera so that all actors are visible.
* Keypress s: modify the representation of all actors so that they are surfaces.
* Keypress w: modify the representation of all actors so that they are wireframe.
```
