#!/bin/sh
ParentDir=$(dirname "$0")
EMAutomate=`osascript "$ParentDir"/EdgeMonitorAutomation.applescript $@`
case $EMAutomate in
    100)
        echo "Automation Successful"
        exit 100
        ;;
    1)
        echo "Invalid Arguments passed"
        exit 1
        ;;
    2)
        echo "Invalid Password/Username"
        exit 2
        ;;
    3)
        echo "Timeout for Computer name field"
        exit 3
        ;;
    4)
        echo "Incorrect User Type"
        exit 4
        ;;
    5)
        echo "Timeout for registration or activation process"
        exit 5
        ;;
    6)
        echo "Please check your internet connection and try again"
        exit 6
        ;;
    7)
        echo "Web Service is not reachable, please try again later. If the problem persists, contact your administrator."
        exit 7
        ;;
    8)
        echo "User not pre-registered or invalid Clientname argument passed"
        exit 8
        ;;
    9)
        echo "Error occurred after or during Registration and Activation process"
        exit 9
        ;;
    10)
        echo "Backup infrastructure is currently unavailable. Please try later. If problem persists, contact your administrator"
        exit 10
        ;;
    11)
        echo "Timeout for SAML redirect or Timeut for password field "
        exit 11
        ;;
    12)
        echo "Error trying to acess UI elements"
        exit 12
        ;;
    13)
        echo "Error trying to access Backup window"
        exit 13
        ;;
    14)
        echo "Error trying to access Backup window Buttons"
        exit 14
        ;;
    15)
        echo "Error trying to pause Backup"
        exit 15
        ;;
    16)
        echo "Timeout for Backup process"
        exit 16
        ;;
    17)
        echo "Error Client is not Retired"
        exit 17
        ;;
    18)
        echo "Error Clients are not registered"
        exit 18
        ;;
    19)
        echo "Given Clients are Registered"
        exit 19
        ;;
        
    *)
        echo "Invalid return code. Aomething went wrong $EMAutomate"
        exit $EMAutomate
        ;;
esac

