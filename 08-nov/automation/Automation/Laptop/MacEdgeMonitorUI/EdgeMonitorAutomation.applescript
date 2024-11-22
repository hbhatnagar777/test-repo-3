property REGISTRATION_ACTIVATION_TIMEOUT : 360
property SAMLREDIRECT_TEXTFIELD_TIMEOUT : 30
property BACKUP_PROCESS_TIMEOUT : 60

property RET_CODE_SUCCESS : 100

property RET_CODE_INVALID_ARGUMENTS : 1
property RET_CODE_INVALID_CREDENTIALS : 2
property RET_CODE_TIMEOUT_TEXTFIELD : 3
property RET_CODE_INCORRECT_USER : 4
property RET_CODE_REG_TIMEOUT : 5
property RET_CODE_CONNECTION_ERROR : 6
property RET_CODE_WEBSERVICE_ERROR : 7
property RET_CODE_NOT_REG_USER : 8
property RET_CODE_ERROR : 9
property RET_CODE_BACKUP_ERROR : 10
property RET_CODE_TIMEOUT_SAMLREDIRECT_PASSWORD : 11
property RET_CODE_UI_ERROR : 12
property RET_CODE_INVALID_BACKUP_WINDOW : 13
property RET_CODE_BUTTON_ERROR : 14
property RET_CODE_PAUSE_ERROR : 15
property RET_CODE_BACKUP_TIMEOUT : 16
property RET_CODE_RETIREDCLIENT_ERROR : 17
property RET_CODE_ERROR_TAKEOVER_CLIENT_NOT_REG : 18
property RET_CODE_SUCCESS_REG_CLIENTS : 19
property RET_CODE_SUCCESS_FUNCTION : 99


