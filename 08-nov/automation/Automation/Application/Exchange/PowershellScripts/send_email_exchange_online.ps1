
$rand = new-object system.random
################################
## Generates the Subject content ##
################################
function getSubject()
{
	$subjects = get-content -path $rootPath\subjects.txt
	$subject = $subjects[$rand.next(0,($subjects.count))] + " - " + $rand.next(1,999999999)
	[GC]::Collect()  ## Garbage collection
	return $subject
}


################################
## Generates the body content ##
################################
function getBody()
{
	$bodies = get-childitem -path $rootPath\Body
	$body = $bodies[$rand.next(0,$bodies.count)].name
	$bodyContent = get-content $rootPath\Body\$body
	if($body.Contains(".txt"))
	{
		$bodyTxt = ""
		foreach($line in $bodyContent)
		{
			$bodyTxt+= $line + "<br>"		
		}
	return $bodyTxt
	}
	else 
	{
		return $bodyContent
	}
}

################################
## Generates the body content ##
################################
function sendMail([int]$messages,$adminname,$adminpwd,$smtpserver)
{
    for($m=1; $m -le [int]$messages; $m+=1)
	    {
            $subject = getSubject
            $body = getBody
            $User = get-content -path $rootPath\userlist.txt
            $to = get-content -path $rootPath\userlist.txt 
            $from = $adminname

                $emailMessage = New-Object System.Net.Mail.MailMessage
                    $emailMessage.Subject = $subject
                    $attach = get-childitem -path $rootPath\Attach
                    if($rand.next(0,2))
		                {
                            $rand.next(0,2)
			                ###Find and attach each attachment to the message
			                $numAttach = $rand.next(1,5)
                            #This is the number of possible attachments to the message
			                for ($i=1; $i -le $numAttach; $i+=1)
			                {
				                $attachFileName = "$rootPath\Attach\" + $attach[$rand.next(0,($attach.count))].Name
                                $attachment = new-object System.Net.Mail.Attachment $attachFileName
                                $emailMessage.Attachments.add($attachment)
			                }
		                }
                    $emailMessage.From= $adminname

                    for($n=1; $n -le $to.count; $n+=1)
                    {

                    $emailMessage.To.Add(($to[$n-1]))

                    }
                    $emailMessage.IsBodyHtml = $true
                    $emailMessage.Body = $body

                    $SMTPClient = New-Object System.Net.Mail.SmtpClient( $smtpserver , 25 )
                    $SMTPClient.EnableSsl = $false
                    $SMTPClient.Credentials = New-Object System.Net.NetworkCredential( $adminname , $adminpwd );
            $SMTPClient.Send( $emailMessage )

        }
    }

Function Main()
{
 $exchangeServerName = "##Automation--SMTPSever--##"
 $exchangeAdminName = "##Automation--LoginUser--##"
 $exchangeAdminPwd = "##Automation--LoginPassword--##"
 $numberOfemails = "##Automation--NumberOfEmails--##"
 $rootPath = "##Automation--RootPath--##"
 ## $rootPath = "C:\Scripts\PowerCDO"


sendMail $numberOfemails $exchangeAdminName $exchangeAdminPwd $exchangeServerName

}
