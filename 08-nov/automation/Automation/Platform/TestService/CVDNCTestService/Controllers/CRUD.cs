using CVDotNetLogger;
using Microsoft.AspNetCore.Mvc;

namespace CVDNCTestService.Controllers
{
    [ApiController]
    [Route("/Tests/CRUD")]
    public class CRUDController : ControllerBase
    {

        public readonly ICVDotNetLogger _logger;
        public TestsStore _store;

        public CRUDController(ICVDotNetLogger logger, TestsStore store)
        {
            _logger = logger;
            _store = store;
        }

        [HttpGet]
        public IActionResult Get()
        {
            return Ok(_store.fileComments);
        }

        [HttpGet]
        [Route("{userGuid}")]
        public IActionResult GetComment(string userGuid)
        {
            foreach (var fileComment in _store.fileComments)
            {
                if (fileComment.userGuid == userGuid)
                {
                    return Ok(fileComment);
                }
            }

            _logger.LogError($"File comment for userGUID [{userGuid}] does not exist");

            CVModelsMsg.GenericResp error = new();
            error.errorMessage = "User GUID not found";
            return BadRequest(error);
        }

        [HttpPost]
        public IActionResult AddComment([FromBody] databrowseMsg.FileComment fileComment)
        {
            CVModelsMsg.GenericResp error = new();

            if (fileComment.userGuid == null) {
                error.errorMessage = "User GUID is not set in the request";
                return BadRequest(error);
            }

            foreach (var comment in _store.fileComments)
            {
                if (comment.userGuid == fileComment.userGuid)
                {
                    _logger.LogError($"User comment [{fileComment.userGuid}] already exists");
                    return Conflict(fileComment);
                }
            }

            _store.fileComments.Add(fileComment);

            _logger.LogInfo($"User comment [{fileComment.userGuid}] added successfully");

            return Ok(fileComment);

        }

        [HttpPut]
        [Route("{userGuid}")]
        public IActionResult ModifyComment(string userGuid, [FromBody] databrowseMsg.FileComment fileComment)
        {
            CVModelsMsg.GenericResp error = new();
            _logger.LogError($"Modify request received [{userGuid}] [{fileComment}]");

            int commentIndex = _store.fileComments.FindIndex(comment => comment.userGuid == userGuid);

            if (commentIndex == -1)
            {
                error.errorMessage = $"File comment [{userGuid}] not found";
                return BadRequest(error);
            }

            if (fileComment.userGuid == null)
            {
                fileComment.userGuid = userGuid;
            }

            _store.fileComments[commentIndex] = fileComment;
            return Ok(fileComment);
        }

        [HttpDelete]
        [Route("{userGuid}")]
        public IActionResult DeleteComment(string userGuid)
        {
            CVModelsMsg.GenericResp error = new();
            int commentIndex = _store.fileComments.FindIndex(comment => comment.userGuid == userGuid);

            if (commentIndex == -1)
            {
                error.errorMessage = $"File comment [{userGuid}] not found to delete";
                _logger.LogError(error.errorMessage);
                return BadRequest(error);
            }

            _logger.LogInfo($"Found File comment at index [{commentIndex}]");

            _store.fileComments.RemoveAt(commentIndex);

            _logger.LogInfo($"File comment [{userGuid}] deleted successfully");

            return Ok("File comment deleted successfully");
        }

    }
}
