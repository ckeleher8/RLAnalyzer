using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using GatewayApi.Contracts;
using GatewayApi.Infrastructure;
using GatewayApi.Models;
using GatewayApi.Models.Entities;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GatewayApi.Services
{
    public class ReplayAnalysisService : IReplayAnalysisService
    {
        private readonly AppDbContext _dbContext;
        private readonly IMlModelClient _mlClient;
        private readonly IServiceScopeFactory _scopeFactory;
        private readonly ILogger<ReplayAnalysisService> _logger;

        public ReplayAnalysisService(
            AppDbContext dbContext,
            IMlModelClient mlClient,
            IServiceScopeFactory scopeFactory,
            ILogger<ReplayAnalysisService> logger)
        {
            _dbContext = dbContext;
            _mlClient = mlClient;
            _scopeFactory = scopeFactory;
            _logger = logger;
        }

        public async Task<UploadResponseDto> InitiateUploadAsync(IFormFile replayFile)
        {
            if (replayFile == null || replayFile.Length == 0)
            {
                throw new ArgumentException("Replay file cannot be empty.");
            }

            var matchGuid = Guid.NewGuid().ToString();
            var matchEntity = new MatchEntity
            {
                MatchId = matchGuid,
                FileName = replayFile.FileName,
                UploadedAt = DateTime.UtcNow,
                Status = "Processing"
            };

            _dbContext.Matches.Add(matchEntity);
            await _dbContext.SaveChangesAsync();

            // Read file bytes into memory buffer for background task
            byte[] fileBytes;
            using (var memoryStream = new MemoryStream())
            {
                await replayFile.CopyToAsync(memoryStream);
                fileBytes = memoryStream.ToArray();
            }

            // Run processing in background so HTTP response is instant
            _ = Task.Run(async () =>
            {
                await ProcessReplayBackgroundAsync(matchEntity.Id, fileBytes, replayFile.FileName);
            });

            return new UploadResponseDto
            {
                Id = matchEntity.Id,
                MatchId = matchEntity.MatchId,
                Status = "Processing",
                Message = "Replay uploaded successfully. Analysis in progress."
            };
        }

        private async Task ProcessReplayBackgroundAsync(int matchDbId, byte[] fileBytes, string fileName)
        {
            using var scope = _scopeFactory.CreateScope();
            var scopedDb = scope.ServiceProvider.GetRequiredService<AppDbContext>();
            var scopedMlClient = scope.ServiceProvider.GetRequiredService<IMlModelClient>();
            var logger = scope.ServiceProvider.GetRequiredService<ILogger<ReplayAnalysisService>>();

            var match = await scopedDb.Matches.FindAsync(matchDbId);
            if (match == null) return;

            try
            {
                logger.LogInformation("Processing replay #{MatchId} ({FileName})", matchDbId, fileName);

                using var stream = new MemoryStream(fileBytes);
                var report = await scopedMlClient.AnalyzeReplayAsync(stream, fileName);

                match.Status = "Completed";
                match.RawReportJson = JsonSerializer.Serialize(report);

                if (report.Metadata != null)
                {
                    match.MapName = report.Metadata.Map_Name;
                    match.DurationSeconds = report.Metadata.Duration_Seconds;
                    match.BlueScore = report.Metadata.Blue_Score;
                    match.OrangeScore = report.Metadata.Orange_Score;
                    match.WinningTeam = report.Metadata.Winning_Team;
                }

                if (report.Players != null)
                {
                    foreach (var p in report.Players)
                    {
                        match.PlayerStats.Add(new PlayerStatEntity
                        {
                            MatchId = match.Id,
                            PlayerName = p.Name,
                            Team = p.Team,
                            Goals = p.Goals,
                            Saves = p.Saves,
                            Shots = p.Shots,
                            TotalActionValue = p.Total_Action_Value,
                            AvgActionValue = p.Avg_Action_Value,
                            TotalWastedBoost = p.Total_Wasted_Boost,
                            PadPickupCount = p.Pad_Pickups
                        });
                    }
                }

                if (report.ML_Action_Values != null)
                {
                    foreach (var t in report.ML_Action_Values)
                    {
                        match.Touches.Add(new TouchEntity
                        {
                            MatchId = match.Id,
                            Frame = t.Frame,
                            PlayerName = t.Player,
                            Team = t.Team,
                            VBefore = t.V_Before,
                            VAfter = t.V_After,
                            ActionValue = t.Action_Value,
                            IsGoal = t.Is_Goal,
                            IsSave = t.Is_Save
                        });
                    }
                }

                if (report.Heuristics != null)
                {
                    foreach (var kvp in report.Heuristics)
                    {
                        var summaryJson = JsonSerializer.Serialize(kvp.Value);
                        match.Heuristics.Add(new HeuristicSummaryEntity
                        {
                            MatchId = match.Id,
                            PlayerName = kvp.Key,
                            MetricType = "Heuristic",
                            SummaryJson = summaryJson,
                            WarningCount = 0
                        });
                    }
                }

                await scopedDb.SaveChangesAsync();
                logger.LogInformation("Successfully analyzed and persisted replay #{MatchId}", matchDbId);
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Failed to analyze replay #{MatchId}", matchDbId);
                match.Status = "Failed";
                match.ErrorMessage = ex.Message;
                await scopedDb.SaveChangesAsync();
            }
        }

        public async Task<MatchResponseDto?> GetMatchByIdAsync(int id)
        {
            var match = await _dbContext.Matches
                .Include(m => m.PlayerStats)
                .Include(m => m.Touches)
                .Include(m => m.Heuristics)
                .FirstOrDefaultAsync(m => m.Id == id);

            return match == null ? null : MapToResponseDto(match);
        }

        public async Task<MatchResponseDto?> GetMatchByMatchIdAsync(string matchId)
        {
            var match = await _dbContext.Matches
                .Include(m => m.PlayerStats)
                .Include(m => m.Touches)
                .Include(m => m.Heuristics)
                .FirstOrDefaultAsync(m => m.MatchId == matchId);

            return match == null ? null : MapToResponseDto(match);
        }

        public async Task<List<MatchResponseDto>> GetRecentMatchesAsync(int count = 20)
        {
            var matches = await _dbContext.Matches
                .Include(m => m.PlayerStats)
                .OrderByDescending(m => m.UploadedAt)
                .Take(count)
                .ToListAsync();

            return matches.Select(MapToResponseDto).ToList();
        }

        public async Task<UploadResponseDto?> GetMatchStatusAsync(int id)
        {
            var match = await _dbContext.Matches
                .Select(m => new { m.Id, m.MatchId, m.Status, m.ErrorMessage })
                .FirstOrDefaultAsync(m => m.Id == id);

            if (match == null) return null;

            return new UploadResponseDto
            {
                Id = match.Id,
                MatchId = match.MatchId,
                Status = match.Status,
                Message = match.ErrorMessage ?? $"Match status: {match.Status}"
            };
        }

        private static MatchResponseDto MapToResponseDto(MatchEntity entity)
        {
            Dictionary<string, object>? heuristicsDict = null;
            if (!string.IsNullOrEmpty(entity.RawReportJson))
            {
                try
                {
                    var parsed = JsonSerializer.Deserialize<PythonAnalysisReport>(entity.RawReportJson);
                    heuristicsDict = parsed?.Heuristics;
                }
                catch { }
            }

            return new MatchResponseDto
            {
                Id = entity.Id,
                MatchId = entity.MatchId,
                FileName = entity.FileName,
                UploadedAt = entity.UploadedAt,
                Status = entity.Status,
                ErrorMessage = entity.ErrorMessage,
                MapName = entity.MapName,
                DurationSeconds = entity.DurationSeconds,
                BlueScore = entity.BlueScore,
                OrangeScore = entity.OrangeScore,
                WinningTeam = entity.WinningTeam,
                Players = entity.PlayerStats.Select(p => new PlayerSummaryDto
                {
                    Name = p.PlayerName,
                    Team = p.Team,
                    Goals = p.Goals,
                    Saves = p.Saves,
                    Shots = p.Shots,
                    Total_Action_Value = Math.Round(p.TotalActionValue, 3),
                    Avg_Action_Value = Math.Round(p.AvgActionValue, 3),
                    Total_Wasted_Boost = Math.Round(p.TotalWastedBoost, 1),
                    Pad_Pickups = p.PadPickupCount
                }).ToList(),
                Touches = entity.Touches.Select(t => new ActionValueTouchDto
                {
                    Frame = t.Frame,
                    Player = t.PlayerName,
                    Team = t.Team,
                    V_Before = Math.Round(t.VBefore, 3),
                    V_After = Math.Round(t.VAfter, 3),
                    Action_Value = Math.Round(t.ActionValue, 3),
                    Is_Goal = t.IsGoal,
                    Is_Save = t.IsSave
                }).ToList(),
                Heuristics = heuristicsDict
            };
        }
    }
}