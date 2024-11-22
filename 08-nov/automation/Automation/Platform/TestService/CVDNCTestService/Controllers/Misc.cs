using CVDotNetLogger;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Specialized;
using System.Text;

namespace CVDNCTestService.Controllers
{
    [ApiController]
    [Route("Tests/Misc")]
    public class MiscController : ControllerBase
    {

        public readonly ICVDotNetLogger _logger;

        public MiscController(ICVDotNetLogger logger)
        {
            _logger = logger;
        }

        [HttpGet]
        [Route("Ping")]
        public IActionResult Ping()
        {
            return Ok("pong");
        }

        [HttpGet]
        [Route("Logs")]
        public IActionResult Logs([FromQuery] string randGUID)
        {
            _logger.LogError($"This is error log [{randGUID}]");
            _logger.LogWarn($"This is warning log [{randGUID}]");
            _logger.LogInfo($"This is info log [{randGUID}]");
            _logger.LogTrace($"This is trace log [{randGUID}]");
            _logger.LogDiag($"This is diag log [{randGUID}]");
            _logger.LogException(new Exception($"This is exception log [{randGUID}]"));

            return Ok();
        }

        [HttpGet]
        [Route("QueryString")]
        public IActionResult QueryString([FromQuery] string userGuid, [FromQuery] string comment)
        {

            if (userGuid is null || comment is null) 
            {
                throw new Exception("clientId/client Name not provided.");
            }

            databrowseMsg.FileComment fileComment = new databrowseMsg.FileComment()
            {
                comment = comment,
                userGuid = userGuid
            };

            return Ok(fileComment);
        }

        // Works only when Content-Type is application/x-www-form-urlencoded or multipart/form-data;
        [HttpPost]
        [Route("FormData")]
        public IActionResult FormData([FromBody] NameValueCollection data)
        {
            databrowseMsg.FileComment fileComment = new databrowseMsg.FileComment()
            {
                comment = data["comment"],
                userGuid = data["userGuid"]
            };

            return Ok(fileComment);
        }

        [HttpGet]
        [Route("PasswordOut")]
        public IActionResult PasswordOut()
        {
            byte[] password = Encoding.UTF8.GetBytes("dummy-password");

            databrowseMsg.AppUserPassword appUserPassword = new databrowseMsg.AppUserPassword(){ 
                domainName = "example.com",
                password = password
            };

            return Ok(appUserPassword);
        }

        [HttpGet]
        [Route("CustomHeader")]
        public IActionResult CustomHeader([FromQuery] string headerName, [FromQuery] string headerValue) 
        {
            Response.Headers.Add(headerName, headerValue);
            return Ok();
        }

        [HttpGet]
        [Route("Exception")]
        public IActionResult Exception()
        {
            throw new Exception("Forced exception message");
        }

    }
}
