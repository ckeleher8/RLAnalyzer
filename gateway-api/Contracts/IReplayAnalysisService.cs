using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Http;
using GatewayApi.Models;

namespace GatewayApi.Contracts
{
    public interface IReplayAnalysisService
    {
        Task<UploadResponseDto> InitiateUploadAsync(IFormFile replayFile);
        Task<MatchResponseDto?> GetMatchByIdAsync(int id);
        Task<MatchResponseDto?> GetMatchByMatchIdAsync(string matchId);
        Task<List<MatchResponseDto>> GetRecentMatchesAsync(int count = 20);
        Task<UploadResponseDto?> GetMatchStatusAsync(int id);
    }
}