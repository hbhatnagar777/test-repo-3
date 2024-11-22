const req = require('request-promise-native');
const fs = require('fs');
const NL = require("os").EOL;
const LOG_TO_CONSOLE = true;
const path = require('path');
const ntlm = require("request-ntlm-lite");
const ntlmPromise = require('request-ntlm-promise');
const shell = require("shelljs");
const logUtils = require("./logUtils.js");
const ucUtils = require("./ucUtils.js");
const _ = require('lodash');

const env = {
	projectId: process.env.CI_MERGE_REQUEST_PROJECT_ID,
	commitProjectId: process.env.CI_PROJECT_ID,
	mergeId: process.env.CI_MERGE_REQUEST_IID,
	commitId: process.env.CI_COMMIT_SHA,
	// glToken: "hZNJYHxzGLQCsdraMCxx", MHfasvNsAftUWqzbs6_Z
	glToken: process.env.gitlabtokenformergerequest,
	ucToken: process.env.uctokenforcommitrequest,	//token1
	ucApiUser: process.env.ucApiUser,
	ucApiPass: process.env.ucApiPass,
	version: process.env.BRANCH_NAME,
	buildId: process.env.BRANCH_BUILD_ID,	// depends on SP
	// version: "REL_11_0_0_BRANCH",
	// 	version: process.env.CI_MERGE_REQUEST_TARGET_BRANCH_NAME
	// buildId: "1100080",	// depends on SP
	isBatchBuild: process.env.BATCH_BUILDER,
	batchBins: process.env.BINARIES_TO_BUILD,
	serverHost: process.env.CI_SERVER_HOST,
	commitRefName: process.env.CI_COMMIT_REF_NAME,
	gitlabUserName: process.env.GITLAB_USER_EMAIL,
	gitlabUserEmail: process.env.GITLAB_USER_NAME,
	buildName: process.env.BRANCH_BUILD_NAME,
	buildExternalSource: process.env.BUILD_EXTERNAL_SOURCE,
	binaryFinderFolder: process.env.BINARY_FINDER_FOLDER, // if set, the cwd will be changed to this folder before executing the BINARY_FINDER_COMMAND
	binaryFinderCommand: process.env.BINARY_FINDER_COMMAND, // the command to execute to run the local binary finder script/utility; defaults to "getBinaries.sh"
	externalFormId: process.env.UC_EXTERNAL_FORM_ID,
	externalBuildId: process.env.UC_EXTERNAL_BUILD_ID
};

/*
 * This is the list of env vars that get passed to project-specific binary
 * finder scripts. Update this as needed if a new project requires additional
 * information:
 */
const envVarsToPassToBinaryFinder = ["mergeId", "commitId", "version", "buildId", "isBatchBuild"];

const base = "https://git.commvault.com/api/v4";
const ucBase = "https://updatecenter.commvault.com";
const projectAPI = `${base}/projects/${env.projectId}`;
const commitProjectAPI = `${base}/projects/${env.commitProjectId}`;
const changesAPI = `${base}/projects/${env.projectId}/merge_requests/${env.mergeId}/changes`;	// search for better APIs to get only filenames
const commitChangesAPI = `${base}/projects/${env.commitProjectId}/repository/commits/${env.commitId}/diff?per_page=100`;	// search for better APIs to get only filenames
const commitGetMrAPI = `${base}/projects/${env.commitProjectId}/repository/commits/${env.commitId}`;
const mrDetailsApi = `${base}/projects/${env.projectId ? env.projectId : env.commitProjectId}/merge_requests/`;	// append mr id
const getMergedRefApi = `${base}/projects/${env.projectId}/merge_requests/${env.mergeId}/merge_ref`;
const getPipelineJobsApi = (projectId, pipelineId) => `${base}/projects/${projectId}/pipelines/${pipelineId}/jobs`;

const ucFormCreateAPI = `${ucBase}/updatecenterwebapi/api/createform`;
const ucFormModifyAPI = `${ucBase}/updatecenterwebapi/api/modifyandbuildform`;
const ucFormInfo = `${ucBase}/updatecenterwebapi/api/gitlabform?GitMergeID=${env.mergeId}&GitProjectID=${env.projectId}`;
const ucCommitFormInfo = `${ucBase}/updatecenterwebapi/api/gitlabform?GitProjectID=${env.commitProjectId}&GitMergeID=`;	// append mr id
const ucModifyGitlabInfoAPI = `${ucBase}/updatecenterwebapi/api/modifygitlabinfo`;
const ucResetToCreatedState = `${ucBase}/updatecenterwebapi/api/ResetUpdateAndMoveFormToCreatedState`;
const ucDownloadSourceApi = `${ucBase}/updatecenterwebapi/api/DownloadFormSourceFiles`;
const distDir = './jobDetails';
const debugLog = `${distDir}/debug.log`;
const gitDiffRequired = `${distDir}/gitDiffRequired`;
const gitSourceProject_path_with_namespace_txt = `${distDir}/gitSourceProject_path_with_namespace.txt`;
const uc_formId_txt = `${distDir}/uc_formId.txt`;
const buildTypeOfficial = (env.mergeId == null);
// const ac_job_details_path = 'jobDetails/ac-job-details.json';
// const wc_job_details_path = 'jobDetails/wc-job-details.json';

const getLatestDependenciesPipelineApi = `${base}/projects/236/pipelines?per_page=1&page=1&ref=${env.version}`;	// using hard coded project id
const getLatestDependenciesPipelineDetailsApi = `${base}/projects/236/pipelines/`;	// using hard coded project id
const startDependenciesPipelineApi = `${base}/projects/236/pipeline?ref=${env.version}`;	// using hard coded project id

//utils
const utils = {
	now: () => {
		const dt = new Date();
		let mon = dt.getMonth();
		let day = dt.getDate();
		if (mon < 10) {
			mon = "0" + mon;
		}
		if (day < 10) {
			day = "0" + dt;
		}

		return dt.getFullYear() + ":" + mon + ":" + day + " " + dt.getHours() + ":" + dt.getMinutes() + ":" + dt.getSeconds() + ":" + dt.getMilliseconds();
	},
	logToFile: (fn, contents) => {
		fs.writeFileSync(fn, contents);
	},
	log: (msg, err, enableMaskSensitiveData) => {
		let level = err ? "ERROR" : "DEBUG";
		if(enableMaskSensitiveData){
			//Mask all occurrences of gitlab token
			let tokenString = /gitlab-ci-token:[^@]*@git.commvault.com/g;
    		msg = msg.replace(tokenString, "gitlab-ci-token:xxxxxx@git.commvault.com");
		}
		let toLog = `${utils.now()}  ${level}  ${msg}${NL}`;
		fs.appendFileSync(debugLog, toLog);
		if (LOG_TO_CONSOLE) {
			console.log(toLog);
		}
	},
	isUndefinedOrEmpty: (what) => {
		return typeof what === 'undefined' || what === '';
	},
	api: (url) => {
		utils.log('Calling API: ' + url);
		// let token = env.glToken;
		// // temp code todo remove
		// if (token == null || token == ""){
		// 	console.log('using temp code token-- remove this');
		// 	token = "MHfasvNsAftUWqzbs6_Z";
		// }
		// // temp code end
		return {
			url: url,
			headers: {
				'Private-token': env.glToken
			}
		};
	},
	execCommand: (command) => {
		utils.log("Executing command : " + command, false, true); //some commands might have gitlab token so mask them
		let res = shell.exec(command);
		if (res && res.code){
			utils.log("Command failed. Error code : " + res.code, true, true);
		}
		return res;
	},
	execCommandNative: (command, opts) => {
		utils.log("Executing command with execSync: command=[" + command + "], opts=[" + JSON.stringify(opts) + "]", false, true); //some commands might have gitlab token so mask them
		try {
			return require('child_process').execSync(command, opts);
		}
		catch(err) {
			utils.log("Command failed: " + err, true, true);
			return null;
		}
	}

 };



