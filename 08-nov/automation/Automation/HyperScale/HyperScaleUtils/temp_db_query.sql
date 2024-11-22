USE [TroubleShooting]
GO

DECLARE @return_value int

EXEC @return_value = [dbo].[TL_ResizeTempDb]
@maxDataFiles = 8,
@executeSQL = 1,
@MB0orGB1Unit = 1,
@dataFileSz = 1,
@logFileSz = 2,
@moveTempDbPath = N'G:\TempDB'

SELECT 'Return Value' = @return_value

GO