on KnownPopupError() --Subroutine for Known popup errors
	run script "tell application \"System Events\"
        	if (exists static text \"Invalid login/password.\" of window \"EdgeMonitor\" of application process \"EdgeMonitor\" of application \"System Events\") then
								click button \"Okay\" of window \"EdgeMonitor\" of application process \"EdgeMonitor\" of application \"System Events\"
								return " & RET_CODE_INVALID_CREDENTIALS & " --  Invalid Password -- Returning the value 2
							end if
							if (exists static text \"Please check your internet connection and try again\" of window \"EdgeMonitor\" of application process \"EdgeMonitor\" of application \"System Events\") then
								click button \"Okay\" of window \"EdgeMonitor\" of application process \"EdgeMonitor\" of application \"System Events\"
								return " & RET_CODE_CONNECTION_ERROR & "
							end if
							if (exists static text \"Backup infrastructure is currently unavailable.
 Please try later. If problem persists, contact your administrator.\" of window \"EdgeMonitor\" of application process \"EdgeMonitor\" of application \"System Events\") then
								click button \"Okay\" of window \"EdgeMonitor\" of application process \"EdgeMonitor\" of application \"System Events\"
								return " & RET_CODE_BACKUP_ERROR & "
							end if
							if (exists static text \"Web Service is not reachable, please try again later. If the problem persists, contact your administrator.\" of window \"EdgeMonitor\" of application process \"EdgeMonitor\" of application \"System Events\") then
								click button \"Okay\" of window \"EdgeMonitor\" of application process \"EdgeMonitor\" of application \"System Events\"
								return " & RET_CODE_WEBSERVICE_ERROR & "
							end if
							return " & RET_CODE_SUCCESS_FUNCTION & "
							end tell"
end KnownPopupError

--Subroutine for RetireClient process
on RetireClientFunc(strRetireClient)
	-- Run a script to interact with the system events
	run script "tell application \"System Events\"
		-- Get the names of all radio buttons in the 'Laptop Activation' window of the 'EdgeMonitor' application process
		set List_ClientNames to name of every radio button of window \"Laptop Activation\" of application process \"EdgeMonitor\" of application \"System Events\"
		set x to 1
		
		-- Iterate through each element
		repeat while (x < (count of List_ClientNames) + 1)	
			-- Check if the current element matches the specified retire client name
			if (item x of List_ClientNames is \"" & strRetireClient & "\") then
				-- Click the 'Cancel' button in the 'Laptop Activation' window of the 'EdgeMonitor' application process
				click button \"Cancel\" of window \"Laptop Activation\" of application process \"EdgeMonitor\" of application \"System Events\"
				-- Return the retirement error code
				return " & RET_CODE_RETIREDCLIENT_ERROR & "
			end if
			set x to x + 1
		end repeat
		
		-- Return the success code for the retire client function
		return " & RET_CODE_SUCCESS_FUNCTION & "
	end tell"
end RetireClientFunc


on Client_Exists(Client_key, List_Names as list)
	-- Check if the given client key exists in the list of names
	considering case
		return List_Names contains Client_key
	end considering
end Client_Exists

on TakeOverClientsFunc(ClientList)
	-- Run a script to interact with the system events
	set List_ButtonName to run script "tell application \"System Events\"
		-- Get the names of all radio buttons in the 'Laptop Activation' window of the 'EdgeMonitor' application process
		set List_ButtonName to name of every radio button of window \"Laptop Activation\" of application process \"EdgeMonitor\" of application \"System Events\"
		return List_ButtonName
	end tell" as list
	
	set x to 1
	
	-- Iterate through each client in the client list
	repeat while (x < (count of ClientList) + 1)
		-- Check if the current client exists in the list of button names
		if (not Client_Exists(item x of ClientList, List_ButtonName)) then
			-- Return the error code for the takeover client not registered error
			return RET_CODE_ERROR_TAKEOVER_CLIENT_NOT_REG
		end if
		set x to x + 1
	end repeat
	
	-- Return the success code for registering clients
	return RET_CODE_SUCCESS_REG_CLIENTS
end TakeOverClientsFunc

-- Subroutine for Laptop Activation
on LaptopActivationFunc(TakeOverFlag, strClientName)
	-- Run a script using the "System Events" application to interact with the user interface
	run script "tell application \"System Events\"
			-- Check if the window named \"Laptop Activation\" exists in the application process \"EdgeMonitor\"
			if (exists window \"Laptop Activation\" of application process \"EdgeMonitor\" of application \"System Events\") then
				-- Check if TakeOverFlag is equal to 1
				if (" & TakeOverFlag & " is 1) then
					try
						-- Click the radio button specified by strClientName in the window named \"Laptop Activation\"
						click radio button \"" & strClientName & "\" of window \"Laptop Activation\" of application process \"EdgeMonitor\" of application \"System Events\"
					on error
						-- If an error occurs, click the \"Cancel\" button in the window and return a specific return code
						click button \"Cancel\" of window \"Laptop Activation\" of application process \"EdgeMonitor\" of application \"System Events\"
						return " & RET_CODE_NOT_REG_USER & " -- User not pre-registered or invalid ClientName argument passed.
					end try
				else
					-- If TakeOverFlag is not equal to 1, click the \"New Activation\" radio button in the window named \"Laptop Activation\"
					click radio button \"New Activation\" of window \"Laptop Activation\" of application process \"EdgeMonitor\" of application \"System Events\"
				end if
				
				-- Delay of 2 seconds to let radio button be selected
				delay 2
				
				-- Click the \"Activate\" button in the window named \"Laptop Activation\"
				click button \"Activate\" of window \"Laptop Activation\" of application process \"EdgeMonitor\" of application \"System Events\"
			end if
			return " & RET_CODE_SUCCESS_FUNCTION & "
		end tell"
end LaptopActivationFunc



-- Subroutine for Generic PopupError
on GenericPopupError()
	
	-- Run a script using the "System Events" application to interact with the user interface
	run script "tell application \"System Events\"
	
			-- Retrieve the value of every static text element in the window named \"EdgeMonitor\"
			set iStaticText_count to value of every static text of window \"EdgeMonitor\" of application process \"EdgeMonitor\" of application \"System Events\"
			set x to 1

			-- Iterate through each static text element
			repeat while (x < (count of iStaticText_count) + 1)
				-- Check if the current static text element is not equal to \"Edge Monitor\" or \"EdgeMonitor\"
				if (item x of iStaticText_count is not \"Edge Monitor\" and item x of iStaticText_count is not \"EdgeMonitor\") then
					-- Click the button named \"Okay\" in the window named \"EdgeMonitor\"
					click button \"Okay\" of window \"EdgeMonitor\" of application process \"EdgeMonitor\" of application \"System Events\"
					-- Return the value of the current static text element
					return item x of iStaticText_count
				end if
				set x to x + 1
			end repeat
			return " & RET_CODE_SUCCESS_FUNCTION & "
		end tell"
	
end GenericPopupError






on run argv
	try
		tell application "System Events"
			set strKeyName to quoted form of "sProductName"
			set theCommand to " /etc/CommVaultRegistry/Galaxy/Instance001/Base/.properties | awk '{print $2}' "
			set strProductName to do shell script " grep " & strKeyName & theCommand
			set AppPath to "/Applications/" & strProductName & " Edge Monitor.app"
			set PathToEdgeMonitor to alias AppPath
			set x to 1 -- item number for argv
			set strUsername to ""
			set strPassword to ""
			set iTypeOfRegistration to 0 as integer
			set strClientName to ""
			set SAMLflag to 0
			set TakeOverFlag to 0
			set myTime to 0
			set DoLoginFlag to 0
			set strAuthCode to ""
			set strRetireClient to ""
			set TakeOverClientsFlag to 0
			set AuthCodeRegistrationFlag to 0
			set LaptopActivationFlag to 0
			set strPausePeriod to ""
			set ClientList to {}
			set icount to count of items of argv
			
			
			-- Loop to iterate through the items in argv
			repeat while (x is not icount + 1)
				if (item x of argv is "-UserName") then -- checking if the current item is "-UserName"
					set x to x + 1
					try
						set strUsername to item x of argv -- setting strUsername with the value following "-UserName"
					on error
						return RET_CODE_INVALID_ARGUMENTS
					end try
				else if (item x of argv is "-UserPassword") then -- checking if the current item is "UserPassword"
					set x to x + 1
					try
						set strPassword to item x of argv -- setting strPassword with the value following "UserPassword"
					on error
						return RET_CODE_INVALID_ARGUMENTS
					end try
				else if (item x of argv is "-Type") then -- checking if the current item is "-type"
					set x to x + 1
					try
						set iTypeOfRegistration to item x of argv as integer -- setting iTypeOfRegistration with the value following "-type"
					on error
						return RET_CODE_INVALID_ARGUMENTS -- if there is no item x after corresponding argument
					end try
				else if (item x of argv is "-ClientName") then -- checking if the current item is "-type"
					set x to x + 1
					try
						set strClientName to item x of argv -- setting iTypeOfRegistration with the value following "-type"
					on error
						return RET_CODE_INVALID_ARGUMENTS
					end try
				else if (item x of argv is "-AuthCode") then -- checking if the current item is "-AuthCode"
					set x to x + 1
					try
						set strAuthCode to item x of argv -- setting  strAuthCode with the value following "-AuthCode"					
					on error
						return RET_CODE_INVALID_ARGUMENTS
					end try
				else if (item x of argv is "-RetiredClientName") then -- checking if the current item is "-RetiredClientName"
					set x to x + 1
					try
						
						set strRetireClient to item x of argv -- setting  strRetireClient with the value following "-RetiredClientName"		
						display dialog strRetireClient
					on error
						return RET_CODE_INVALID_ARGUMENTS
					end try
					
				else if (item x of argv is "-TakeOverClients") then -- checking if the current item is "-RetiredClientName"
					set x to x + 1
					set Client_String to item x of argv
					set AppleScript's text item delimiters to ","
					set ClientNames to text items in Client_String
					set AppleScript's text item delimiters to "" -- setting the delimiter back
					
					
					set iCountClients to count every text item of ClientNames
					set TakeOverClientsFlag to 1
					set y to 1
					try
						repeat iCountClients times
							set end of ClientList to text item y of ClientNames
							set y to y + 1
						end repeat
						
					on error
						return RET_CODE_INVALID_ARGUMENTS
					end try
				else if (item x of argv is "-isSAML") then -- checking if the current item is "-isSAML"
					set SAMLflag to 1 -- setting  SAMLflag  1  
				else if (item x of argv is "-TakeOver") then -- checking if the current item is "-TakeOver"
					set TakeOverFlag to 1 -- setting  TakeOverFlag  1  
				else if (item x of argv is "-DoLogin") then -- checking if the current item is "-DoLogin"
					set DoLoginFlag to 1 -- setting  DoLoginFlag 1
				else if (item x of argv is "-PausePeriod") then -- checking if the current item is "-PausePeriod"
					set x to x + 1
					try
						set strPausePeriod to item x of argv -- setting  strAuthCode with the value following "-PausePeriod"					
					on error
						return RET_CODE_INVALID_ARGUMENTS
					end try
				end if
				set x to x + 1
			end repeat
			--end of argv iteration 			
			--Checking for invalid syntax 
			if (strUsername is "") then
				if ((iTypeOfRegistration is 1 and DoLoginFlag is 0) or iTypeOfRegistration > 2) then
				else
					return RET_CODE_INVALID_ARGUMENTS
				end if
			end if
			if (strPassword is "") then
				if ((iTypeOfRegistration is 1 and DoLoginFlag is 0) or iTypeOfRegistration > 2) then
				else
					return RET_CODE_INVALID_ARGUMENTS
				end if
				
			end if
			if (iTypeOfRegistration ² 0 or iTypeOfRegistration > 6) then
				return RET_CODE_INVALID_ARGUMENTS
			end if
			if (TakeOverFlag is 1 and strClientName is "") then
				return RET_CODE_INVALID_ARGUMENTS
			end if
			if (iTypeOfRegistration is 1 and strAuthCode is "") then
				return RET_CODE_INVALID_ARGUMENTS
			end if
			
			
			-- Checking if process EdgeMonitor is already running.
			-- The app has to quit and restart  because as of now we are not able to click on application icon and bring it to foreground. 
			if (exists process "EdgeMonitor") then
				tell application "System Events"
					quit application "EdgeMonitor" -- quitting the EdgeMonitor application if it's running
					delay 2
				end tell
			end if
			
			
			-- Opening application using EdgeMonitorShortcut.app
			
			tell application "System Events" to open PathToEdgeMonitor
			-- Delay for the EdgeMonitor process to run 
			delay 2
			
			if (iTypeOfRegistration < 3) then --Only type less than 3 needs to wait for the computer field to get filled
				-- Waiting until the  Computer Name field is empty
				set myTime to (time of (current date))
				repeat while value of text field 3 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" is ""
					delay 1
					if (time of (current date) > myTime + SAMLREDIRECT_TEXTFIELD_TIMEOUT) then
						return RET_CODE_TIMEOUT_TEXTFIELD --Timeout for  computer name field 
					end if
				end repeat
				delay 2
				
				-- Filling the Computer name field with ClientName when Takeoverflag is 0
				if (strClientName is not "" and TakeOverFlag is 0) then
					set value of text field 3 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" to strClientName
				end if
			end if
			repeat
				-- AuthCode login flow is the same as username-password based login with type 2.
				-- In order to avoid repeated code, flag AuthCodeRegistrationFlag is set to 1 after authcode-based registration is complete if DoLoginFlag is set to 1.
				
				if (iTypeOfRegistration is 2 or AuthCodeRegistrationFlag is 1) then -- checking if iTypeOfRegistration is "2"
					set value of text field 1 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" to strUsername -- setting the value of the username field  
					delay 2
					click button "Continue" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" -- clicking the "Continue" button
					
					repeat while exists button "Continue" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" -- after continue button is pressed we will wait till continue button is there and see if following error occurrs 
						-- Checking if the "EdgeMonitor" window exists
						
						if (exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then
							
							set returnValue to my KnownPopupError() --calling function KnownPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
							set returnValue to my GenericPopupError() --calling function GenericPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
							
						end if
					end repeat
					
					if (exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then
						
						set returnValue to my KnownPopupError() --calling function KnownPopupError
						if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
							return returnValue
						end if
						set returnValue to my GenericPopupError() --calling function GenericPopupError
						if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
							return returnValue
						end if
					end if
					
					
					delay 2
					
					if (SAMLflag is 1) then --for SAML user
						
						set myTime to (time of (current date))
						repeat while (not (exists text field 1 of group 2 of UI element 1 of scroll area 1 of group 1 of group 1 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events")) -- Waiting until the  SAML webview loaded
							
							if (focused of text field 2 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" is true) then --Checking if User is not SAML --(*)
								if (not (exists text field 1 of group 2 of UI element 1 of scroll area 1 of group 1 of group 1 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events")) then --Double checking if SAML redirection has happen if not then returning  incorrect user type
									return RET_CODE_INCORRECT_USER --incorrect user type(Not SAML)
								end if
							end if
							if time of (current date) > myTime + SAMLREDIRECT_TEXTFIELD_TIMEOUT then
								return RET_CODE_TIMEOUT_SAMLREDIRECT_PASSWORD --Timeout for SAML redirect. 
							end if
						end repeat
						delay 1
						set value of text field 1 of group 2 of UI element 1 of scroll area 1 of group 1 of group 1 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" to strPassword --Password field in the webview
						delay 1
						
						click button "Sign in" of group 4 of group 2 of UI element 1 of scroll area 1 of group 1 of group 1 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" -- clicking the "Sign in" button
						delay 1
						
						--Checking for invalid password 
						if (exists static text "Your account or password is incorrect. If you can't remember your password," of group 1 of group 1 of group 2 of UI element 1 of scroll area 1 of group 1 of group 1 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events") then
							return RET_CODE_INVALID_CREDENTIALS --  Invalid Password
						end if
						delay 1
						if (exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then
							
							set returnValue to my KnownPopupError() --calling function KnownPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
							set returnValue to my GenericPopupError() --calling function GenericPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
						end if
						click button "Yes" of group 3 of group 2 of UI element 1 of scroll area 1 of group 1 of group 1 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events"
						delay 2
						
						set myTime to (time of (current date))
						repeat while (exists static text "Registration is in progress.
We're setting up the software for you. This might take a few minutes." of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events") -- Waiting while Registration  process is running  
							
							if (time of (current date) > myTime + REGISTRATION_ACTIVATION_TIMEOUT) then
								return RET_CODE_REG_TIMEOUT -- Timeout for Registration or Activation process. If Registration or Activation process takes more than 360 sec(6 min) than  return  RET_CODE_REG_TIMEOUT.  							
							end if
							if (exists window "Laptop Activation" of application process "EdgeMonitor" of application "System Events") then
								set LaptopActivationFlag to 1
								if (ClientList is not {}) then --Checking if -TakeOverClients argument is passed and if the list contains the ClientNames
									set returnValue to my TakeOverClientsFunc(ClientList)
									click button "Cancel" of window "Laptop Activation" of application process "EdgeMonitor" of application "System Events"
									return returnValue
									--We will return the return value of the function to exit the script
								end if
								if (strRetireClient is not "") then
									set returnValue to my RetireClientFunc(strRetireClient)
									if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
										return returnValue
									end if
								end if
							end if
							set returnValue to my LaptopActivationFunc(TakeOverFlag, strClientName) --calling function  for Laptop Activation
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
							
							
							if (exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then
								
								set returnValue to my KnownPopupError() --calling function KnownPopupError
								if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
									return returnValue
								end if
								set returnValue to my GenericPopupError() --calling function GenericPopupError
								if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
									return returnValue
								end if
							end if
							delay 1
						end repeat
						
						if (LaptopActivationFlag is 0 and ClientList is not {}) then
							return RET_CODE_ERROR_TAKEOVER_CLIENT_NOT_REG
						end if
						
						if (exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then
							set returnValue to my KnownPopupError() --calling function KnownPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
							set returnValue to my GenericPopupError() --calling function GenericPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
						end if
						delay 4 --Waiting for the main view to come up
						
						if (exists static text "Backup" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events") then
							return RET_CODE_SUCCESS --Success
						end if
						return RET_CODE_ERROR --After or during  the registration and activation if any error occurs
						
					end if -- End for SAML-user
					
					-- Waiting until the password field is comes and filling it
					set myTime to (time of (current date))
					repeat while (value of text field 2 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" is "")
						delay 1
						
						-- Checking if the username field is displayed
						if (exists text field 1 of group 2 of UI element 1 of scroll area 1 of group 1 of group 1 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events") then
							return RET_CODE_INCORRECT_USER --incorrect user type    -- Returning the value 4
						end if
						if time of (current date) > myTime + SAMLREDIRECT_TEXTFIELD_TIMEOUT then
							return RET_CODE_TIMEOUT_SAMLREDIRECT_PASSWORD --Timeout for password textfield. If the process takes more than 30 seconds  return  RET_CODE_INVALID_ARGUMENTS1
						end if
						
						-- Setting password field 
						set value of text field 2 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" to strPassword
					end repeat
					
					delay 2
					
					-- Clicking the "Sign in" button
					click button "Sign in" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events"
					
					-- Checking if during the AuthCode Login Invalid Password field comes 
					if (AuthCodeRegistrationFlag is 1) then
						repeat while (exists busy indicator 1 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events") --using busy indicator because in normal type 2 login registartion in progress comes while loading but for AuthCode a loading indicator is the only parameter to check for the loading  process.
						end repeat
						delay 1
						if (exists static text "Invalid Credentials. Please try again." of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events") then
							return RET_CODE_INVALID_CREDENTIALS --Invalid Password for Authcode
						end if
						
						if (exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then
							set returnValue to my KnownPopupError() --calling function KnownPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
							set returnValue to my GenericPopupError() --calling function GenericPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
						end if
					end if
					
					delay 3
					
					-- Checking the progress of registration
					set myTime to (time of (current date))
					repeat while (exists static text "Registration is in progress" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events")
						delay 2
						
						-- Checking if the time exceeds the maximum allowed time for registration
						if (time of (current date) > myTime + REGISTRATION_ACTIVATION_TIMEOUT) then
							return RET_CODE_REG_TIMEOUT -- Timeout for Registration or Activation process. If Registration or Activation process takes more than 360 sec(6 min) than  return  RET_CODE_REG_TIMEOUT.  						
						end if
						
						if (exists window "Laptop Activation" of application process "EdgeMonitor" of application "System Events") then
							set LaptopActivationFlag to 1
							if (ClientList is not {}) then
								set returnValue to my TakeOverClientsFunc(ClientList)
								click button "Cancel" of window "Laptop Activation" of application process "EdgeMonitor" of application "System Events"
								return returnValue
							end if
							if (strRetireClient is not "") then
								set returnValue to my RetireClientFunc(strRetireClient)
								if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
									return returnValue
								end if
							end if
						end if
						
						
						set returnValue to my LaptopActivationFunc(TakeOverFlag, strClientName) --calling function  for Laptop Activation
						if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
							return returnValue
						end if
						
						if (exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then
							
							set returnValue to my KnownPopupError() --calling function KnownPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
							set returnValue to my GenericPopupError() --calling function GenericPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
						end if
						
					end repeat
					
					if (LaptopActivationFlag is 0 and ClientList is not {}) then
						return RET_CODE_ERROR_TAKEOVER_CLIENT_NOT_REG
					end if
					
					
					-- Checking if the popup window exists
					if (exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then
						
						set returnValue to my KnownPopupError() --calling function KnownPopupError
						if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
							return returnValue
						end if
						set returnValue to my GenericPopupError() --calling function GenericPopupError
						if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
							return returnValue
						end if
					end if
					
					delay 2
					
					set myTime to (time of (current date))
					repeat while (exists static text "Activation is in progress.
We're setting up the software for you. This might take a few minutes." of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events")
						-- Repeat the following code block as long as the specified text exists in the designated location
						
						if (time of (current date) > myTime + REGISTRATION_ACTIVATION_TIMEOUT) then
							-- If the current time exceeds the time stored in 'myTime' plus 360 seconds (5 minutes)
							return RET_CODE_REG_TIMEOUT -- Timeout for Registration or Activation process. If Registration or Activation process takes more than 360 sec(6 min) than  return  RET_CODE_REG_TIMEOUT.  							
							
						end if
					end repeat
					
					set myTime to (time of (current date))
					repeat while (exists button "Sign in" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events")
						delay 1
						if (time of (current date) > myTime + REGISTRATION_ACTIVATION_TIMEOUT) then
							return RET_CODE_REG_TIMEOUT --Timeout for Registration or activation process
						end if
					end repeat
					
					delay 4
					
					-- Checking if the "Backup Now" button exists
					if (exists static text "Backup" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events") then
						return RET_CODE_SUCCESS
					end if
					
					return RET_CODE_ERROR -- After or during  the registration and activation if any error occurs
					
					
				else if (iTypeOfRegistration is 1) then -- checking if iTypeOfRegistration is "1"
					
					-- Using auth code for registration
					click button "Or use auth code" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events"
					delay 1
					
					-- Setting the value of the auth code field
					set value of text field 1 of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" to strAuthCode
					delay 1
					
					-- Clicking the "Sign in" button
					click button "Sign in" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events"
					
					delay 1
					
					-- Checking the progress of registration
					set myTime to (time of (current date))
					repeat while (exists static text "Registration is in progress" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events")
						
						-- Checking if the time exceeds the maximum allowed time for registration
						if (time of (current date) > myTime + 600) then
							return RET_CODE_REG_TIMEOUT -- Timeout for Registration or Activation process. If Registration or Activation process takes more than 360 sec(6 min) than  return  RET_CODE_REG_TIMEOUT.  
						end if
						
						
						
						if (exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then
							if (exists static text "Given authcode is not valid. Please provide the correct authcode to proceed with registration." of window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then -- Checking for invalid authcode passed
								click button "Okay" of window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events"
								return RET_CODE_INVALID_CREDENTIALS
							end if
							
							my GenericPopupError()
						end if
						
						delay 1
					end repeat
					delay 1
					if (exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then
						if (exists static text "Given authcode is not valid. Please provide the correct authcode to proceed with registration." of window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then -- Checking for invalid authcode passed
							click button "Okay" of window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events"
							return RET_CODE_INVALID_CREDENTIALS
						end if
						
						my GenericPopupError()
					end if
					
					delay 2
					
					set myTime to (time of (current date))
					repeat while (exists static text "Activation is in progress.
We're setting up the software for you. This might take a few minutes." of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events")
						-- Repeat the following code block as long as the specified text exists in the designated location
						
						if (time of (current date) > myTime + REGISTRATION_ACTIVATION_TIMEOUT) then
							return RET_CODE_REG_TIMEOUT -- Timeout for Registration or Activation process. If Registration or Activation process takes more than 360 sec(6 min) than  return  RET_CODE_REG_TIMEOUT.  						
						end if
						delay 2
						
					end repeat
					
					delay 3
					-- Checking if the login flag is enabled
					if (DoLoginFlag is 1) then
						set AuthCodeRegistrationFlag to 1
					else
						if (exists static text "Login" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events") then
							return RET_CODE_SUCCESS
						end if
						return RET_CODE_ERROR
					end if
				end if
				
				
				
				
				
				
				--AS OF NOW THIS PART OF THE CODE IS NOT FUNCTIONING AS EXPECTED. ONCE THE CLICKING ISSUE IS RESOLVED THIS SHOULD WORK
				
				
				
				
				
				
				
				
				
				if (iTypeOfRegistration > 2) then
					if (not (exists static text "Backup" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events")) then --Checking for the Backup window
						return RET_CODE_INVALID_BACKUP_WINDOW
					end if
				end if
				
				if (iTypeOfRegistration is 3) then --Backup button
					try
						click button "Backup Now" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events"
					on error
						return RET_CODE_BUTTON_ERROR --if Backup button is not present or error trying to access the backup button
					end try
					set myTime to (time of (current date))
					repeat until (exists static text "Backup in progress on Server..." of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events") --repeating until Backup in progress on server... comes meaning backup has started.
						
						if (time of (current date) > myTime + BACKUP_PROCESS_TIMEOUT) then
							return RET_CODE_BACKUP_TIMEOUT -- Timeout for Backup process. If backup process takes more than 60 sec(1 min) than  return  RET_CODE_BACKUP_TIMEOUT.  						
						end if
						
						delay 1
					end repeat
					return RET_CODE_SUCCESS
				end if
				
				if (iTypeOfRegistration is 4) then --Pause button
					try
						click button "Pause" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events"
					on error
						return RET_CODE_BUTTON_ERROR --if Pause button is not present or error trying to access the Pause button
					end try
					if exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events" then
						if (exists static text "Unable to pause backup" of window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then -- Error trying to pause Backup
							click button "Okay" of window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events"
							return RET_CODE_PAUSE_ERROR
						end if
						my GenericPopupError()
					end if
					
					
					if exists pop over 1 of button "Pause" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" then
						if (strPausePeriod is "") then
							click button "1 hour" of pop over 1 of button "Pause" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events"
						else
							try
								click button strPausePeriod of pop over 1 of button "Pause" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events"
							on error
								return RET_CODE_PAUSE_ERROR
							end try
						end if
					end if
					
					set myTime to (time of (current date))
					repeat until exists static text "The backup job has been paused." of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events" --repeating until  Backup job has been paused text comes meaning backup has paused.
						
						if (time of (current date) > myTime + BACKUP_PROCESS_TIMEOUT) then
							return RET_CODE_BACKUP_TIMEOUT -- Timeout for Backup process. If backup process takes more than 60 sec(1 min) than  return  RET_CODE_BACKUP_TIMEOUT.  						
						end if
						if exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events" then
							if (exists static text "Unable to pause backup" of window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then -- Error trying to pause Backup
								click button "Okay" of window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events"
								return RET_CODE_PAUSE_ERROR
							end if
							
							set returnValue to my GenericPopupError() --calling function GenericPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
						end if
						
						delay 1
					end repeat
					delay 1
					if exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events" then
						if (exists static text "Unable to pause backup" of window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events") then -- Error trying to pause Backup
							click button "Okay" of window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events"
							return RET_CODE_PAUSE_ERROR
						end if
						set returnValue to my GenericPopupError() --calling function GenericPopupError
						if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
							return returnValue
						end if
					end if
					
					return RET_CODE_SUCCESS
				end if
				
				if (iTypeOfRegistration is 5) then --Resume button
					try
						click button "Resume Backup" of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events"
					on error
						return RET_CODE_BUTTON_ERROR
					end try
					delay 1
					
					set myTime to (time of (current date))
					repeat until (exists static text "Backup in progress on Server..." of pop over 1 of menu bar 2 of application process "EdgeMonitor" of application "System Events") --repeating until Backup in progress on server... comes meaning backup has started.
						
						if (time of (current date) > myTime + BACKUP_PROCESS_TIMEOUT) then
							return RET_CODE_BACKUP_TIMEOUT -- Timeout for Backup process. If backup process takes more than 60 sec(1 min) than  return  RET_CODE_BACKUP_TIMEOUT.  						
						end if
						if exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events" then
							
							set returnValue to my GenericPopupError() --calling function GenericPopupError
							if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
								return returnValue
							end if
						end if
						delay 1
					end repeat
					delay 1
					if exists window "EdgeMonitor" of application process "EdgeMonitor" of application "System Events" then
						
						set returnValue to my GenericPopupError() --calling function GenericPopupError
						if (returnValue is not RET_CODE_SUCCESS_FUNCTION) then
							return returnValue
						end if
					end if
					
					return RET_CODE_SUCCESS
				end if
			end repeat
		end tell
	on error
		return RET_CODE_UI_ERROR
	end try
end run