//app
const app = {
	init: () => {
		if (!fs.existsSync(distDir)) {
			fs.mkdirSync(distDir);
		}
		if (!fs.existsSync(debugLog)) {
			fs.writeFileSync(debugLog, "");
		}
	},
	logBinariesAfterLookup: async function(res) {
		/*
		 * Process binaries list that was previously generated via the binary
		 * finder: add binaries from labels, tweak the structure to match UC
		 * requirements, etc., then save the final list in a file.
		 */
		// check for labels on this MR
		let details = await app.getDetailsForMrSync();
		let labels = details.labels;

		// add new binaries from labels to the binary list
		let bins = JSON.parse(res);

		if (!bins.hasOwnProperty('windowsBinaries')){
			bins.WinBinaries = [];
		} else {
			// rename json key to match UC API spec
			bins.WinBinaries = bins.windowsBinaries;
			delete bins.windowsBinaries;
		}
		if (!bins.hasOwnProperty('unixBinaries')){
			bins.UnixBinaries = [];
		} else {
			// rename json key to match UC API spec
			bins.UnixBinaries = bins.unixBinaries;
			delete bins.unixBinaries;
		}

		for(let val of labels) {
			if (val.endsWith('.tar')){
				if (!bins.UnixBinaries.includes(val)){
					bins.UnixBinaries.push(val);
				}
			} else if (val.endsWith('.see')){
				if (!bins.WinBinaries.includes(val)){
					bins.WinBinaries.push(val);
				}
			} else if (val.endsWith('.cmd')){
				if (!bins.WinBinaries.includes(val)){
					bins.WinBinaries.push(val);
				}
			} else if (val.endsWith('.sh') || val === 'cvToolsBase.sh.tmpl'){
				if (!bins.UnixBinaries.includes(val)){
					bins.UnixBinaries.push(val);
				}
			} else {
				// add to both
				if (!bins.WinBinaries.includes(val)){
					bins.WinBinaries.push(val);
				}
				if (!bins.UnixBinaries.includes(val) && val !== "cv-ac-master" && val !== "cv-wc-master"){
					bins.UnixBinaries.push(val);
				}
			}
		}

		// !!!! Remove this later once the external sources pipeline project is completed and well-tested:
		// add wc-messages if there is any jar binary
		if (!bins.WinBinaries.includes('wc-messages.jar') && bins.WinBinaries.some(e => (e.startsWith('wc-') && e.endsWith('.jar')))){
			bins.WinBinaries.push('wc-messages.jar');
			bins.UnixBinaries.push('wc-messages.jar');
		}
		if (!bins.WinBinaries.includes('cv-ac-messages.jar') && bins.WinBinaries.some(e => (e.startsWith('cv-ac-') && e.endsWith('.jar')))){
			bins.WinBinaries.push('cv-ac-messages.jar');
			bins.UnixBinaries.push('cv-ac-messages.jar');
		}

		if (buildTypeOfficial){
			// get binaries from UC to make sure we are building same binaries
			// this fixes the case where official commit might have less files (and hence less binaries) than friendly
			// because the same files were already committed by another GMR
			let formInfo = await app.getDetailsForFormSync();
			formInfo.BinaryInfo.WinBinaries.forEach(element => {
				if (!bins.WinBinaries.includes(element)){
					// binary not present
					utils.log("UC form Windows binary not present, adding it.");
					bins.WinBinaries.push(element);
				}
			});
			formInfo.BinaryInfo.UnixBinaries.forEach(element => {
				if (!bins.UnixBinaries.includes(element)){
					// binary not present
					utils.log("UC form Unix binary not present, adding it.");
					bins.UnixBinaries.push(element);
				}
			});
			if (formInfo.BinaryInfo.WinBinaries.length !== bins.WinBinaries.length){
				utils.log("Current build has more windows binaries than in UC form. This should not happen.");
			}
			if (formInfo.BinaryInfo.UnixBinaries.length !== bins.UnixBinaries.length){
				utils.log("Current build has more unix binaries than in UC form. This should not happen.");
			}
		}

		res = JSON.stringify(bins);
		utils.logToFile(`${distDir}/binaries.json`, res);
		utils.log("Binaries logged in: " + path.resolve(`${distDir}/binaries.json`));
		return bins;
	},
	logBinariesRemoteLookup: (changedFiles, successCb, errCb) => {
		/*
		 * Determine binaries from sources list using marvel's binary finder,
		 * then process/log them via logBinariesAfterLookup.
		 */
		const binReq = {
			version: env.version,
			sources: changedFiles
		};
		utils.log("Running logBinariesRemoteLookup: " + JSON.stringify(binReq));

		req.post({
			headers: {
				'content-type': 'application/json'
			},
			url: 'http://marvel.gp.cv.commvault.com/binfinder/find.do',
			body: JSON.stringify(binReq)
		}).then( async function (res) {
			app.logBinariesAfterLookup(res);
			successCb(res);
		}).catch(e => {
			utils.log('Binaries could not be fetched: ' + e, true);
			errCb(e);
		});
	},
	lookupBinariesLocal: (changedFilesFile, binaryFinderOutputFile) => {
		/*
		 * Determine binaries from the sources list using a local binary finder utility.
		 */
		try {
			let opts = {
				env:{}
			};
			// Pass only env vars listed in envVarsToPassToBinaryFinder to the external script:
			envVarsToPassToBinaryFinder.forEach(envName => opts.env[envName] = env[envName]);

			let binaryFinderCommand = null;
			if (env.binaryFinderCommand) {
				binaryFinderCommand = env.binaryFinderCommand;
				utils.log("Using env binary finder command: " + binaryFinderCommand);
			}
			else {
				binaryFinderCommand = "./getBinaries.sh";
				utils.log("Using default binary finder command: " + binaryFinderCommand);
			}

			if (env.binaryFinderFolder) {
				utils.log("Local binary finder utility folder: " + env.binaryFinderFolder);
				opts.cwd = env.binaryFinderFolder;
			}
			utils.log("Local binary finder utility command: " + binaryFinderCommand);
			utils.log("Local binary finder source changes input file: " + changedFilesFile);

			// Params passed to the local binary finder script:
			// 1) Path to the file containing the list of changed sources (1 source per line)
			// 2) Path to the project folder (e.g. in the case of the web project, it will be
			//    the web folder itself, under which you will find AdminConsole and vaultcxWeb)
			let localBinFinderResult = utils.execCommandNative(binaryFinderCommand + ' '
					+ changedFilesFile + ' ' + path.resolve('.') + ' ' + binaryFinderOutputFile,
					opts);

			// utils.log("Local binfinder result: " + localBinFinderResult);
			return localBinFinderResult;
		}
		catch (e) {
			utils.log('Error: Local binary finder lookup failed: ' + e);
			return null;
		}
	},
	logBinaries: async function(changedFiles, successCb, errCb) {
		/*
		 * Determine binaries from sources list, then process/log them via
		 * logBinariesAfterLookup.
		 */
		if (`${env.isBatchBuild}` === "true"){
			utils.log("No binary finder lookup required because this is a batch build");
			// no need to call bin finder
			// make sure to call successCb and errorCb
			let bins = {};
			bins.WinBinaries = env.batchBins.split(',');
			let res = JSON.stringify(bins);
			utils.logToFile(`${distDir}/binaries.json`, res);
			utils.log("Binaries logged in: " + path.resolve(`${distDir}/binaries.json`));
			successCb(res);
			return;
		}

		utils.log("Performing lookup using local binary finder");
		/*
		 * !!! Consider refactoring so this fn receives a path to a file with
		 * the sources list, since we have to pass one to lookupBinariesLocal.
		 * One probably already exists (in all cases?) in
		 * `${distDir}/changes.txt` or `jobDetails/changedFiles.txt`. For now,
		 * just saving the list to a temp file and passing that.
		 */
		let localBinaryFinderResult = null;
		try {
			let changedFilesFile = path.resolve(`${distDir}/temp-changed-files.txt`);
			let binaryFinderOutputFile = path.resolve(`${distDir}/temp-get-binaries-output.txt`);
			try {
				fs.unlinkSync(binaryFinderOutputFile); // just in case we run this twice and the second time fails
			} catch {
				// File probably doesn't exist
			}

			utils.logToFile(changedFilesFile, changedFiles.join(NL));
			utils.log("changedFiles saved to temp file for local binary finder lookup: " + changedFilesFile);
			let clresponse = app.lookupBinariesLocal(changedFilesFile, binaryFinderOutputFile);
			if (clresponse) {
				utils.log("return value from local binary finder lookup (may be response code or log data): " + clresponse);
			}
			localBinaryFinderResult = fs.readFileSync(binaryFinderOutputFile);
			if (localBinaryFinderResult == null) {
				throw "local binary finder returned no results";
			}
		}
		catch(err) {
			console.log("Warning: local binary finder lookup failed, falling back to remote lookup. Error: " + err);
		}
		if (localBinaryFinderResult != null) {
			utils.log("Unconverted binary finder response: " + localBinaryFinderResult);
			let convertedResponse = await app.logBinariesAfterLookup(localBinaryFinderResult);
			utils.log("Converted binary finder response: " + JSON.stringify(convertedResponse));
			successCb(JSON.stringify(convertedResponse));
		} else {
			// Local lookup failed, fall back to old marvel binary finder lookup
			/*
			 * !!!! when the local binary finder is tested and stable we can
			 * remove this fallback, as well as the logBinariesRemoteLookup
			 * fn. Instead, just call errCb here,
			 */
			return app.logBinariesRemoteLookup(changedFiles, successCb, errCb);
		}
	},
	createUCFormData: (mergeData, changedFiles, project, binaries, mergeId, projectId) => {
		binaries = JSON.parse(binaries);

		// temp code to skip unix builds because UC test system lack of support - todo remove temp code
		// binaries.WinBinaries = binaries.WinBinaries.filter(item => (item !== 'cv-ac-cloudservices.see' && item !== 'cv-ac-cloudservices.jar' ))
		// binaries.UnixBinaries = [];
		// end temp code
		let formData = {
			BuildID: env.buildId,	// this depends on SP
			FormType: 'GitLabForm',
			Author: mergeData.formAuthor,
			SourceInfo: {
				WinFiles: changedFiles,
				UnixFiles: []
			},
			// project: project.path,
			BinaryInfo: binaries,
			Summary: mergeData.title,
			projectname: '',	// hard coded for now.. todo
			GitLabFormProperties: {
				GitMergeRequestID: mergeId,
				GitProjectID: projectId,
				GitMiscInfo: ''
			},
			MR: '254534',
			FormResource: {
				DevOwner: '',
				// TestOwner: '',
				// ListDevChoiceCodeReviewers: []
			}
			// RebuildComment: "",
			// FormStateName: "",
			// FormSubStateName: "",
			// "lstCustomers": [
			// 	{
			// 	  "CustomerName": "sample string 1",
			// 	  "CustomerTR": "sample string 2"
			// 	},
			// 	{
			// 	  "CustomerName": "sample string 1",
			// 	  "CustomerTR": "sample string 2"
			// 	}
			//   ],
			// "BugFixInfo": {
			// 	"BugSymptomsList": [
			// 	  "sample string 1",
			// 	  "sample string 2"
			// 	],
			// 	"BugCauseList": [
			// 	  "sample string 1",
			// 	  "sample string 2"
			// 	],
			// 	"BugFixList": [
			// 	  "sample string 1",
			// 	  "sample string 2"
			// 	],
			// 	"AdditionalIntructionsList": [
			// 	  "sample string 1",
			// 	  "sample string 2"
			// 	],
			// 	"ProjectName": "sample string 1"
			//   },

		};
		utils.log("Data for UC: " + JSON.stringify(formData));
		// formData.AccessToken = env.ucToken;	// adding after println
		// write to a file (to save multiple API calls) to be sent after build
		utils.logToFile(`${distDir}/formData.json`, JSON.stringify(formData));
	},
	createUpdateUCForm: async function () {
		// check if the build was successful or not
		// if failed, then do nothing for friendly
		// for official set the failed status in UC form
		let allJobs = await app.getPipelineJobs();
		let buildJobs = allJobs.filter(e => e.stage == "build");

		// if (fs.existsSync(ac_job_details_path) && fs.existsSync(wc_job_details_path)){	// find better way to determine this
		if (buildJobs.filter(e => e.status == "failed").length == 0) {
			// build succeeded
			app.createUCForm(buildJobs);
		} else {
			// at least 1 build failed

			if (!buildTypeOfficial){
				// Mark form as created when friendly failed
				let formInfo = null;
				try {
					formInfo = await app.getDetailsForFormSync();
				} catch (error) {
					utils.log("Friendly failure and UC form not found. " + error);
					return;
				}

				var opts = {
					// todo get actual user here
					username: env.ucApiUser,
					password: env.ucApiPass,
					url: ucResetToCreatedState +
							"?BuildID=" + formInfo.BuildID +
							"&FormID=" + formInfo.FormID +
							"&Comment=Build failed" +
							"&AccessToken=" + env.ucToken
				};
				try {
					let ucResp = await ntlmPromise.put(opts, null);
					utils.log("reponse ucResp: " + JSON.stringify(ucResp));
				} catch (error) {
					utils.log("Error while updated UC form in case of friendly build failure: "  + error, true);
					throw Error ("Error updating UC form in case of friendly build failed.");
				}
				utils.log("Updated UC form in case of friendly failure.");
				return;
			}
			// call status change api and set gitmisc info as failed official and new MR id

			// get existing form details
			let formInfo = await app.getDetailsForFormSync();
			function arrayUnique(array) {
				var a = array.concat();
				for(var i=0; i<a.length; ++i) {
					for(var j=i+1; j<a.length; ++j) {
						if(a[i] === a[j])
							a.splice(j--, 1);
					}
				}
				return a;
			}
			console.log("##### formInfo.BinaryInfo.WinBinaries: " + JSON.stringify(formInfo.BinaryInfo.WinBinaries));
			let binariyList = arrayUnique(formInfo.BinaryInfo.WinBinaries.concat(formInfo.BinaryInfo.UnixBinaries));

			// create new GMR
			let oldMrInfo = await app.getDetailsForMrSync();

			let newMrData = {
				id: oldMrInfo.source_project_id,
				title: "Corrective GMR for: " + oldMrInfo.title,
				description: "Corrective GMR for official build failure."
							+ "\n\nHow to fix: http://devserver.commvault.com:81/adminconsoledocs/resolving-official-build-failure/"
							+ "\n\nUpdate Form id: " + formInfo.FormID
							+ " \n\nPrevious MergeRequest: !" + oldMrInfo.iid
							+ " \n\nOriginal description: " + oldMrInfo.description,
				target_branch: oldMrInfo.target_branch,
				// GMR can be created with non existing source branch
				// creating new GMR on a non-existent source branch so the pipeline does not auto-start
				source_branch: oldMrInfo.source_branch + "-" + formInfo.FormID + "-" + Date.now(),
				target_project_id: oldMrInfo.target_project_id,
				squash: true,
				labels: binariyList.join()
				};

			let newMrInfo = null;
			try {
				newMrInfo = await req.post({
											url: utils.api(`${base}/projects/${oldMrInfo.source_project_id}/merge_requests?sudo=${oldMrInfo.author.id}`).url,
											form: newMrData,
											headers: {'Private-token': env.glToken}	// TODO: check token
									});
				utils.log("new GMR response: " + newMrInfo);
			} catch (error) {
				utils.log("Error while creating new GMR: "  + error, true);
				throw Error ("Error while creating new GMR.");
			}

			newMrInfo = JSON.parse(newMrInfo);
			// add new GMR number to old GMR desc
			let updatedOldMrInfo = {}
			updatedOldMrInfo.id = oldMrInfo.project_id;
			updatedOldMrInfo.merge_request_iid = oldMrInfo.iid;
			updatedOldMrInfo.description = "New corrective merge-request !" + newMrInfo.iid + " is created for this change because official build failed." +
											"\n\n" + oldMrInfo.description;
			let oldMrUpdatedResp = await req.put({
					url: utils.api(`${base}/projects/${oldMrInfo.project_id}/merge_requests/${oldMrInfo.iid}`).url,
					form: updatedOldMrInfo,
					headers: {'Private-token': env.glToken}	// TODO: check token
			});
			utils.log("update old GMR response: " + oldMrUpdatedResp);

			// send new MR info to update center
			let newMiscInfo = {};
			newMiscInfo.oldMr = oldMrInfo.iid + "";
			let ucData = {};
			ucData.BuildID = formInfo.BuildID;
			ucData.FormID = formInfo.FormID;
			ucData.GitLabFormProperties = {};
			ucData.GitLabFormProperties.GitMergeRequestID = "" + newMrInfo.iid;
			ucData.GitLabFormProperties.GitProjectID = formInfo.GitLabFormProperties.GitProjectID;
			ucData.GitLabFormProperties.GitMiscInfo = JSON.stringify(newMiscInfo);
			utils.log("data to be posted for UC status change: " + JSON.stringify(ucData));
			ucData.AccessToken = env.ucToken;

			let ucResp = null;
			var opts = {
				// todo get actual user here
				username: env.ucApiUser,
				password: env.ucApiPass,
				url: utils.api(ucModifyGitlabInfoAPI).url
			};
			try {
				ucResp = await ntlmPromise.put(opts, ucData);
				utils.log("reponse ucResp: " + JSON.stringify(ucResp));
			} catch (error) {
				utils.log("Error while posting form details: "  + error, true);
				throw Error ("Error posting changed data for form details.");
			}
		}
	},
	createUCForm: (buildJobs) => {
		let data = JSON.parse(fs.readFileSync(`jobDetails/formData.json`, 'utf8'));

		// check if we need to create a new form or modify existing
		let formInfoApi = ucFormInfo;

		// need MR in case if commit/official build
		if (buildTypeOfficial){
			let mrId = data.GitLabFormProperties.GitMergeRequestID;
			formInfoApi = ucCommitFormInfo + mrId;
		}
		console.log("calling api: " + formInfoApi);

		var opts = {
			username: env.ucApiUser,
			password: env.ucApiPass,
			url: formInfoApi
		};

		ntlm.get(opts, null, async function(err, response) {
			if (err){
				utils.log('Error: ' + err, true);
				process.exit(1);
			}
			if (response.statusCode !== 404 && response.statusCode !== 200){
				utils.log('Error response.statusCode: ' + response.statusCode, true);
				utils.log('Error response: ' + JSON.stringify(response), true);
				process.exit(1);
			}

			// prepare data
			// helper function to store job details in json obj
			function storeJobDataToMiscObj(miscObj){
				let buildJobIds = buildJobs.map(e => e.id + "");
				// var acJson = JSON.parse(fs.readFileSync(ac_job_details_path, 'utf8').trim());
				// var wcJson = JSON.parse(fs.readFileSync(wc_job_details_path, 'utf8').trim());
				if (buildTypeOfficial){
					// _.set(miscObj, 'officialBuild.acJobId', acJson.jobid);
					_.set(miscObj, 'officialBuild.projectId', env.commitProjectId);
					// _.set(miscObj, 'officialBuild.wcJobId', wcJson.jobid);
					_.set(miscObj, 'officialBuild.completedPipelineId', process.env.CI_PIPELINE_ID);
					_.set(miscObj, 'officialBuild.buildJobIds', buildJobIds)
				} else {
					_.set(miscObj, 'friendlyBuild.completedPipelineId', process.env.CI_PIPELINE_ID);
					// _.set(miscObj, 'friendlyBuild.acJobId', acJson.jobid);
					_.set(miscObj, 'friendlyBuild.projectId', env.projectId);
					// _.set(miscObj, 'friendlyBuild.wcJobId', wcJson.jobid);
					_.set(miscObj, 'friendlyBuild.buildJobIds', buildJobIds)

					//refreshable property is used by updatecenter. When form is rebuilt, UC starts new pipeline for the merge request.
					//Refreshable property is set to true in pipeline if there have been no new commits since last form build
					//refreshable is true, form will not stay in dev integration but move forward as there havent been any new commits
					let refreshable = false;
					if(miscObj.friendlyBuild && miscObj.friendlyBuild.commitId && miscObj.friendlyBuild.commitId === process.env.CI_COMMIT_SHA) {
						refreshable = true;
					}
					_.set(miscObj, 'friendlyBuild.refreshable', refreshable.toString());
					_.set(miscObj, 'friendlyBuild.commitId', process.env.CI_COMMIT_SHA);
				}
				return miscObj;
			}

			if (response.statusCode === 404) {
				// no existing form
				if (buildTypeOfficial){
					utils.log('No update form for this merged/official build: ' + JSON.stringify(response), true);
					process.exit(1);
				}
				let miscObj = {};
				miscObj = storeJobDataToMiscObj(miscObj);
				data.GitLabFormProperties.GitMiscInfo = JSON.stringify(miscObj);	// always store as string

				utils.log('no existing form: ' + (err||JSON.stringify(response)), true);
				utils.logToFile(`${distDir}/formData.json`, JSON.stringify(data));
				utils.log("sending data: " + JSON.stringify(data));
				opts.url = utils.api(ucFormCreateAPI).url;
				data.AccessToken = env.ucToken;	// add token at last so not to print anywhere
				ntlm.post(opts, data, async function(err, response) {
					if (err || response.body.error || response.statusCode !== 200) {
						utils.log('Failed to create update form: ' + err, true);
						utils.log('Failed to create update form: ' + JSON.stringify(response), true);
						utils.log('####################################################################');
						utils.log('Failed to create update form: Error: ' + JSON.stringify(response.body.Error) + ' Message: ' + JSON.stringify(response.body.Message), true);
						utils.log('####################################################################');
						process.exit(1);
					}
					utils.log("Good to go: " + JSON.stringify(response));
					// add form id to GMR
					let mrInfo = await app.getDetailsForMrSync();
					let newMrData = {};
					newMrData.id = mrInfo.project_id;
					newMrData.merge_request_iid = mrInfo.iid;
					newMrData.description = "UpdateCenter Form: [" +
											response.body.FormID +
											`](${ucBase}/Form.aspx?BuildID=` +
											response.body.BuildID  +
											'&FormID=' +
											response.body.FormID  +
											") \n\n" + mrInfo.description
					let newMrInfo = await req.put({
											url: utils.api(`${base}/projects/${mrInfo.project_id}/merge_requests/${mrInfo.iid}`).url,
											form: newMrData,
											headers: {'Private-token': env.glToken}	// TODO: check token
									});
					utils.log("update GMR response: " + newMrInfo);
				});
			} else {
				utils.log('Existing form details: ' + response.body);

				var miscObj = JSON.parse(JSON.parse(response.body).GitLabFormProperties.GitMiscInfo);	// parsing 2 times cause we save misinfo as string
				if (miscObj === null){
					// in case of auto forward form value can be null
					miscObj = {};
				}
				miscObj = storeJobDataToMiscObj(miscObj);
				// data.GitLabFormProperties.GitMiscInfo = JSON.stringify(miscObj);	// always store as string
				data.GitLabFormProperties.GitMiscInfo = JSON.stringify(miscObj);	// always store as string

				var existingFormId = "" + JSON.parse(response.body).FormID;

				// Store existing form id in a file to be used by next jobs (auto-fp))
				utils.log("Storing existingFormId to a file: " + existingFormId);
				fs.writeFileSync(uc_formId_txt, existingFormId);

				if (buildTypeOfficial){
					// official build done.. send UC success status
					data.FormID = existingFormId;
					// data.ApprovalStatus = "Success";	// not needed anymore
					// rest info is still present in data but not used by UC

					utils.logToFile(`${distDir}/formData.json`, JSON.stringify(data));
					utils.log("sending data: " + JSON.stringify(data));
					opts.url = utils.api(ucModifyGitlabInfoAPI).url;
					data.AccessToken = env.ucToken;
					ntlm.put(opts, data, function(err, response) {
						if (err || response.body.error || response.statusCode !== 200) {
							utils.log('Failed to create update form: ' + err, true);
							utils.log('Failed to create update form: ' + JSON.stringify(response), true);
							utils.log('####################################################################');
							utils.log('Failed to create update form: Error: ' + JSON.stringify(response.body.Error) + ' Message: ' + JSON.stringify(response.body.Message), true);
							utils.log('####################################################################');
							process.exit(1);
						}
						utils.log("Good to go: " + JSON.stringify(response));
					});

				} else {
					// modify existing friendly form
					if (miscObj.hasOwnProperty('oldMr') && miscObj.oldMr !== ""){
						// dont modify if its official failed case
						// utils.log("Not modifying update form as official build failed earlier. Old MergeRequest: " + miscObj.oldMr);
						utils.log("Check binaries and files and then continue modifying update form as official build failed earlier. Old MergeRequest: " + miscObj.oldMr);
						// binaries should be same
						// files should be same or more

						// todo- check if its success after a failed official, then binaries should be same
						let formJson = JSON.parse(response.body);
						// compare binaries array
						if (formJson.BinaryInfo.WinBinaries.length == data.BinaryInfo.WinBinaries.length &&
							!formJson.BinaryInfo.WinBinaries.some( (v) =>  data.BinaryInfo.WinBinaries.indexOf(v) < 0) &&
							formJson.BinaryInfo.UnixBinaries.length == data.BinaryInfo.UnixBinaries.length &&
							!formJson.BinaryInfo.UnixBinaries.some( (v) =>  data.BinaryInfo.UnixBinaries.indexOf(v) < 0) ) {
								// same binaries.. let it proceed
								utils.log('Same binaries present.. proceeding.');
						} else {
							// binaries are diff fail build
							utils.log('Official failed case. Binaries not same as update form.', true);
							process.exit(1);
						}
						if (formJson.SourceInfo.WinFiles.length <= data.SourceInfo.WinFiles.length &&
							!formJson.SourceInfo.WinFiles.some( (v) =>  data.SourceInfo.WinFiles.indexOf(v) < 0) ) {
								// same or more files present.. proceeding
								utils.log('Same or more files present.. proceeding.');
							} else {
							// binaries are diff fail build
							utils.log('Official failed case. Files not same or more as update form.', true);
							process.exit(1);
						}
					}
					data.FormID = existingFormId;
					utils.logToFile(`${distDir}/formData.json`, JSON.stringify(data));
					utils.log("sending data: " + JSON.stringify(data));
					opts.url = utils.api(ucFormModifyAPI).url;
					data.AccessToken = env.ucToken;
					ntlm.post(opts, data, function(err, response) {
						if (err || response.body.error ||  response.statusCode !== 200) {
							utils.log('Failed to create update form: ' + err, true);
							utils.log('Failed to create update form: ' + JSON.stringify(response), true);
							utils.log('####################################################################');
							utils.log('Failed to create update form: Error: ' + JSON.stringify(response.body.Error) + ' Message: ' + JSON.stringify(response.body.Message), true);
						    utils.log('####################################################################');
							process.exit(1);
						}
						utils.log("Good to go: " + JSON.stringify(response.body));
					});

					// add form id to GMR
					let mrInfo = await app.getDetailsForMrSync();
					let ucUrl =  `${ucBase}/Form.aspx?BuildID=` +
									JSON.parse(response.body).BuildID  +
									'&FormID=' +
									JSON.parse(response.body).FormID;
					if (!mrInfo.description.includes(ucUrl)){
						// UC url not already present
						let newMrData = {};
						newMrData.id = mrInfo.project_id;
						newMrData.merge_request_iid = mrInfo.iid;
						newMrData.description = "UpdateCenter Form: [" +
												JSON.parse(response.body).FormID +
												"](" + ucUrl + ") \n\n" +
												mrInfo.description;
						let newMrInfo = await req.put({
												url: utils.api(`${base}/projects/${mrInfo.project_id}/merge_requests/${mrInfo.iid}`).url,
												form: newMrData,
												headers: {'Private-token': env.glToken}	// TODO: check token
										});
						utils.log("update GMR response: " + newMrInfo);
					} else {
						utils.log("UC url already present");
					}
				}
			}
		});
	},
	getDetailsForFormSync: async function (){
		utils.log("Running getDetailsForFormSync");
		// todo add caching

		// check if we need to create a new form or modify existing
		let formInfoApi = ucFormInfo;

		// need MR in case if commit/official build
		if (buildTypeOfficial){
			let mrId = await app.getMergeIdForCommitSync(env.commitId);
			formInfoApi = ucCommitFormInfo + mrId;
		}
		utils.log("calling api: " + formInfoApi);

		var opts = {
			// todo get actual user here
			username: env.ucApiUser,
			password: env.ucApiPass,
			url: formInfoApi
		};

		let jsonData = {};
		let formData = null;
		try {
			formData = await ntlmPromise.get(opts, jsonData);

		} catch (error) {
			utils.log("Error while getting form details: "  + error, true);
			throw Error ("Error getting formData for form details.");
		}
		utils.log("reponse formData: " + JSON.stringify(formData));
		// 200 response
		return formData;
	},
	getDetailsForMrSync: async function (){
		utils.log("Running getDetailsForMrSync");
		// get mr number
		let mrid = null;
		if (env.mergeId){
			mrid = env.mergeId;
		} else {
			mrid = await app.getMergeIdForCommitSync(env.commitId);
		}

		try {
			let api = mrDetailsApi + mrid;
			let res = await req(utils.api(api));

			utils.log("getDetailsForMrSync response: " + res);
			res = JSON.parse(res);

			// get and store project name to a file to be used for auto forward-port
			if (buildTypeOfficial){
				let projRes = await req(utils.api(`${base}/projects/` + res.source_project_id));
				utils.log("Project details response: " + projRes);
				fs.writeFileSync(gitSourceProject_path_with_namespace_txt, JSON.parse(projRes).path_with_namespace);
			}

			return res;
		} catch (e) {
			utils.log("Failed to get MR details for labels: " + e, true);
			process.exit(1);
			throw new Error("getDetailsForMrSync failed to get MR details for labels");
		}
	},
	getMergeIdForCommitSync: async function (commitSHA){
		// remove the async copy of this function
		utils.log("Running getMergeIdForCommitSync");
		// TODO: caching
		try {
			// let commitGetMrAPI = `${base}/projects/9/repository/commits/12d78b770c46225f563fc28278c618389de25898`;
			let res = await req(utils.api(commitGetMrAPI));

			utils.log("getMergeIdForCommitSync response: " + res);
			res = JSON.parse(res);
			var commitMsg = res.message;
			const fixedString = `See merge request ${process.env.CV_OFFICIAL_PROJECT}!`;
			var mrId = commitMsg.substring(commitMsg.indexOf(fixedString) + fixedString.length);
			return mrId;
		} catch (e) {
			utils.log("Failed to get MR id: " + e, true);
			throw new Error("getMergeIdForCommitSync failed to get MR id");
		}
	},
	getMergeChanges: async function (){
		utils.log("Running getMergeChanges");
		// TODO: caching
		try {
			let res = await req(utils.api(changesAPI));

			utils.log("getMergeChanges response: " + res);
			res = JSON.parse(res);
			return res;
		} catch (e) {
			utils.log("Failed to get MR changes: " + e, true);
			throw new Error("getMergeChanges failed to get MR changes");
		}
	},
	getCommitChangesSync: async function (){
		utils.log("Running getCommitChangesSync");
		try {
			let res = await req(utils.api(commitChangesAPI));

			utils.log("getCommitChangesSync response: " + res);
			res = JSON.parse(res);
			return res;
		} catch (e) {
			utils.log("Failed to get commit changes: " + e, true);
			throw new Error("getCommitChangesSync failed to get commit changes");
		}
	},
	getDependenciesPipelineInfoSync: async function (){
		utils.log("Running getDependenciesPipelineInfoSync");
		try {
			let res = await req(utils.api(getLatestDependenciesPipelineApi));
			// https://git.commvault.com/api/v4/projects/236/pipelines?per_page=1&page=1
			utils.log("getDependenciesPipelineInfoSync response: " + res);
			res = JSON.parse(res);
			return res;
		} catch (e) {
			utils.log("Failed to get latest pipeline id: " + e, true);
			throw new Error("getDependenciesPipelineInfoSync failed to get latest pipeline id.");
		}
	},
	getDependenciesPipelineDetailSync: async function (pipeId){
		utils.log("Running getDependenciesPipelineDetailSync");
		try {
			let res = await req(utils.api(getLatestDependenciesPipelineDetailsApi + pipeId));
			// https://git.commvault.com/api/v4/projects/236/pipelines?per_page=1&page=1
			utils.log("getDependenciesPipelineDetailSync response: " + res);
			res = JSON.parse(res);
			return res;
		} catch (e) {
			utils.log("Failed to get latest pipeline details: " + e, true);
			throw new Error("getDependenciesPipelineDetailSync failed to get latest pipeline details");
		}
	},
	startDependenciesPipeline: async function (){
		utils.log("Running startDependenciesPipeline");
		try {
			// todo check support for other branches
			let res = await req.post({
								url: utils.api(startDependenciesPipelineApi).url,
								headers: {'Private-token': env.glToken}
							});
			utils.log("startDependenciesPipeline response: " + res);
			res = JSON.parse(res);
			return res;
		} catch (e) {
			utils.log("Failed to start pipeline: " + e, true);
			throw new Error("startDependenciesPipeline failed to start pipeline.");
		}
	},
	getPipelineJobs: async function (){
		utils.log("Running getPipelineJobs");
		try {
			let projId;
			let pipeId = process.env.CI_PIPELINE_ID;
			if (buildTypeOfficial){
				projId = env.commitProjectId;
			} else {
				projId = env.projectId;
			}
			let res = await req(utils.api(getPipelineJobsApi(projId, pipeId)));

			utils.log("getPipelineJobs response: " + res);
			res = JSON.parse(res);
			return res;
		} catch (e) {
			utils.log("Failed to getPipelineJobs: " + e, true);
			let userFriendlyErrInfo = {
				errMsg : `getPipelineJobs API failed.`,
				explanation : `getPipelineJobs API failed, probably due to network issue.`,
				adminResponse : `If this is friendly pipeline then try running a new pipeline, otherwise contact git-admins.`
			};
			logUtils.logUserFriendlyError(userFriendlyErrInfo);
			process.exit(1);
			throw Error("Failed to getPipelineJobs");
		}
	},
	getMergedRef: async function (){
		utils.log("Running getMergedRef");
		try {
			let res = await req(utils.api(getMergedRefApi));

			utils.log("getMergedRef response: " + res);
			res = JSON.parse(res);
			return res.commit_id;
		} catch (e) {
			utils.log("Failed to get MR ref: " + e, true);
			let errMsg = "getMergedRef failed to get MR ref, please contact git-admins";
			if (e.statusCode === 400){
				errMsg = "Unable to merge source branch to official branch. Please resolve merge conflicts and push changes to run build again."
			}
			utils.log(errMsg, true);
			let userFriendlyErrInfo = {
				errMsg : `Merge request is not mergeable.`,
				explanation : `Destination branch has moved. Changes in this merge request are causing merge conflicts.`,
				adminResponse : `Merge conflicts need to be resolved manually. For this, pull latest from upstream, merging any conflicts, and push a new commit. This will initiate a new pipeline for your git merge request.`
			};
			logUtils.logUserFriendlyError(userFriendlyErrInfo);

			// fix this with proper error handling of async await
			process.exit(1);
		}
	},
	storeAutoFpResult: async function (result){
		utils.log("Running storeAutoFpResult");
		let formInfo = await app.getDetailsForFormSync();

		// send new MR info to update center
		let miscInfoObj = JSON.parse(formInfo.GitLabFormProperties.GitMiscInfo);
		if (miscInfoObj == null) {
			miscInfoObj = {};
		}
		miscInfoObj.AutoFpStatus = result;
		formInfo.GitLabFormProperties.GitMiscInfo = JSON.stringify(miscInfoObj);
		utils.log("data to be posted for UC storeAutoFpResult: " + JSON.stringify(formInfo));
		formInfo.AccessToken = env.ucToken;

		let ucResp = null;
		var opts = {
			username: env.ucApiUser,
			password: env.ucApiPass,
			url: utils.api(ucModifyGitlabInfoAPI).url
		};
		try {
			ucResp = await ntlmPromise.put(opts, formInfo);
			utils.log("reponse storeAutoFpResult ucResp: " + JSON.stringify(ucResp));
		} catch (error) {
			utils.log("Error while posting storeAutoFpResult: "  + error, true);
			throw Error ("Error posting changed data for storeAutoFpResult.");
		}
	},

	//This method handles forward port for hotfix GMRs
	handleForwardPort: async function (projectToCO, formID){

		function forwardPortBranch(fpBranch) {
			try{
				utils.log("Processing forward port for branch : " + fpBranch.masterBranchName );

				//sample forward port branch name auto-fp-v11B80SP18-945-v11B80SP19
				let checkOutResult = utils.execCommand("git checkout -b " + fpBranch.fpBranchName + " upstream/" + fpBranch.masterBranchName);
				if (checkOutResult && checkOutResult.code){
					utils.log("ERROR: checkout failed", true);
					return {status : 1, failureReason : "Checkout failed"};
				}
				utils.log("Checkout success");

				let ciResult = utils.execCommand("npm ci --prefer-offline --registry http://npm.commvault.com:4873 ");
				if (ciResult && ciResult.code){
					utils.log("ERROR: npm ci failed", true);
					return {status : 1, failureReason : "npm ci failed"};
				}
				utils.log("npm ci success");

				let cherryPickResult = utils.execCommand("git cherry-pick " + env.commitId +" -m 1 -x ");
				//For testing
				//let cherryPickResult = utils.execCommand("git cherry-pick --keep-redundant-commits d8c9311b -m 1 -x ");
				if (cherryPickResult && cherryPickResult.code) {
					utils.log("ERROR: git cherry-pick failed", true);
					return {status : 1, failureReason : "cherry-pick failed"};
				}
				utils.log("Cherry pick success");

				let pushOriginResult = utils.execCommand("git push origin");
				if (pushOriginResult && pushOriginResult.code) {
					utils.log("ERROR: git push origin failed", true);
					return {status : 1, failureReason : "push origin failed"};
				}
				utils.log("Forward-port branch push success");

				utils.log("Completed forward port for branch : " + fpBranch.masterBranchName );
				return {status : 0};
			}
			catch(error){
				utils.log("Exception : "  + error, true);
				return {status : 1, failureReason : "Exception occurred"};
			}

		}

		let fwdPortStatus = {
			status : 0,
			failureReason : "",
			branches : []
		};

		try {
			utils.log("Start cloning");
			let tempco = "tempco";
			utils.execCommand("time git clone --progress --verbose --no-single-branch --no-checkout --reference /app/refrepo/web.git https://gitlab-ci-token:" + env.glToken + "@" + env.serverHost + "/" + projectToCO +".git " + tempco);
			utils.execCommand("time mv " + tempco + "/.git .");
			utils.execCommand("git remote add upstream https://gitlab-ci-token:" + env.glToken + "@git.commvault.com/eng/ui/web.git");
			utils.execCommand("git fetch --all");
			utils.log("Cloning completed");
		} catch (error) {
			utils.log("Error occurred while cloning: "  + error, true);
			fwdPortStatus.status = 1; //failed or partially failed
			fwdPortStatus.failureReason = "Error occurred while cloning";
			await app.storeAutoFpResult(fwdPortStatus);
			utils.log("Cloning failed. Hence not proceeding to forward port");
			return;
		}

		//Determine required branches where the change should be forwardported
		//To DO - Get updatecenter api to get valid forward port branches, instead of below hardcoded logic
		//sample forward port branch name auto-fp-v11B80SP18-945-v11B80SP19
		let fpBranches=[{masterBranchName : "REL_11_0_0_BRANCH", fpBranchName : "auto-fp-" + env.buildName + "-" + formID + "-v11B80"}];
		if(env.commitRefName === "REL_11_0_0_B80_SP19_BRANCH"){
			fpBranches.push({masterBranchName : "REL_11_0_0_B80_SP20_BRANCH", fpBranchName : "auto-fp-" + env.buildName + "-" + formID + "-v11B80SP20"});
		}
		utils.log("Number of forward port branches : " + fpBranches.length);

		utils.execCommand("git config --global user.email " + env.gitlabUserEmail);
		utils.execCommand("git config --global user.name " + env.gitlabUserName);

		for(let i = 0; i < fpBranches.length; i++ ){
			if(i !== 0){
				//git reset as part of cleanup
				let gitResetResult = utils.execCommand("git reset --hard");
				if (gitResetResult && gitResetResult.code){
					utils.log("ERROR: git reset failed", true);
					fwdPortStatus.status = 1; //failed or partially failed
					fwdPortStatus.failureReason = "Git reset failed";
					await app.storeAutoFpResult(fwdPortStatus);
					utils.log("Cleanup failed. Hence not proceeding to forward port rest of the branches", true);
					return;
				}
			}

			let fwdPortBranchResult = forwardPortBranch(fpBranches[i]);
			if(fwdPortBranchResult.status !== 0){
				utils.log("ERROR: Forward port failed for branch " + fpBranches[i].masterBranchName, true);
				fwdPortStatus.status = 1; //failed or partially failed
			}
			fwdPortBranchResult.masterBranchName = fpBranches[i].masterBranchName;
			fwdPortStatus.branches.push(fwdPortBranchResult);
		}


		await app.storeAutoFpResult(fwdPortStatus);

		if(fwdPortStatus.status === 0)
			utils.log("Completed forward port for all required branches");
		else if	(fwdPortStatus.status === 1 && fwdPortStatus.branches.filter((b) => b.status === 0).length	> 0)
			utils.log("Partially completed forward port for required branches", true);
		else
			utils.log("Failed forward port for all branches", true);
	},
	initBuildExternalsource: async function(){
 		utils.log(`
 			BUILD_EXTERNAL_SOURCE ${process.env.BUILD_EXTERNAL_SOURCE} \n
			CI_SERVER_HOST ${process.env.CI_SERVER_HOST} \n
			CI_PROJECT_ID ${process.env.CI_PROJECT_ID} \n
			CI_PROJECT_PATH ${process.env.CI_PROJECT_PATH} \n
			CI_COMMIT_REF_NAME ${process.env.CI_COMMIT_REF_NAME} \n
			CI_COMMIT_SHA ${process.env.CI_COMMIT_SHA} \n
			UC_EXTERNAL_FORM_ID ${process.env.UC_EXTERNAL_FORM_ID} \n
			UC_EXTERNAL_BUILD_NO ${process.env.UC_EXTERNAL_BUILD_NO} \n
			UC_FORM_STATUS_OFFICIAL ${process.env.UC_FORM_STATUS_OFFICIAL} \n
			BINARIES_TO_BUILD ${process.env.BINARIES_TO_BUILD} \n
			EXTERNAL_SOURCE_LIST ${process.env.EXTERNAL_SOURCE_LIST}
 		`);

		let bins = {};
		bins.WinBinaries = env.batchBins.split(',');
		res = JSON.stringify(bins);
		utils.logToFile(`${distDir}/binaries.json`, res);
		utils.log("Binaries logged in: " + path.resolve(`${distDir}/binaries.json`));


	},
	downloadFriendlySource: async function(){
		utils.log(`Downloading external source code for update center build ${env.externalBuildId} and form ${env.externalFormId}`);

		let zipDownloadLoc = path.join(process.cwd(), `tempExternalSrcLocation`);
		fs.mkdirSync(zipDownloadLoc, {recursive: true});
		//mkdirp.sync(zipDownloadLoc, null);

		utils.log(`Calling download source update center api`);
		var opts = {
			username: env.ucApiUser,
			password: env.ucApiPass,
			url: `${ucDownloadSourceApi}?BuildID=${env.externalBuildId}&FormID=${env.externalFormId}`
		};
		//zipped source is sent in api response
		try{
			ntlmPromise.get(opts, {}, (response) => {
				utils.log(`Received API response`);
				if(response.statusCode === 404) {
					utils.log(`Api response : 404. Source for this form is not available. Nothing to download.`);
					return;
				}
				let zipFilePath = path.join(zipDownloadLoc, `source.zip`);
				const writableZipLoc = fs.createWriteStream(zipFilePath);

				utils.log(`Saving form source zip file`);
				let stream = response.pipe(writableZipLoc);
				stream.on(`finish`, () => {
					utils.log(`Source zip download completed`);
				});
			});
		}
		catch (error) {
			utils.log("Error while downloading external source for update center form: "  + error, true);
			throw Error ("Error while downloading external source for update center form");
		}
	},
	//Save pipelineid as attemptedPipelineId in gitmiscInfo if friendly build and if form exists
	updateNewPipelineInfo : async function () {
		if (buildTypeOfficial){
			logUtils.log(`Official build. No need to record pipelineInfo`);
			return;
		}

		logUtils.log(`New pipeline started`);

		let formInfo = await ucUtils.getFormDetails(env.projectId, env.mergeId);

		if(formInfo === null) {
			logUtils.log("Form not found. This appears to be first pipeline for the GMR");
			//cannot update gitmiscinfo form property as there is no form yet
			return;
		}

		let miscInfoObj = {};
		if(formInfo && formInfo.GitLabFormProperties && formInfo.GitLabFormProperties.GitMiscInfo){
			miscInfoObj = JSON.parse(formInfo.GitLabFormProperties.GitMiscInfo);
		}
		_.set(miscInfoObj, 'friendlyBuild.attemptedPipelineId', process.env.CI_PIPELINE_ID);
		_.set(formInfo, 'GitLabFormProperties.GitMiscInfo', JSON.stringify(miscInfoObj));

		await ucUtils.updateGitlabFormProperties(formInfo.FormID, formInfo.BuildID, formInfo.GitLabFormProperties);
	},
	getMergeIdForCommit: (commitSHA, successCb, errCb) => {
		utils.log("Running getMergeIdForCommit");
		req(utils.api(commitGetMrAPI)).then(res => {
			utils.log("getMergeIdForCommit result: " + res);
			successCb(JSON.parse(res));
		}).catch(e => {
			utils.log('getMergeIdForCommit could not be fetched: ' + e, true);
			errCb(e);
		});
	},
	logChangesInCommit: () => {
		utils.log("Running logChangesInCommit");
		req(utils.api(commitProjectAPI)).then(project => {
			let projectData = JSON.parse(project);
			req(utils.api(commitChangesAPI)).then(data => {
				let mergeData = JSON.parse(data);
				let changedFiles = "";
				if (mergeData.length < 99 ){
					// use API assuming all changes are present
					changedFiles = mergeData.map(p => p.new_path);
					utils.logToFile(`${distDir}/changes.txt`, changedFiles.join(NL));
					utils.log("Changes logged in file: " + path.resolve(`${distDir}/changes.txt`) + " for merge: " + JSON.stringify(mergeData));
				} else {
					// use jobDetails/changedFiles.txt if present
					let gitChange = fs.readFileSync(`jobDetails/changedFiles.txt`, 'utf8')
					if (gitChange === ''){
						throw Error ("Failed to get git changes");
					}
					gitChange = gitChange.trim().split("\n");
					utils.log("Changes from git diff: " + gitChange);
					changedFiles = gitChange;
				}

				app.logBinaries(changedFiles, (binaries) => {
					// get merge id after commit is done
					app.getMergeIdForCommit(env.commitId,
						(res) => {
							var commitMsg = res.message;
							const fixedString = `See merge request ${process.env.CV_OFFICIAL_PROJECT}!`;
							var mrId = commitMsg.substring(commitMsg.indexOf(fixedString) + fixedString.length);
							// mrId will be empty here if there string is not present
							// try to remove this call as its only needed to fetch author which is not required
							// set username
							mergeData.formAuthor = res.author_email;
							app.createUCFormData(mergeData, changedFiles, projectData, binaries, mrId, env.commitProjectId)
						},
						(e) => {
							//error in getting MR for this commit
							utils.log("Failed to get MR id for this commit: "  + env.commitId + " Error: " + e, true);
						});
				}, (e) => {
					utils.log("Failed to get binaries. Form will not be created. " + e, true);
					process.exit(1);
					throw Error ("Failed to get binaries. Form will not be created");
				});
			}).catch(e => {
				utils.log("Failed to get changes" + e, true);
				process.exit(1);
				throw Error ("Failed to get changes");
			});
		}).catch(e => {
			utils.log('Failed to load project details' + e, true);
			process.exit(1);
			throw Error ("Failed to load project details");
		});

	},
	logChangesInMerge: () => {
		utils.log("Running logChangesInMerge");
		req(utils.api(projectAPI)).then(project => {
			let projectData = JSON.parse(project);
			let projectName = projectData.path;	// not used anywhere right now
			req(utils.api(changesAPI)).then(data => {
				let mergeData = JSON.parse(data);
				let changedFiles = "";
				if (!mergeData.changes_count.endsWith('+')){
					changedFiles = mergeData["changes"].map(p => p.new_path);
					utils.logToFile(`${distDir}/changes.txt`, changedFiles.join(NL));
					utils.log("Changes logged in file: " + path.resolve(`${distDir}/changes.txt`) + " for merge: " + JSON.stringify(mergeData));
				} else {
					// too many changes for API
					utils.log("Using git diff. changes_count=" + mergeData.changes_count);
					// use jobDetails/changedFiles.txt if present
					let gitChange = fs.readFileSync(`jobDetails/changedFiles.txt`, 'utf8')
					if (gitChange === ''){
						throw Error ("Failed to get git changes");
					}
					gitChange = gitChange.trim().split("\n");
					utils.log("Changes from git diff: " + gitChange);
					changedFiles = gitChange;
				}

				app.logBinaries(changedFiles, (binaries) => {
					mergeData.formAuthor = mergeData.author.username;
					app.createUCFormData(mergeData, changedFiles, projectData, binaries, env.mergeId, env.projectId);
				}, (e) => {
					utils.log("Failed to get binaries. Form will not be created. " + e, true);
					process.exit(1);
					throw Error ("Failed to get binaries. Form will not be created");
				});
			}).catch(e => {
				utils.log("Failed to get changes" + e, true);
				process.exit(1);
				throw Error ("Failed to get changes");
			});
		}).catch(e => {
			utils.log('Failed to load project details' + e, true);
			process.exit(1);
			throw Error ("Failed to load project details");
		});
	},
	run: async (cmd) => {
		if (utils.isUndefinedOrEmpty(env.glToken) || utils.isUndefinedOrEmpty(env.ucToken)){
			console.log('Environment not set: Token');
			process.exit(1);
		}
		if (utils.isUndefinedOrEmpty(env.projectId) && utils.isUndefinedOrEmpty(env.commitProjectId)) {
			console.log("Environment not set: projectId, commitProjectId");
			process.exit(1);
		}
		console.log("Is MergeID available : ", !buildTypeOfficial);

		app.init();
		if (cmd === "checkDependencyUpdateRequired"){
			// only called if file jobDetails/dependenciesUpdateRequired is present
			try {
				if (fs.existsSync("jobDetails/dependenciesUpdateRequired")){
					let pipeInfo = await app.getDependenciesPipelineInfoSync();
					if (pipeInfo[0].status === "success" ){
						let pipeDetail = await app.getDependenciesPipelineDetailSync(pipeInfo[0].id);
						let timeDiffMins = Math.abs((Date.now() - new Date(pipeDetail.finished_at))/60000);
						utils.log("Time diff (in minutes) since last successful pipeline: " + timeDiffMins);
						if (timeDiffMins > 10){
							// needs new pipeline
							app.startDependenciesPipeline();
						} else {
							utils.log("Dependencies image update is not done. Last job finished time less than 10 mins.");
						}
					} else {
						utils.log("Dependencies image update is not done. Last status is not succuess.");
					}
				} else {
					utils.log("Dependencies image update is not required.");
				}
			} catch (error){
				// ignore failure
				utils.log("Ignore failure. Error while updating dependencies: " + error);
			}
		} else if (cmd === "checkGitDiffRequired"){
			// check if API limit crossed for number of files and git diff is required
			let needGitDiff = false;
			if (buildTypeOfficial){
				let commitChanges = await app.getCommitChangesSync();
				if (commitChanges.length > 99 ){
					needGitDiff = true;
				}
			} else {
				let mrChanges = await app.getMergeChanges();
				if (mrChanges.changes_count.endsWith('+')){
					needGitDiff = true;
				}
			}
			if (needGitDiff){
				// write empty file to indicate git diff is required
				// ci yml will read this and checkout project
				utils.log("git diff is needed.");
				fs.writeFileSync(gitDiffRequired, "");
			}
		} else if (cmd === "storeAutoFpResult"){
			const cherryResult = process.argv[3];
			app.storeAutoFpResult(cherryResult);
		} else if (cmd === "handleForwardPort"){
			console.log(process.argv);
			await app.handleForwardPort(process.argv[3], process.argv[4]);
		} else if (cmd === "getMergedRef"){
			// run only for friendly case
			if (buildTypeOfficial){
				utils.log("No need to run get updated merged ref for official build");
			} else {
				let commitId = await app.getMergedRef();
				utils.log("updated merged ref: " + commitId);
			}
		} else if (cmd === "createUCForm"){
			app.createUpdateUCForm();
		} else if(cmd === "initBuildExternalSource"){
			await app.initBuildExternalsource();
		} else if(cmd === "downloadFriendlySource"){
			await app.downloadFriendlySource();
		} else if (cmd === "updateNewPipelineInfo") {
			await app.updateNewPipelineInfo();
		} else if (!utils.isUndefinedOrEmpty(env.mergeId)){
			// MR case
			app.logChangesInMerge();
		} else if (!utils.isUndefinedOrEmpty(env.commitId)){
			// branch commit
			app.logChangesInCommit();
		} else {
			console.log("Environment not set.");
			process.exit(1);
		}
	}
};

