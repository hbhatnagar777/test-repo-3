
SET NOCOUNT ON

DECLARE @spidstr varchar(8000)
DECLARE @ConnKilled smallint
DECLARE @DBName varchar(50)
DECLARE @DBName1 varchar(50)
DECLARE @withmsg bit=1
DECLARE @DBcount int
DECLARE @DBcount1 int
DECLARE @DBflag int

SET @ConnKilled=0
SET @spidstr = ''
SET @DBName =('$(databasename)')
SET @DBcount1 = ('$(dbcount)')
SET @DBflag = ('$(dbflag)')
SET @DBcount = 1

WHILE (@DBcount <= @DBcount1) 
BEGIN
 
IF @DBflag != 1
	SET @DBName1 = @DBName + str(@dbcount,len(@DBcount))
ELSE
	SET @DBName1 = @DBName

IF db_id(@DBName1) < 4 
BEGIN
	PRINT 'Connections to system databases cannot be killed'
	PRINT db_id(@DBName1)
	RETURN
END

SET @spidstr = ''
SET @ConnKilled = 0

SELECT @spidstr=coalesce(@spidstr,',' ) + 'kill '+ convert(varchar, spid)+ '; '
FROM master..sysprocesses WHERE dbid = db_id(@DBName1) AND spid != @@SPID

IF LEN(@spidstr) > 0 
BEGIN
	EXEC(@spidstr)

	SELECT @ConnKilled = COUNT(1)
	FROM master..sysprocesses WHERE dbid=db_id(@DBName1) 

END

IF @withmsg =1
	PRINT  CONVERT(VARCHAR(10), @ConnKilled) + ' Connection(s) killed for DB :'+ @DBName1
	
SET @DBcount += 1 
END
