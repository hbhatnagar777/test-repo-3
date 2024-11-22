Edge Monitor Automation

In the Edge Monitor folder, there are 2 script files. 1.EdgeMonitorAutomationScript.sh, 2.EdgeMonitorAutomation.applescript.

EdgeMonitorAutomationScript.sh is just a wrapper script which calls the actual EdgeMonitorAutomation.applescript and print the success/error message. 
EdgeMonitorAutomation.applescript is the actual automation script which does UI automation. 


Instructions to use	
		
		
	Supported Platform:

		Supported Only on Ventura and above

	General Instruction:

		When the automation scripts starts don’t move the mouse or takeover the UI control. Since its UI based Automation.

 		Pass Username and Password arguments value in single inverted comma.

		Make sure EdgeMonitorAutomationScript.sh, EdgeMonitorAutomation.applescript to have it in same folder. 
		
		In the case of Registration using SAML User pass SAML email ID as a argument for Username


	Supported Arguments: 
  		
		osascript EdgeMonitorAutomation.applescript -Type <value> -UserName <value> -UserPassword <value> -isSAML -AuthCode <value> -TakeOver -ClientName <value> -DoLogin -TakeOverClients <value1>,<value2>,<value3> -RetiredClientName <value>

		-Type:
		      1 -  AuthCode based Registration
		      2 -  Username Password Login

		As of now Type 3,4,5 won't work as expected because we are not able to click on the pop over window

		      3 -  Start Backup process
		      4 -  Pause Backup Process
		      5 -  Resume Backup Process

		-UserName:
			  Argument for Username

		-UserPassword:  
			  Argument for Password

		 -isSAML:
			  If the username passed is expected to be a SAMl user then pass this. ( Optional )

		-AuthCode: 
			  This will go with "-Type 1" argument for AuthCode only.


		-ClientName:
			  This will be used for computerName field or for takeover ( optional )
  
		 -TakeOver: 
			  Without takeover flag by default new activation will be attempted. To perform takeover pass this argument along with clientname
 			  Optiona argument.		

 		-DoLogin: 
			  This argument will go only with -AuthCode, to do the login (optional). If this Is passed then its mandatory to pass username and password.  

		-TakeOverClients:
			  This argument is used for checking if multiple clients passed are registered or not.
			  After this argument multiple clients names are passed seperated by a delimiter ','. 

		-RetiredClientName:
			  This argument is used for checking if the client is retired or not.
			  After this argument single clientname is passed.
		
		
	Examples to use EdgeMonitorAutomation.applescript directly :
		
   		Registration using Non-SAML User

			1. EdgeMonitorAutomation.applescript -Type 2 -UserName 'username' -UserPassword 'password'
			
			Flow :
			a. If at all it identifies user passed is SAML, it will exit with error
			b. If the take over screen comes, then new activation is chosen by default. 
			c. Scripts exit once the registration/activation competes and main view for backups comes

		
			2. EdgeMonitorAutomation.applescript -Type 2 -UserName 'username' -UserPassword 'password' -ClientName 'clientname'

			Flow:
			Same as 1. But ClientName passed will be added to the client name filed in the computerName field
			
			3. EdgeMonitorAutomation.applescript -Type 2 -UserName 'username' -UserPassword 'password' -ClientName 'clientname' -TakeOver
		
			Same as 2. But If the takeover screen pops up then the given client name will be used to take over the laptop.
			If the given client name is not present in the pre existing clients, script will return with error. 


		Registration using SAML User

			4. osascript EdgeMonitorAutomation.applescript -Type 2 -UserName 'username' -UserPassword 'password' -isSAML 

			Flow: 
			a. If at all it identifies user passed is non SAML, it will exit with error
			b. If the take over screen comes, then new activation is chosen by default. 
			c. Scripts exit once the registration/activation competes and main view for backups comes

 
			5. EdgeMonitorAutomation.applescript -Type 2 -UserName 'username' -UserPassword 'password' -isSAML -ClientName 'clientname'

			Flow:
			Same as 4. But ClientName passed will be added to the client name filed in the computerName field
			
			6. EdgeMonitorAutomation.applescript -Type 2 -UserName 'username' -UserPassword 'password' -isSAML -ClientName 'clientname' -TakeOver
			

			Flow:
			Same as 5. But If the takeover screen pops up then the given client name will be used to take over the laptop.
			If the given client name is not present in the pre existing clients, script will return with error. 


		Registration using Authcode

			7. osascript EdgeMonitorAutomation.applescript -Type 1 -AuthCode 'authcode'

			Flow:
			Given authcode will be used for registration. Once the registration is complete it will exit when the log in screen comes. 
			But this can take time since auto activation thread will kick in. 
			
			8. osascript EdgeMonitorAutomation.applescript -Type 1 -AuthCode 'authcode' -DoLogin -UserName 'username' -UserPassword  'password' -isSAML 

			9. osascript EdgeMonitorAutomation.applescript -Type 1 -AuthCode 'authcode' -DoLogin -UserName 'username' -UserPassword  'password' -isSAML 
		
		Example for TakeOverClients
               		10. osascript EdgeMonitorAutomation.applescript -Type 2 -UserName 'username' -UserPassword 'password' -ClientName 'clientname' -TakeOverClients 'client1,client2,client3'
			
			Flow:
		        Same as 2. until laptop activation window comes.Once the window appears script will check for clients names Laptop1,Laptop2,Laptop3 as radio buttons names in the window.
			if all the client names are present as radio buttons script will exit with return code 19.
			else script will exit with return code 18.

		Example for RetiredClientName
               		11. osascript EdgeMonitorAutomation.applescript -Type 2 -UserName 'username' -UserPassword 'password' -ClientName 'clientname' -RetiredClientName 'client1'
			
			Flow:
		        Same as 2. until laptop activation window comes.Once the window appears script will check for client name 'client1' as radio button name in the window.
			if the client name 'client1' is present as radio button script will exit with return code 17.
			else script will continue with the registration and activation process.
			   

	Examples to use via EdgeMonitorAutomationScript.sh

		/Users/administrator/EdgeMonitorAutomationScript.sh -Type 2 -UserName 'username' -UserPassword  'password'
  
	Error Codes:

		Return 100: Success

		Return 1:   Invalid Arguments passed 

		Return 2:   Invalid Password 
  
		Return 3:   Timeout for Computer Name Field   (if Computer field takes more than 30 sec to get filled return 3)

		Return 4:   Incorrect user type

		Return 5:   Timeout for registration process or activation progress

		Return 6:   popup window “Please check your internet connection and try again”

		Return 7:   popup window “Web Service is not reachable, please try again later. If the problem persists, contact your administrator.”  

		Return 8:   User not pre-registered or invalid ClientName argument passed

		Return 9:   After Registration and Activation process is done if any error occurs than return 9

		Return 10:  popup window “Backup infrastructure is currently unavailable. Please try later. If problem persists, contact your administrator.”  
 
		Return 11:  Timeout for SAML redirect.   (if SAML redirect takes more than 30 seconds return 11) 
                   
            		    Timeout for password Field.  (If password field for regular user takes more than 30 seconds to activate return 11)
		
		Return 12:  Error trying to access UI elements

		Return 13:  Error trying to access Backup window

		Return 14:  Error trying to access Backup window Buttons

		Return 15:  Error trying to pause Backup

		Return 16:  Timeout for Backup process
		
		Return 17:  Error Client is not Retired

		Return 18:  Error Clients are not Registered
         
		Return 19:  Given Clients are Registered
 
	  
