Dim swApp As Object
Dim swModel As SldWorks.ModelDoc2
Dim swDraw As Object
Dim swView As SldWorks.View
Dim ModelPath As String
Dim TemplatePath As String
Dim Width As Double
Dim Height As Double
Dim MainPlane As String
Dim PrinciplePlane As String
Dim SheetSizeInput As String

Sub main()

    Set swApp = Application.SldWorks
    Set swModel = swApp.ActiveDoc
    
    If swModel Is Nothing Then
        MsgBox "Please open a part file first."
        Exit Sub
    End If
    
    If swModel.GetType <> 1 Then ' swDocPART = 1
        MsgBox "This macro only works on Part files."
        Exit Sub
    End If
    
    ModelPath = swModel.GetPathName
    
    ' Get Principle Plane
    PrinciplePlane = InputBox("Select Primary Plane:" & vbNewLine & "F = Front" & vbNewLine & "T = Top" & vbNewLine & "R = Right", "Primary Plane Selection", "F")
    
    If UCase(PrinciplePlane) = "F" Then
        MainPlane = "*Front"
    ElseIf UCase(PrinciplePlane) = "T" Then
        MainPlane = "*Top"
    ElseIf UCase(PrinciplePlane) = "R" Then
        MainPlane = "*Right"
    Else
        MainPlane = "*Front" ' Default
    End If
    
    ' Get Sheet Size
    SheetSizeInput = InputBox("Select Sheet Size:" & vbNewLine & "4 = A4" & vbNewLine & "3 = A3" & vbNewLine & "2 = A2" & vbNewLine & "1 = A1", "Sheet Size Selection", "3")
    
    Select Case SheetSizeInput
        Case "4"
            TemplatePath = "C:\NPD\Admin\Templates\SolidWorks PDM Templates\Standard - A4.DRWDOT"
            Width = 0.297
            Height = 0.21
        Case "3"
            TemplatePath = "C:\NPD\Admin\Templates\SolidWorks PDM Templates\Standard - A3.DRWDOT"
            Width = 0.42
            Height = 0.297
        Case "2"
            TemplatePath = "C:\NPD\Admin\Templates\SolidWorks PDM Templates\Standard - A2.DRWDOT"
            Width = 0.594
            Height = 0.42
        Case "1"
            TemplatePath = "C:\NPD\Admin\Templates\SolidWorks PDM Templates\Standard - A1.DRWDOT"
            Width = 0.841
            Height = 0.594
        Case Else
            TemplatePath = "C:\NPD\Admin\Templates\SolidWorks PDM Templates\Standard - A3.DRWDOT"
            Width = 0.42
            Height = 0.297
    End Select
    
    ' Create Drawing
    Set swDraw = swApp.NewDocument(TemplatePath, 12, Width, Height)
    
    If swDraw Is Nothing Then
        MsgBox "Failed to create drawing. Check template path."
        Exit Sub
    End If
    
    ' View Positions (Third Angle)
    ' Main View (Bottom Left)
    Dim X_Main As Double, Y_Main As Double
    X_Main = Width * 0.25
    Y_Main = Height * 0.35
    
    ' Insert Main View
    Set swView = swDraw.CreateDrawViewFromModelView3(ModelPath, MainPlane, X_Main, Y_Main, 0)
    
    If swView Is Nothing Then
        MsgBox "Failed to insert main view."
        Exit Sub
    End If
    
    ' Auto Insert Center Marks
    swView.AutoInsertCenterMarks2 7, 11, True, True, True, 0.0025, 0.0025, True, True, 0
    swView.SetDisplayMode3 False, 1, False, True
    
    ' Determine orientations for other views
    Dim TopViewName As String
    Dim RightViewName As String
    
    If MainPlane = "*Front" Then
        TopViewName = "*Top"
        RightViewName = "*Right"
    ElseIf MainPlane = "*Top" Then
        TopViewName = "*Back"
        RightViewName = "*Right"
    ElseIf MainPlane = "*Right" Then
        TopViewName = "*Top"
        RightViewName = "*Back"
    End If

    ' Insert Top View (Manually placed to avoid projection errors)
    Dim X_Top As Double, Y_Top As Double
    X_Top = X_Main
    Y_Top = Height * 0.75
    Dim swViewTop As SldWorks.View
    Set swViewTop = swDraw.CreateDrawViewFromModelView3(ModelPath, TopViewName, X_Top, Y_Top, 0)
    swViewTop.AutoInsertCenterMarks2 7, 11, True, True, True, 0.0025, 0.0025, True, True, 0
    
    ' Insert Right View (Manually placed to avoid projection errors)
    Dim X_Right As Double, Y_Right As Double
    X_Right = Width * 0.75
    Y_Right = Y_Main
    Dim swViewRight As SldWorks.View
    Set swViewRight = swDraw.CreateDrawViewFromModelView3(ModelPath, RightViewName, X_Right, Y_Right, 0)
    swViewRight.AutoInsertCenterMarks2 7, 11, True, True, True, 0.0025, 0.0025, True, True, 0
    
    ' Insert Isometric View (Top Right)
    Dim X_Iso As Double, Y_Iso As Double
    X_Iso = Width * 0.75
    Y_Iso = Height * 0.75
    swDraw.CreateDrawViewFromModelView3 ModelPath, "*Isometric", X_Iso, Y_Iso, 0
    
    ' Force Rebuild before adding dimensions
    swDraw.ForceRebuild3 True
    
    ' Activate Sheet 1
    swDraw.ActivateSheet "Sheet1"

    ' Insert Dimensions
    ' Change system setting to import ALL dimensions, not just those marked for drawing
    Dim bOldSetting As Boolean
    bOldSetting = swApp.GetUserPreferenceToggle(16) ' 16 = swDetailingImportDimensionsMarkedForDrawing
    swApp.SetUserPreferenceToggle 16, False
    
    ' Imports dimensions using the specific mask from Autodrawing
    Dim vAnnotations As Variant
    ' 0 = swImportModelItemsFromEntireModel
    ' 1212424 = Combination of types (Dimensions, Hole Callouts, etc.)
    ' True = Import to all views
    ' True = Eliminate duplicates
    ' False = Do not import hidden
    ' False = Do not use default placement
    vAnnotations = swDraw.InsertModelAnnotations3(0, 1212424, True, True, False, False)
    
    ' Restore system setting
    swApp.SetUserPreferenceToggle 16, bOldSetting
    
    ' Format Hole Callouts (Force Straight Leader)
    Dim vViews As Variant
    Dim vView As Variant
    Dim swViewIter As SldWorks.View
    Dim swDispDim As SldWorks.DisplayDimension
    Dim swAnn As SldWorks.Annotation
    Dim swDim As Object
    
    ' Create array of views to process
    vViews = Array(swView, swViewTop, swViewRight)
    
    For Each vView In vViews
        Set swViewIter = vView
        Set swDispDim = swViewIter.GetFirstDisplayDimension5
        
        While Not swDispDim Is Nothing
            ' Get underlying dimension object to check type
            Set swDim = swDispDim.GetDimension
            
            If Not swDim Is Nothing Then
                ' Check if it is a Diameter dimension (Type 4) or Radial (Type 3)
                ' swDimensionType_e: swDiameterDimension = 4, swRadialDimension = 3
                If swDim.GetType = 4 Or swDim.GetType = 3 Then
                    Set swAnn = swDispDim.GetAnnotation
                    If Not swAnn Is Nothing Then
                        ' swLeaderStyle_e.swSTRAIGHT = 1
                        swAnn.LeaderStyle = 1
                    End If
                End If
            End If
            Set swDispDim = swDispDim.GetNext5
        Wend
    Next vView
    
    ' Copy Custom Properties from Part to Drawing
    Dim swCustPropMgr As SldWorks.CustomPropertyManager
    Dim swPartCustPropMgr As SldWorks.CustomPropertyManager
    Dim vPropNames As Variant
    Dim vPropTypes As Variant
    Dim vPropValues As Variant
    Dim ValOut As String
    Dim ResolvedValOut As String
    Dim nNbrProps As Long
    Dim i As Integer
    
    Set swCustPropMgr = swDraw.Extension.CustomPropertyManager("")
    Set swPartCustPropMgr = swModel.Extension.CustomPropertyManager("")
    
    ' Get all properties from part
    nNbrProps = swPartCustPropMgr.Count
    If nNbrProps > 0 Then
        swPartCustPropMgr.GetAll3 vPropNames, vPropTypes, vPropValues, Empty, Empty
        
        For i = 0 To UBound(vPropNames)
            swPartCustPropMgr.Get2 vPropNames(i), ValOut, ResolvedValOut
            swCustPropMgr.Add3 vPropNames(i), swCustomInfoText, ResolvedValOut, swCustomPropertyReplaceValue
        Next i
    End If
    
    ' Set DrawnBy to current PDM/Windows User
    Dim CurrentUser As String
    CurrentUser = Environ("USERNAME")
    swCustPropMgr.Add3 "DrawnBy", swCustomInfoText, CurrentUser, swCustomPropertyReplaceValue
    swCustPropMgr.Add3 "DrawnDate", swCustomInfoText, Date, swCustomPropertyReplaceValue
    
    ' Force Rebuild
    swDraw.ForceRebuild3 True
    
    ' Save Drawing
    Dim DrawingPath As String
    Dim DotPos As Integer
    
    DotPos = InStrRev(ModelPath, ".")
    If DotPos > 0 Then
        DrawingPath = Left(ModelPath, DotPos - 1) & ".SLDDRW"
    Else
        DrawingPath = ModelPath & ".SLDDRW"
    End If
    
    ' Save silently to avoid "Replace" dialog if possible, or handle it
    ' 1 = swSaveAsOptions_Silent (Overwrites without prompt)
    ' 2 = swSaveAsOptions_Copy
    Dim saveErrors As Long
    Dim saveWarnings As Long
    Dim bRet As Boolean
    
    bRet = swDraw.SaveAs4(DrawingPath, 0, 0, saveErrors, saveWarnings)
    
    If bRet = False Then
        MsgBox "Failed to save drawing."
        Exit Sub
    End If
    
    MsgBox "Drawing created and saved: " & vbNewLine & DrawingPath
    
    ' PDM Integration
    ' Automatically Add and Check In to ensure PDM recognizes it
    Dim response As Integer
    response = MsgBox("Do you want to add this drawing to PDM?" & vbNewLine & "This will register the file and attempt to check it in.", vbYesNo + vbQuestion, "PDM Integration")
    
    If response = vbYes Then
        AddToPDM DrawingPath
    End If
    
