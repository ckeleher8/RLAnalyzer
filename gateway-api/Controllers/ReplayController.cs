using System;
using System.Threading.Tasks;
using GatewayApi.Contracts;
using GatewayApi.Models;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;

namespace GatewayApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class ReplayController : ControllerBase
    {
        private readonly IReplayAnalysisService _analysisService;

        public ReplayController(IReplayAnalysisService analysisService)
        {
            _analysisService = analysisService;
        }

        /// <summary>
        /// Uploads a .replay file for asynchronous analysis.
        /// </summary>
        [HttpPost("upload")]
        [ProducesResponseType(typeof(UploadResponseDto), StatusCodes.Status202Accepted)]
        [ProducesResponseType(StatusCodes.Status400BadRequest)]
        public async Task<IActionResult> UploadReplay(IFormFile file)
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest("No file uploaded or file is empty.");
            }

            if (!file.FileName.EndsWith(".replay", StringComparison.OrdinalIgnoreCase))
            {
                return BadRequest("Uploaded file must have a .replay extension.");
            }

            try
            {
                var response = await _analysisService.InitiateUploadAsync(file);
                return AcceptedAtAction(nameof(GetStatus), new { id = response.Id }, response);
            }
            catch (Exception ex)
            {
                return StatusCode(StatusCodes.Status500InternalServerError, new { error = ex.Message });
            }
        }

        /// <summary>
        /// Polls the processing status of a submitted replay analysis.
        /// </summary>
        [HttpGet("{id:int}/status")]
        [ProducesResponseType(typeof(UploadResponseDto), StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<IActionResult> GetStatus(int id)
        {
            var status = await _analysisService.GetMatchStatusAsync(id);
            if (status == null)
            {
                return NotFound($"Match with ID {id} not found.");
            }
            return Ok(status);
        }

        /// <summary>
        /// Retrieves the full match analysis report by database ID.
        /// </summary>
        [HttpGet("{id:int}")]
        [ProducesResponseType(typeof(MatchResponseDto), StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<IActionResult> GetMatchById(int id)
        {
            var match = await _analysisService.GetMatchByIdAsync(id);
            if (match == null)
            {
                return NotFound($"Match with ID {id} not found.");
            }
            return Ok(match);
        }

        /// <summary>
        /// Retrieves the full match analysis report by UUID match ID.
        /// </summary>
        [HttpGet("by-uuid/{matchId}")]
        [ProducesResponseType(typeof(MatchResponseDto), StatusCodes.Status200OK)]
        [ProducesResponseType(StatusCodes.Status404NotFound)]
        public async Task<IActionResult> GetMatchByMatchId(string matchId)
        {
            var match = await _analysisService.GetMatchByMatchIdAsync(matchId);
            if (match == null)
            {
                return NotFound($"Match with UUID {matchId} not found.");
            }
            return Ok(match);
        }

        /// <summary>
        /// Retrieves recently analyzed matches.
        /// </summary>
        [HttpGet]
        [ProducesResponseType(typeof(List<MatchResponseDto>), StatusCodes.Status200OK)]
        public async Task<IActionResult> GetRecentMatches([FromQuery] int count = 20)
        {
            var matches = await _analysisService.GetRecentMatchesAsync(count);
            return Ok(matches);
        }
    }
}