const command = process.argv[2];

(async () => {
	console.log('Index.js start time:' + new Date());
    await app.run(command);
	console.log('Command completed. Index.js end time:' + new Date());
})()
.catch(e => {
    console.log('Error: ' + e);
	console.log('Exiting node process');
	process.exit(1);
});


// test code
// const base = "https://git.commvault.com/api/v4";
// POST /projects/:id/repository/commits/:sha/revert

// req.post({
// 	url: utils.api("https://git.commvault.com/api/v4/projects/9/repository/commits/d687339f921bad2c42a5a4bf47519d6d3b4b620f/revert").url,
// 	body: "branch=REL_11_0_0_BRANCH",
// 	headers: {
// 		'Private-token': 'EzmLGs7GT1knVRe6GzL3'
// 	}
// 	}).then(project => {
// 	let projectData = JSON.parse(project);
// 	console.log(project);
// }).catch(e => {
// 	utils.log('Failed to load project details' + e, true);
// });


// POST /projects/:id/merge_requests

// req.post({
// 	url: utils.api("https://git.commvault.com/api/v4/projects/26/merge_requests?sudo=8").url,
// 	form: {
// 		id: 26,
// 		title: "test - new GMR",
// 		description: "Merge conflict testing",
// 		target_branch: "REL_11_0_0_BRANCH",
// 		source_branch: "new-source-branch-61585-" + Date.now(),
// 		target_project_id: 9
// 	  },
// 	headers: {
// 		'Private-token': 'MHfasvNsAftUWqzbs6_Z'
// 	}
// 	}).then(project => {
// 	let projectData = JSON.parse(project);
// 	console.log(project);
// }).catch(e => {
// 	utils.log('Failed to load project details' + e, true);
// });


