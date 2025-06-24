from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog
from System import *
from System.Collections.Specialized import StringCollection
from System.IO import Path, StreamWriter, File
from System.Text import Encoding
from Deadline.Scripting import ClientUtils, FrameUtils

import re

scriptDialog = None

def __main__():
    global scriptDialog
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle("Submit USD to Arnold")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid("NameLabel", "LabelControl", "Job Name", 0, 0)
    scriptDialog.AddControlToGrid("NameBox", "TextControl", "SickUSDJob", 0, 1)
    scriptDialog.AddControlToGrid("InputLabel", "LabelControl", "USD File", 1, 0)
    inputBox = scriptDialog.AddSelectionControlToGrid("InputBox", "FileBrowserControl", "", "USD Files (*.usd *.usda *.usdc)", 1, 1)
    inputBox.ValueModified.connect(UpdateFrameRange)
    scriptDialog.AddControlToGrid("FramesLabel", "LabelControl", "Frame Range", 2, 0)
    scriptDialog.AddControlToGrid("FramesBox", "TextControl", "1001-1240", 2, 1)
    scriptDialog.AddControlToGrid("OutputLabel", "LabelControl", "Output File", 3, 0)
    scriptDialog.AddSelectionControlToGrid("OutputBox", "FileSaverControl", "", "EXR Files (*.exr)", 3, 1)
    submitButton = scriptDialog.AddControlToGrid("SubmitButton", "ButtonControl", "Submit", 4, 0)
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid("CloseButton", "ButtonControl", "Close", 4, 1)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    scriptDialog.ShowDialog(False)

def UpdateFrameRange(*args):
    global scriptDialog
    usdFile = scriptDialog.GetValue("InputBox").strip()
    if not File.Exists(usdFile):
        return
    try:
        filename = Path.GetFileNameWithoutExtension(usdFile)
        # Match frame range in filename (e.g., render_1001-1100)
        match = re.match(r".*?(\d+)-(\d+)$", filename, re.IGNORECASE)
        if match:
            startFrame, endFrame = map(int, match.groups())
            if startFrame <= endFrame:
                scriptDialog.SetValue("FramesBox", f"{startFrame}-{endFrame}")
            else:
                scriptDialog.ShowMessageBox("Invalid frame range: start frame must be less than or equal to end frame", "Warning")
        else:
            scriptDialog.ShowMessageBox(f"No frame range found in filename '{filename}'. Expected format: name_####-####", "Warning")
    except Exception as e:
        scriptDialog.ShowMessageBox(f"Failed to parse frame range: {str(e)}", "Warning")

def SubmitButtonPressed(*args):
    global scriptDialog
    usdFile = scriptDialog.GetValue("InputBox").strip()
    if not File.Exists(usdFile):
        scriptDialog.ShowMessageBox(f"USD file {usdFile} does not exist", "Error")
        return
    frames = scriptDialog.GetValue("FramesBox").strip()
    if not FrameUtils.FrameRangeValid(frames):
        scriptDialog.ShowMessageBox(f"Frame range {frames} is not valid", "Error")
        return
    outputFile = scriptDialog.GetValue("OutputBox").strip()
    jobInfoFilename = Path.Combine(ClientUtils.GetDeadlineTempPath(), "sick_usd_job_info.job")
    writer = StreamWriter(jobInfoFilename, False, Encoding.Unicode)
    writer.WriteLine("Plugin=SickUSD")
    writer.WriteLine(f"Name={scriptDialog.GetValue('NameBox')}")
    writer.WriteLine(f"Frames={frames}")
    writer.WriteLine("ChunkSize=1")
    writer.WriteLine(f"OutputFilename0={outputFile}")
    writer.Close()
    pluginInfoFilename = Path.Combine(ClientUtils.GetDeadlineTempPath(), "sick_usd_plugin_info.job")
    writer = StreamWriter(pluginInfoFilename, False, Encoding.Unicode)
    writer.WriteLine(f"InputFile={usdFile}")
    writer.WriteLine(f"OutputFile={outputFile}")
    writer.Close()
    arguments = StringCollection()
    arguments.Add(jobInfoFilename)
    arguments.Add(pluginInfoFilename)
    results = ClientUtils.ExecuteCommandAndGetOutput(arguments)
    scriptDialog.ShowMessageBox(results, "Submission Results")

if __name__ == "__main__":
    __main__()