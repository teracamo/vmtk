#!/usr/bin/env python

## Program:   VMTK
## Module:    $RCSfile: vmtkdijkstradistancetopoints.py,v $
## Language:  Python
## Date:      $$
## Version:   $$

##   Copyright (c) Luca Antiga, David Steinman. All rights reserved.
##   See LICENCE file for details.

##      This software is distributed WITHOUT ANY WARRANTY; without even 
##      the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR 
##      PURPOSE.  See the above copyright notices for more information.

## Note: this class was contributed by 
##       Tangui Morvan
##       Kalkulo AS
##       Simula Research Laboratory

## This class computes the geodesic distance on the graph of a surface
## from a set of user-selected points on the surface using the Dijkstra algorithm.


import vtk
import sys

import vtkvmtk
import vtkvmtkcontrib
import vmtkrenderer
import pypes

vmtkdijkstradistancetopoints = 'vmtkDijkstraDistanceToPoints'


class vmtkDijkstraDistanceToPoints(pypes.pypeScript):

    def __init__(self):

        pypes.pypeScript.__init__(self)
        
        self.Surface = None
        self.DijkstraDistanceToPointsArrayName = 'DijkstraDistanceToPoints'
        self.DistanceOffset = 0.
        self.DistanceScale = 1.
        self.MinDistance = 0.
        self.MaxDistance = -1.
        self.SeedPoints = vtk.vtkPolyData()
        self.SeedIds = vtk.vtkIdList()
        self.vmtkRenderer = None
        self.OwnRenderer = 0
        self.DisplayArray = False
        self.SurfaceMapper = None
        self.Opacity = 1.
        self.PointActor = None
        self.ScalarBarActor = None
        
        self.SetScriptName('vmtkdijkstradistancetopoints')
        self.SetInputMembers([
            ['Surface','i','vtkPolyData',1,'','the input surface','vmtksurfacereader'],
            ['DijkstraDistanceToPointsArrayName','distancetopointsarray','str',1,'','array storing the distances'],
            ['DistanceOffset','offset','float',1,'','offset added to the distances'],
            ['DistanceScale','scale','float',1,'','scale applied to the distances'],
            ['MinDistance','mindistance','float',1,'','minimum value for the distances'],
            ['MaxDistance','maxdistance','float',1,'','maximum value for the distances'],
            ['Opacity','opacity','float',1,'(0.0,1.0)','object opacities in the scene'],
            ['vmtkRenderer','renderer','vmtkRenderer',1,'','external renderer']
            ])
        self.SetOutputMembers([
            ['Surface','o','vtkPolyData',1,'','','vmtksurfacewriter']
            ])
    
    def DistanceParametersValidator(self,text):
        if not text:
            return 1
        splitText = text.strip().split(' ')
        if len(splitText) not in range(1,5):
            return 0
        try:
            for i in range(1,len(splitText)+1):
                float(splitText[i-1])
        except ValueError:
            return 0
        return 1
        
        
    def ComputeDistances(self):
        dijkstraFilter = vtkvmtkcontrib.vtkvmtkPolyDataDijkstraDistanceToPoints()
        dijkstraFilter.SetInput(self.Surface)
        dijkstraFilter.SetSeedIds(self.SeedIds)
        dijkstraFilter.SetDistanceOffset(self.DistanceOffset)
        dijkstraFilter.SetDistanceScale(self.DistanceScale)
        dijkstraFilter.SetMinDistance(self.MinDistance)
        dijkstraFilter.SetMaxDistance(self.MaxDistance)
        dijkstraFilter.SetDijkstraDistanceToPointsArrayName(self.DijkstraDistanceToPointsArrayName)
        dijkstraFilter.Update()
        return dijkstraFilter.GetOutput()
      
    
    def InitializeSeeds(self):
        self.SeedIds.Initialize()
        self.SeedPoints.Initialize()
        seedPoints = vtk.vtkPoints()
        self.SeedPoints.SetPoints(seedPoints)
        
    
    
    def KeyPressed(self,obj,event):
        key = obj.GetKeySym()
        if key == 'u':
            self.InitializeSeeds()
            self.SeedPoints.Modified()
            self.vmtkRenderer.RenderWindow.Render()
            return
        elif key == 'space':
            picker = vtk.vtkCellPicker()
            picker.SetTolerance(1E-4 * self.Surface.GetLength())
            eventPosition = obj.GetEventPosition()
            result = picker.Pick(float(eventPosition[0]),float(eventPosition[1]),0.0,self.vmtkRenderer.Renderer)
            if result == 0:
                return
            pickPosition = picker.GetPickPosition()
            pickedCellPointIds = self.Surface.GetCell(picker.GetCellId()).GetPointIds()
            minDistance = 1E10
            pickedSeedId = -1
            for i in range(pickedCellPointIds.GetNumberOfIds()):
                distance = vtk.vtkMath.Distance2BetweenPoints(pickPosition,self.Surface.GetPoint(pickedCellPointIds.GetId(i)))
                if distance < minDistance:
                    minDistance = distance
                    pickedSeedId = pickedCellPointIds.GetId(i)
            if pickedSeedId == -1:
                pickedSeedId = pickedCellPointIds.GetId(0)
            self.SeedIds.InsertNextId(pickedSeedId)
            point = self.Surface.GetPoint(pickedSeedId)
            self.SeedPoints.GetPoints().InsertNextPoint(point)
            self.SeedPoints.Modified()
            self.vmtkRenderer.RenderWindow.Render()
        elif key == 'd':
            self.DisplayArray = not self.DisplayArray
            if self.DisplayArray:
                newSurface = self.ComputeDistances()
                self.SurfaceMapper.SetInput(newSurface)
                newSurface.GetPointData().SetActiveScalars(self.DijkstraDistanceToPointsArrayName)
                array = newSurface.GetPointData().GetScalars()
                if (array):
                    self.SurfaceMapper.SetScalarRange(array.GetRange(0))
                    self.ScalarBarActor.VisibilityOn()
            else:
                self.SurfaceMapper.SetInput(self.Surface)
                self.ScalarBarActor.VisibilityOff()
            self.SurfaceMapper.SetScalarVisibility(self.DisplayArray)
            self.vmtkRenderer.RenderWindow.Render()
        elif key == 'a':
            queryString = 'Please input new parameters :\nDistanceOffset('+str(self.DistanceOffset)+') [DistanceScale('+str(self.DistanceScale)+') MinDistance('+str(self.MinDistance)+') MaxDistance('+str(self.MaxDistance)+'): '
            inputString = self.InputText(queryString,self.DistanceParametersValidator)
            splitInputString = inputString.strip().split(' ')
            if len(splitInputString) >= 1 and splitInputString[0] != '':
                self.DistanceOffset = float(splitInputString[0])
            if len(splitInputString) >= 2:
                self.DistanceScale = float(splitInputString[1])
            if len(splitInputString) >= 3:
                self.MinDistance = float(splitInputString[2])
            if len(splitInputString) >= 4:
                self.MaxDistance = float(splitInputString[3])

    
        

    def Execute(self):

        if self.Surface == None:
            self.PrintError('Error: No input surface.')

        if not self.vmtkRenderer:
          self.vmtkRenderer = vmtkrenderer.vmtkRenderer()
          self.vmtkRenderer.Initialize()
          self.OwnRenderer = 1
          
        glyphs = vtk.vtkGlyph3D()
        glyphSource = vtk.vtkSphereSource()
        glyphSource.SetRadius(1)
        glyphs.SetInput(self.SeedPoints)
        glyphs.SetSource(glyphSource.GetOutput())
        glyphs.SetScaleModeToDataScalingOff()
        glyphs.SetScaleFactor(self.Surface.GetLength()*0.01)
        glyphMapper = vtk.vtkPolyDataMapper()
        glyphMapper.SetInput(glyphs.GetOutput())
        glyphMapper.ScalarVisibilityOff()
        self.PointActor = vtk.vtkActor()
        self.PointActor.SetMapper(glyphMapper)
        self.PointActor.GetProperty().SetColor(1.0,0.0,0.0)
        self.PointActor.GetProperty().SetOpacity(self.Opacity)
        self.PointActor.PickableOff()
        self.vmtkRenderer.Renderer.AddActor(self.PointActor)
        
        self.vmtkRenderer.RenderWindowInteractor.AddObserver("KeyPressEvent", self.KeyPressed)
        
        self.SurfaceMapper = vtk.vtkPolyDataMapper()
        self.SurfaceMapper.SetInput(self.Surface)
        self.SurfaceMapper.SetScalarVisibility(self.DisplayArray)
        surfaceActor = vtk.vtkActor()
        surfaceActor.SetMapper(self.SurfaceMapper)
        surfaceActor.GetProperty().SetOpacity(self.Opacity)
        self.vmtkRenderer.Renderer.AddActor(surfaceActor)
        
        self.ScalarBarActor = vtk.vtkScalarBarActor()
        self.ScalarBarActor.SetLookupTable(self.SurfaceMapper.GetLookupTable())
        self.ScalarBarActor.GetLabelTextProperty().ItalicOff()
        self.ScalarBarActor.GetLabelTextProperty().BoldOff()
        self.ScalarBarActor.GetLabelTextProperty().ShadowOff()
        self.ScalarBarActor.SetLabelFormat('%.2f')
        self.ScalarBarActor.SetTitle('distances')
        self.ScalarBarActor.VisibilityOff()
        self.vmtkRenderer.Renderer.AddActor(self.ScalarBarActor)
        
        
        self.OutputText('Please position the mouse and press space to add points, \'u\' to undo\n')
        
        
        any = 0
        while any == 0:
            self.InitializeSeeds()
            self.vmtkRenderer.Render()
            any = self.SeedIds.GetNumberOfIds()
        
        self.Surface = self.ComputeDistances()

        if self.Surface.GetSource():
            self.Surface.GetSource().UnRegisterAllOutputs()

        if self.OwnRenderer:
            self.vmtkRenderer.Deallocate()

if __name__=='__main__':

    main = pypes.pypeMain()
    main.Arguments = sys.argv
    main.Execute()