// approve
// POST /projects/:id/merge_requests/:merge_request_iid/approve

// req.post({
// 	url: utils.api("https://git.commvault.com/api/v4/projects/9/merge_requests/120/approve").url,
// 	headers: {
// 		'Private-token': 'EzmLGs7GT1knVRe6GzL3'
// 	}
// 	}).then(project => {
// 	let projectData = JSON.parse(project);
// 	console.log(project);
// }).catch(e => {
// 	utils.log('Failed to load project details' + e, true);
// });

// test fail case

// var opts = {
// 	username: "gbuilder",
// 	password: "builder!12",
// 	url: ""
// };
// var s = JSON.parse('{"buildid":"1100080","AccessToken":"token1","formtype":"GitLabForm","author":"apatidar@commvault.com","projectname":"Block Level Replication","gitmergerequestid":"143","gitprojectid":"9","formid":"61597"}');
// s.gitmiscinfo = '{"failed_o":"true"}';
// // rest info is still present in data but not used by UC
// // utils.logToFile(`${distDir}/formData.json`, JSON.stringify(data));
// console.log("sending data: " + JSON.stringify(s));

// opts.url = utils.api(ucModifyGitlabInfoAPI).url;
// ntlm.put(opts, s, function(err, response) {
// 	if (err || response.body.error || response.statusCode !== 200) {
// 		utils.log('Failed to create update form: ' + err, true);
// 		utils.log('Failed to create update form: ' + JSON.stringify(response), true);
// 		process.exit(1);
// 	}
// 	utils.log("Good to go: " + JSON.stringify(response));
// });


