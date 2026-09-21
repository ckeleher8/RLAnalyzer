using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text.Json;
using System.Threading.Tasks;
using GatewayApi.Contracts;
using GatewayApi.Models;
using Microsoft.Extensions.Logging;

namespace GatewayApi.Infrastructure
{
    public class PythonMlHttpClient : IMlModelClient
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<PythonMlHttpClient> _logger;
        private readonly JsonSerializerOptions _jsonOptions;

        public PythonMlHttpClient(HttpClient httpClient, ILogger<PythonMlHttpClient> logger)
        {
            _httpClient = httpClient;
            _logger = logger;
            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            };
        }

        public async Task<PythonAnalysisReport> AnalyzeReplayAsync(Stream fileStream, string fileName)
        {
            _logger.LogInformation("Submitting replay file {FileName} to Python ML engine...", fileName);

            using var content = new MultipartFormDataContent();
            var streamContent = new StreamContent(fileStream);
            streamContent.Headers.ContentType = new MediaTypeHeaderValue("application/octet-stream");
            content.Add(streamContent, "file", fileName);

            var response = await _httpClient.PostAsync("api/analyze-replay", content);
            var responseString = await response.Content.ReadAsStringAsync();

            if (!response.IsSuccessStatusCode)
            {
                _logger.LogError("Failed to submit replay to Python ML engine. Status: {StatusCode}, Body: {Body}", 
                    response.StatusCode, responseString);
                throw new HttpRequestException($"ML Engine submission failed: {response.StatusCode} - {responseString}");
            }

            var initialResponse = JsonSerializer.Deserialize<PythonJobStatusResponse>(responseString, _jsonOptions);
            if (initialResponse == null || string.IsNullOrEmpty(initialResponse.Job_Id))
            {
                throw new InvalidOperationException("Invalid response payload from Python ML service.");
            }

            // If the response already has completed report (synchronous fallback)
            if (initialResponse.Status == "completed" && initialResponse.Report != null)
            {
                return initialResponse.Report;
            }

            var jobId = initialResponse.Job_Id;
            _logger.LogInformation("Replay job accepted by ML engine with Job ID: {JobId}. Starting polling...", jobId);

            // Poll for job completion
            var maxAttempts = 120; // 60 seconds (500ms intervals)
            for (var attempt = 0; attempt < maxAttempts; attempt++)
            {
                await Task.Delay(500);

                var statusResponse = await _httpClient.GetAsync($"api/jobs/{jobId}");
                if (!statusResponse.IsSuccessStatusCode)
                {
                    _logger.LogWarning("Job status check returned {StatusCode} on attempt {Attempt}", 
                        statusResponse.StatusCode, attempt);
                    continue;
                }

                var statusBody = await statusResponse.Content.ReadAsStringAsync();
                var jobStatus = JsonSerializer.Deserialize<PythonJobStatusResponse>(statusBody, _jsonOptions);

                if (jobStatus == null) continue;

                if (jobStatus.Status == "completed" && jobStatus.Report != null)
                {
                    _logger.LogInformation("Job {JobId} completed successfully.", jobId);
                    return jobStatus.Report;
                }

                if (jobStatus.Status == "failed")
                {
                    _logger.LogError("Job {JobId} failed: {Message}", jobId, jobStatus.Message);
                    throw new InvalidOperationException($"Python ML Engine failed: {jobStatus.Message}");
                }
            }

            throw new TimeoutException($"Timed out waiting for Python ML engine job {jobId} to complete.");
        }
    }
}