End Sub

Sub AddToPDM(filePath As String)
    On Error Resume Next
    Dim vault As Object
    Set vault = CreateObject("ConisioLib.EdmVault")
    
    If vault Is Nothing Then
        MsgBox "Could not create PDM Vault object. Is PDM installed?"
        Exit Sub
    End If
    
    ' Attempt to get vault name from path
    Dim vaultName As String
    vaultName = vault.GetVaultNameFromPath(filePath)
    
    If vaultName = "" Then
        MsgBox "Could not determine PDM Vault from file path." & vbNewLine & filePath
        Exit Sub
    End If
    
    ' Login
    If Not vault.IsLoggedIn Then
        vault.LoginAuto vaultName, 0
    End If
    
    If Err.Number <> 0 Then
        MsgBox "Failed to login to PDM Vault: " & vaultName
        Err.Clear
        Exit Sub
    End If
    
    ' Get Folder
    Dim folder As Object
    Dim folderPath As String
    
    ' Extract folder path
    folderPath = Left(filePath, InStrRev(filePath, "\") - 1)
    Set folder = vault.GetFolderFromPath(folderPath)
    
    If folder Is Nothing Then
        MsgBox "Could not find PDM folder."
        Exit Sub
    End If
    
    ' Check if file already exists in PDM
    Dim file As Object
    Dim parentFolder As Object ' Use a separate variable for the output
    Set file = vault.GetFileFromPath(filePath, parentFolder)
    
    If file Is Nothing Then
        ' File is not in PDM yet (Local File). Add it.
        ' This promotes it to a PDM-managed file.
        Err.Clear
        Call folder.AddFile(0, filePath)
        
        If Err.Number <> 0 Then
            MsgBox "Failed to Add file to PDM. Error: " & Err.Description
            Exit Sub
        End If
        
        ' Get the file object again now that it's added
        Set file = vault.GetFileFromPath(filePath, parentFolder)
    End If
    
    ' Check In (Unlock)
    If Not file Is Nothing Then
        If file.IsLocked Then
            ' 0 = Parent Window
            ' Comment
            ' 0 = Flags
            file.UnlockFile 0, "Auto-generated drawing", 0
            
            If Err.Number = 0 Then
                MsgBox "File Added and Checked In successfully."
            Else
                MsgBox "File Added successfully."
            End If
        Else
            MsgBox "File is already Checked In."
        End If
    End If
    
End Sub
