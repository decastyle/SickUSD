from Deadline.Plugins import DeadlinePlugin
from Deadline.Scripting import RepositoryUtils

class SickUSDPlugin(DeadlinePlugin):

    def __init__(self):
        super().__init__()
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument

    def Cleanup(self):
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback

    def InitializeProcess(self):
        self.SingleFramesOnly = True
        self.StdoutHandling = True
        self.AddStdoutHandlerCallback("ERROR.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".* ([0-9]+)% done").HandleCallback += self.HandleProgress

    def RenderExecutable(self):
        return self.GetConfigEntry("SickUSD_SickExecutable")

    def RenderArgument(self):
        inputFile = self.GetPluginInfoEntry("InputFile")
        inputFile = RepositoryUtils.CheckPathMapping(inputFile)
        outputFile = self.GetPluginInfoEntry("OutputFile")
        outputFile = RepositoryUtils.CheckPathMapping(outputFile)
        frame = self.GetStartFrame()
        args = f"-i \"{inputFile}\" -f {frame}"
        if outputFile:
            args += f" -o \"{outputFile}\""
        return args

    def HandleStdoutError(self):
        self.FailRender(self.GetRegexMatch(0))

    def HandleProgress(self):
        self.SetProgress(float(self.GetRegexMatch(1)))

def GetDeadlinePlugin():
    return SickUSDPlugin()

def CleanupDeadlinePlugin(deadlinePlugin):
    deadlinePlugin.Cleanup()