// check for labels on this MR
// req(utils.api(mrDetailsApi)).then(resp => {
// 		console.log(resp);
// }).catch(e => {
// 	utils.log('Labels could not be fetched: ' + e, true);
// 	errCb(e);
// });



// test await
// async function fx1 (){
// 	try {
// 		let data = await req(utils.api("https://git.commvault.com/api/v4/projects/66/merge_requests"));
// 		console.log(data);
//     } catch (e) {
//         console.error(e);
//     } finally {
//         console.log('We do cleanup here');
//     }

// }
// fx1();

// async function fx (){
// 	console.log(await app.getMergeIdForCommitSync());
// }
// fx();

// const ucBase = "https://updatecenter.commvault.com:8001";
// test PUT api/MarkSourceFilesAreCommitted?BuildID={BuildID}&FormID={FormID}&AccessToken={AccessToken}
// var opts = {
// 	username: "gbuilder",
// 	password: "builder!12",
// 	url: ""
// };
// opts.url = utils.api(ucBase + '/updatecenterwebapi/api/MarkSourceFilesAreCommitted?BuildID=1100080&FormID=61567&AccessToken=token1').url;
// ntlm.put(opts, null, function(err, response) {
// 	if (err || response.body.error || response.statusCode !== 200) {
// 		utils.log('Failed to create update form: ' + err, true);
// 		utils.log('Failed to create update form: ' + JSON.stringify(response), true);
// 		process.exit(1);
// 	}
// 	utils.log("Good to go: " + JSON.stringify(response));
// });


// app.createUpdateUCForm();
